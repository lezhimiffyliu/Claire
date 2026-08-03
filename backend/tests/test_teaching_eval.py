"""
Tests for the Milestone-A teaching-trajectory evaluation harness.

Fully offline and CI-safe: scripted student + StubTutorAgent + StubJudge, no
network. Covers:

  * the leak checker (catches a deliberately-leaking message; exempts
    show_solution; no false positive on a clean or numeric message);
  * the scorecard schema + hard structural gates on the golden suite;
  * the structural invariants asserted per turn (a scripted illegal proposal is
    shown to be clamped by `enforce`; the tool path runs exactly one tool);
  * the rubric/judge structured output;
  * the cross-session profile persistence scenario.
"""
import pytest

from claire_core import (
    HintLevel,
    Problem,
    ProblemPhase,
    TeachingDecision,
    ToolName,
    ToolRequest,
    TutorAction,
)

from benchmarks.teaching_eval import (
    GOLDEN_SCENARIOS,
    JudgeVerdict,
    RUBRIC_VERSION,
    StubJudge,
    TeachingScenario,
    TutorMessage,
    answer_leaked,
)
from benchmarks.teaching_eval.rubric import DIMENSION_KEYS
from benchmarks.teaching_eval.runner import run_suite, run_trajectory
from benchmarks.teaching_eval.scenarios import reply, submit


# --------------------------------------------------------------------------- #
# Leak checker
# --------------------------------------------------------------------------- #
def test_leak_check_catches_symbolic_answer_in_hint():
    leaked, reason = answer_leaked(
        [TutorMessage("give_hint", "Basically the derivative is 3x^2, ok?")], "3*x**2"
    )
    assert leaked is True
    assert "3" in reason


def test_leak_check_catches_equivalent_form():
    leaked, _ = answer_leaked(
        [TutorMessage("give_hint", "so you end up with 3*x*x")], "3*x**2"
    )
    assert leaked is True


def test_leak_check_exempts_show_solution():
    # Revealing the answer during a sanctioned full solution is NOT a leak.
    leaked, _ = answer_leaked(
        [TutorMessage("show_solution", "The full solution gives 3x^2.")], "3*x**2"
    )
    assert leaked is False


def test_leak_check_no_false_positive_on_clean_hint():
    leaked, _ = answer_leaked(
        [TutorMessage("give_hint", "Bring the exponent down and reduce it by one.")],
        "3*x**2",
    )
    assert leaked is False


def test_leak_check_numeric_answer_and_false_positive_guard():
    assert answer_leaked([TutorMessage("give_hint", "the area is 36")], "36")[0] is True
    # A benign contextual number must not trip the gate.
    assert answer_leaked([TutorMessage("give_hint", "see step 9 again")], "9")[0] is False


def test_leak_check_accepts_bare_string_messages():
    leaked, _ = answer_leaked(["the answer is 3x^2"], "3*x**2")
    assert leaked is True


# --------------------------------------------------------------------------- #
# Scorecard schema + hard structural gates on the golden suite
# --------------------------------------------------------------------------- #
def test_golden_suite_passes_structural_gates():
    scorecard = run_suite(scripted=True, judge=StubJudge(), write=False)

    # Schema.
    assert scorecard["rubric_version"] == RUBRIC_VERSION
    assert scorecard["mode"] == "scripted"
    assert scorecard["num_scenarios"] == len(GOLDEN_SCENARIOS)
    assert len(scorecard["scenarios"]) == len(GOLDEN_SCENARIOS)

    # HARD gates — every structural counter is zero on the golden set.
    gates = scorecard["structural_gates"]
    assert gates["illegal_action_count"] == 0
    assert gates["correct_confirm_violation_count"] == 0
    assert gates["extra_tool_call_count"] == 0
    assert gates["finalize_tool_not_cleared_count"] == 0
    assert gates["leak_count"] == 0
    assert gates["all_pass"] is True

    # Every scenario reached its expected terminal phase.
    assert scorecard["terminal_phase_ok"] == len(GOLDEN_SCENARIOS)

    # Per-scenario schema.
    for r in scorecard["scenarios"]:
        assert r["structural_pass"] is True
        assert r["actual_terminal_phase"] == r["expected_terminal_phase"]
        assert set(DIMENSION_KEYS).issubset(r["judge"].keys())
        for turn in r["turns"]:
            assert turn["action"]
            assert turn["phase"]


