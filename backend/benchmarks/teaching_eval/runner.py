"""
benchmarks.teaching_eval.runner — drive the real loop, score, and emit a scorecard.

`run_trajectory` runs one scenario end-to-end through the CANONICAL spine
(`run_tutor_turn` for SUBMIT turns, `run_teaching_turn` for REPLY turns) with
in-memory stores, so `enforce` runs for real. Per turn it asserts the structural
spine invariants (these are the HARD gates), runs the symbolic leak check, and
finally hands the transcript to the judge (model-quality, reported not gated).

`run_suite` aggregates into a scorecard JSON under ``benchmarks/results/``.

CLI::

    python -m benchmarks.teaching_eval.runner --scripted-only        # fully offline
    python -m benchmarks.teaching_eval.runner --judge-model <id>     # real tutor + judge
    python -m benchmarks.teaching_eval.runner --limit 3 --llm-student

Exit code is non-zero when a hard structural gate fails, so this doubles as a CI
smoke check.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

import claire_core.tools as _tools_mod
from claire_core import (
    Grade,
    GradeStatus,
    InMemoryAttemptStore,
    InMemoryProfileStore,
    InMemoryTeachingStateStore,
    StudentAttempt,
    StubTutorAgent,
    TutorAction,
    TutorAgent,
    allowed_actions,
    run_teaching_turn,
    run_tutor_turn,
)

from .judge import JUDGE_DEFAULT_MODEL, JudgeProtocol, LLMJudge, StubJudge, judge_trajectory
from .leak_check import TutorMessage, answer_leaked
from .rubric import DIMENSION_KEYS, RUBRIC_VERSION
from .scenarios import GOLDEN_SCENARIOS, TeachingScenario, TurnKind
from .simulated_student import SimulatedStudent

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parents[2] / "benchmarks" / "results"

_TERMINAL_CORRECT_ACTIONS = {TutorAction.CONFIRM_CORRECT, TutorAction.END_PROBLEM}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class _ToolCounter:
    """Counts `claire_core.tools.run_tool` executions inside a `with` block.

    `run_teaching_turn` imports `run_tool` lazily from the module, so patching
    the module attribute is enough to observe every dispatch (grading turns never
    import it, so their count stays 0)."""

    def __enter__(self) -> "_ToolCounter":
        self.count = 0
        self._real = _tools_mod.run_tool

        def wrapper(req, problem, turn):
            self.count += 1
            return self._real(req, problem, turn)

        _tools_mod.run_tool = wrapper
        return self

    def __exit__(self, *exc) -> bool:
        _tools_mod.run_tool = self._real
        return False


def _carried_grade(status: GradeStatus) -> Grade:
    """Reconstruct the background verdict a teaching turn carries (mirrors
    loop._carried_grade) so we can compute the legal action set for the check."""
    return Grade(
        is_correct=status == GradeStatus.CORRECT,
        is_uncertain=status == GradeStatus.UNVERIFIABLE,
        verifier_type="carried",
        confidence=1.0,
        reason="carried",
    )


def build_agent(scenario: TeachingScenario, *, scripted: bool, model_name: Optional[str] = None):
    """Scripted → deterministic StubTutorAgent; otherwise the real TutorAgent."""
    if scripted:
        return StubTutorAgent(
            decision=scenario.scripted_decide,
            propose_returns=scenario.scripted_propose,
        )
    if model_name:
        return TutorAgent(model_name=model_name)
    return TutorAgent()


def _empty_structural() -> Dict[str, int]:
    return {
        "illegal_action": 0,
        "correct_confirm_violation": 0,
        "extra_tool_calls": 0,
        "finalize_tool_not_cleared": 0,
    }


# --------------------------------------------------------------------------- #
# Single trajectory
# --------------------------------------------------------------------------- #
def run_trajectory(
    scenario: TeachingScenario,
    *,
    scripted: bool,
    judge: JudgeProtocol,
    tutor_model: Optional[str] = None,
    student_model=None,
) -> dict:
    profile_store = InMemoryProfileStore()
    attempt_store = InMemoryAttemptStore()
    state_store = InMemoryTeachingStateStore()
    agent = build_agent(scenario, scripted=scripted, model_name=tutor_model)
    student = SimulatedStudent(scenario, model=student_model)
    user_id = f"student::{scenario.id}"

    transcript: List[dict] = []
    tutor_messages: List[TutorMessage] = []
    turn_records: List[dict] = []
    structural = _empty_structural()
    last_grade_status: Optional[GradeStatus] = None
    submit_count = 0
    final_phase = None

    for idx, turn in enumerate(student.turns):
        text = student.message_for(turn, transcript)
        transcript.append({"role": "student", "kind": turn.kind.value, "text": text})

        if turn.kind == TurnKind.SUBMIT:
            # Cross-session: a returning student starts a FRESH session (new
            # teaching-state store) but keeps the SAME long-term profile store.
            if scenario.cross_session and submit_count >= 1:
                state_store = InMemoryTeachingStateStore()
            submit_count += 1

            attempt = StudentAttempt(
                problem_id=scenario.problem.id, answer=text, source="practice"
            )
            with _ToolCounter() as tc:
                res = run_tutor_turn(
                    problem=scenario.problem,
                    attempt=attempt,
                    user_id=user_id,
                    workspace_id="teaching_eval",
                    agent=agent,
                    attempt_store=attempt_store,
                    profile_store=profile_store,
                    teaching_state_store=state_store,
                )
            grade = res.grade
            last_grade_status = grade.status
            action = res.decision.action

            # Invariant: enforced action is legal for the grade.
            if action not in allowed_actions(grade, None):
                structural["illegal_action"] += 1
            # Invariant: CORRECT ⇒ only confirm/end.
            if grade.status == GradeStatus.CORRECT and action not in _TERMINAL_CORRECT_ACTIONS:
                structural["correct_confirm_violation"] += 1
            # Invariant: a grading turn runs ZERO tools.
            if tc.count > 0:
                structural["extra_tool_calls"] += tc.count

            hint_level = res.decision.hint_level.value
            tool_used = None
            message = res.decision.message
            final_phase = res.phase

        else:  # REPLY → teaching turn
            with _ToolCounter() as tc:
                res = run_teaching_turn(
                    problem=scenario.problem,
                    student_message=text,
                    user_id=user_id,
                    agent=agent,
                    profile_store=profile_store,
                    teaching_state_store=state_store,
                )
            carried = _carried_grade(last_grade_status or GradeStatus.INCORRECT)
            action = res.decision.action

            # Invariant: enforced action is legal for the carried grade.
            if action not in allowed_actions(carried, None):
                structural["illegal_action"] += 1
            # Invariant: at most one tool per teaching turn.
            if tc.count > 1:
                structural["extra_tool_calls"] += tc.count - 1
            # Invariant: finalized decision carries no tool request.
            if res.decision.tool_request is not None:
                structural["finalize_tool_not_cleared"] += 1

            hint_level = res.hint_level.value
            tool_used = res.tool_used.value if res.tool_used else None
            message = res.decision.message
            final_phase = res.phase

        transcript.append({"role": "tutor", "action": action.value, "text": message})
        tutor_messages.append(TutorMessage(action.value, message))
        turn_records.append(
            {
                "index": idx,
                "kind": turn.kind.value,
                "student": text,
                "action": action.value,
                "hint_level": hint_level,
                "phase": final_phase.value if final_phase else None,
                "tool_used": tool_used,
                "message": message,
            }
        )

    leaked, leak_reason = answer_leaked(tutor_messages, scenario.official_answer)
    terminal_ok = final_phase is not None and final_phase.value == scenario.expected_terminal_phase.value

    cross_session_ok = None
    if scenario.cross_session:
        prof = profile_store.load(user_id, scenario.problem.course)
        cross_session_ok = (prof.total_correct + prof.total_incorrect) >= submit_count

    verdict = judge_trajectory(scenario, transcript, judge)

    structural_pass = (
        structural["illegal_action"] == 0
        and structural["correct_confirm_violation"] == 0
        and structural["extra_tool_calls"] == 0
        and structural["finalize_tool_not_cleared"] == 0
        and not leaked
    )

    return {
        "id": scenario.id,
        "persona": scenario.persona,
        "description": scenario.description,
        "num_turns": len(turn_records),
        "expected_terminal_phase": scenario.expected_terminal_phase.value,
        "actual_terminal_phase": final_phase.value if final_phase else None,
        "terminal_phase_ok": terminal_ok,
        "cross_session_ok": cross_session_ok,
        "leak": leaked,
        "leak_reason": leak_reason,
        "structural": structural,
        "structural_pass": structural_pass,
        "turns": turn_records,
        "judge": verdict.model_dump(),
    }


# --------------------------------------------------------------------------- #
# Suite
# --------------------------------------------------------------------------- #
def _quality_summary(results: List[dict]) -> dict:
    if not results:
        return {}
    summary: Dict[str, float] = {}
    for key in DIMENSION_KEYS:
        scores = [r["judge"][key]["score"] for r in results]
        summary[key] = round(mean(scores), 3)
    summary["overall"] = round(mean(r["judge"]["overall"] for r in results), 3)
    return summary


def run_suite(
    scenarios: Optional[List[TeachingScenario]] = None,
    *,
    scripted: bool = True,
    judge: Optional[JudgeProtocol] = None,
    tutor_model: Optional[str] = None,
    student_model=None,
    write: bool = True,
    out_dir: Optional[Path] = None,
) -> dict:
    """Run the whole suite and return (and optionally persist) a scorecard dict."""
    scenarios = scenarios if scenarios is not None else GOLDEN_SCENARIOS
    if judge is None:
        judge = StubJudge() if scripted else LLMJudge()

    results = [
        run_trajectory(
            s,
            scripted=scripted,
            judge=judge,
            tutor_model=tutor_model,
            student_model=student_model,
        )
        for s in scenarios
    ]

    total_turns = sum(r["num_turns"] for r in results)
    illegal = sum(r["structural"]["illegal_action"] for r in results)
    confirm_violation = sum(r["structural"]["correct_confirm_violation"] for r in results)
    extra_tools = sum(r["structural"]["extra_tool_calls"] for r in results)
    not_cleared = sum(r["structural"]["finalize_tool_not_cleared"] for r in results)
    leaks = sum(1 for r in results if r["leak"])
    n = len(results)

    gates = {
        "illegal_action_count": illegal,
        "illegal_action_rate": round(illegal / total_turns, 4) if total_turns else 0.0,
        "correct_confirm_violation_count": confirm_violation,
        "extra_tool_call_count": extra_tools,
        "extra_tool_call_rate": round(extra_tools / total_turns, 4) if total_turns else 0.0,
        "finalize_tool_not_cleared_count": not_cleared,
        "leak_count": leaks,
        "leak_rate": round(leaks / n, 4) if n else 0.0,
    }
    # Hard gates: every structural counter must be zero.
    gates["all_pass"] = (
        illegal == 0
        and confirm_violation == 0
        and extra_tools == 0
        and not_cleared == 0
        and leaks == 0
    )

    terminal_ok = sum(1 for r in results if r["terminal_phase_ok"])
    scorecard = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rubric_version": RUBRIC_VERSION,
        "mode": "scripted" if scripted else "live",
        "tutor": "StubTutorAgent" if scripted else (tutor_model or "TutorAgent:default"),
        "judge": type(judge).__name__ + (
            "" if scripted else f":{getattr(judge, 'model_name', JUDGE_DEFAULT_MODEL)}"
        ),
        "num_scenarios": n,
        "total_turns": total_turns,
        "terminal_phase_ok": terminal_ok,
        "structural_gates": gates,
        "quality_summary": _quality_summary(results),
        "scenarios": results,
    }

    if write:
        target_dir = out_dir or RESULTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = target_dir / f"teaching_eval_{stamp}.json"
        path.write_text(json.dumps(scorecard, indent=2))
        scorecard["_path"] = str(path)
        logger.info("wrote scorecard → %s", path)

    return scorecard


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print_summary(scorecard: dict) -> None:
    g = scorecard["structural_gates"]
    print("\n=== teaching_eval scorecard ===")
    print(f"mode            : {scorecard['mode']}")
    print(f"tutor / judge   : {scorecard['tutor']} / {scorecard['judge']}")
    print(f"scenarios       : {scorecard['num_scenarios']} ({scorecard['total_turns']} turns)")
    print(f"terminal phase  : {scorecard['terminal_phase_ok']}/{scorecard['num_scenarios']} matched expected")
    print("--- HARD structural gates (must be 0) ---")
    print(f"  illegal actions      : {g['illegal_action_count']}")
    print(f"  correct-confirm viol.: {g['correct_confirm_violation_count']}")
    print(f"  extra tool calls     : {g['extra_tool_call_count']}")
    print(f"  finalize not cleared : {g['finalize_tool_not_cleared_count']}")
    print(f"  pre-solution leaks   : {g['leak_count']}")
    print(f"  GATES PASS           : {g['all_pass']}")
    print("--- model-quality (reported, NOT gated pre-baseline) ---")
    for key, val in scorecard["quality_summary"].items():
        print(f"  {key:28s}: {val}")
    if scorecard.get("_path"):
        print(f"\nscorecard written to: {scorecard['_path']}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Teaching-trajectory evaluation harness (Milestone A).")
    parser.add_argument("--limit", type=int, default=None, help="run only the first N scenarios")
    parser.add_argument("--scripted-only", action="store_true",
                        help="fully offline: StubTutorAgent + StubJudge + scripted student")
    parser.add_argument("--llm-student", action="store_true",
                        help="rewrite REPLY messages with an LLM persona (live runs only)")
    parser.add_argument("--judge-model", default=None,
                        help=f"judge model id for live runs (default {JUDGE_DEFAULT_MODEL})")
    parser.add_argument("--tutor-model", default=None, help="tutor model id for live runs")
    parser.add_argument("--no-write", action="store_true", help="do not write the scorecard JSON")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    scenarios = list(GOLDEN_SCENARIOS)
    if args.limit is not None:
        scenarios = scenarios[: args.limit]

    scripted = args.scripted_only
    judge: JudgeProtocol
    student_model = None
    if scripted:
        judge = StubJudge()
    else:
        judge = LLMJudge(model_name=args.judge_model or JUDGE_DEFAULT_MODEL)
        if args.llm_student:
            from langchain_anthropic import ChatAnthropic
            from .simulated_student import DEFAULT_STUDENT_MODEL

            student_model = ChatAnthropic(
                model=DEFAULT_STUDENT_MODEL, temperature=0.7, max_tokens=256
            )

    scorecard = run_suite(
        scenarios,
        scripted=scripted,
        judge=judge,
        tutor_model=args.tutor_model,
        student_model=student_model,
        write=not args.no_write,
    )
    _print_summary(scorecard)
    return 0 if scorecard["structural_gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