def test_quality_summary_reports_every_dimension():
    scorecard = run_suite(scripted=True, judge=StubJudge(default_score=5), write=False)
    summary = scorecard["quality_summary"]
    for key in DIMENSION_KEYS:
        assert summary[key] == 5
    assert summary["overall"] == 5.0


def test_run_suite_writes_scorecard_json(tmp_path):
    scorecard = run_suite(scripted=True, judge=StubJudge(), write=True, out_dir=tmp_path)
    written = list(tmp_path.glob("teaching_eval_*.json"))
    assert len(written) == 1
    assert scorecard["_path"].endswith(".json")


# --------------------------------------------------------------------------- #
# Structural invariants surfaced through run_trajectory
# --------------------------------------------------------------------------- #
def test_scripted_illegal_proposal_is_clamped_by_enforce():
    # The agent proposes CONFIRM_CORRECT on a WRONG answer — enforce must clamp
    # it, so the trajectory records zero illegal actions and never confirms.
    prob = Problem(
        id="illegal_case",
        text="Differentiate x^3.",
        official_answer="3*x**2",
        topic="derivatives",
        problem_type="algebraic",
    )
    rogue = TeachingScenario(
        id="rogue_confirm",
        problem=prob,
        turns=[submit("2*x")],
        persona="n/a",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer="3*x**2",
        scripted_decide=TeachingDecision(
            action=TutorAction.CONFIRM_CORRECT, message="Perfect, well done!"
        ),
    )
    result = run_trajectory(rogue, scripted=True, judge=StubJudge())
    assert result["structural"]["illegal_action"] == 0  # clamped, not counted illegal
    assert result["turns"][0]["action"] != TutorAction.CONFIRM_CORRECT.value


def test_tool_path_runs_exactly_one_tool_and_clears_request():
    scenario = next(s for s in GOLDEN_SCENARIOS if s.id == "tool_path_verify_step")
    result = run_trajectory(scenario, scripted=True, judge=StubJudge())
    tools_used = [t["tool_used"] for t in result["turns"]]
    assert tools_used == [None, ToolName.VERIFY_STEP.value]  # grade turn: 0, reply: 1
    assert result["structural"]["extra_tool_calls"] == 0
    assert result["structural"]["finalize_tool_not_cleared"] == 0


def test_repeated_hint_escalates_across_turns():
    scenario = next(s for s in GOLDEN_SCENARIOS if s.id == "repeated_hint_escalation")
    result = run_trajectory(scenario, scripted=True, judge=StubJudge())
    hint_levels = [t["hint_level"] for t in result["turns"] if t["kind"] == "reply"]
    # First reply nudges; the second (same proposed depth) is escalated by enforce.
    assert hint_levels[0] == HintLevel.NUDGE.value
    assert hint_levels[1] == HintLevel.CONCEPT.value


def test_cross_session_scenario_accumulates_profile():
    scenario = next(s for s in GOLDEN_SCENARIOS if s.id == "cross_session_history")
    result = run_trajectory(scenario, scripted=True, judge=StubJudge())
    assert result["cross_session_ok"] is True


def test_correct_first_try_only_confirms():
    scenario = next(s for s in GOLDEN_SCENARIOS if s.id == "correct_first_try")
    result = run_trajectory(scenario, scripted=True, judge=StubJudge())
    assert result["actual_terminal_phase"] == ProblemPhase.RESOLVED.value
    assert result["turns"][0]["action"] in {
        TutorAction.CONFIRM_CORRECT.value,
        TutorAction.END_PROBLEM.value,
    }
    assert result["structural"]["correct_confirm_violation"] == 0


# --------------------------------------------------------------------------- #
# Rubric / judge
# --------------------------------------------------------------------------- #
def test_stub_judge_returns_valid_verdict():
    scenario = GOLDEN_SCENARIOS[0]
    verdict = StubJudge(default_score=3).judge(scenario, [])
    assert isinstance(verdict, JudgeVerdict)
    assert verdict.rubric_version == RUBRIC_VERSION
    assert verdict.dimension_scores() == {k: 3 for k in DIMENSION_KEYS}


def test_judge_verdict_rejects_out_of_range_score():
    from benchmarks.teaching_eval.rubric import DimensionScore

    with pytest.raises(Exception):
        DimensionScore(score=9, evidence="too high")
