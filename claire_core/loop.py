"""
claire_core.loop — the closed adaptive loop.

A single call runs the full cycle and persists the outcome, so teaching advances
across attempts and mastery feeds the next recommendation:

    attempt
      -> verify           (verifier.py = ground truth)
      -> load state        (per-problem teaching memory)
      -> load profile      (long-term mastery, summarized for the agent)
      -> decide            (TutorAgent proposes an action, now history-aware)
      -> enforce           (clamp the action to grade + teaching state)
      -> classify          (deterministic-first error typing)
      -> advance state     (attempt count, hint level, phase)
      -> persist attempt   (AttemptStore.record)
      -> update memory     (StudentProfileV2.record_attempt -> ProfileStore.save)
      -> save state        (TeachingStateStore.save)
      -> recommend         (recommender_v2 -> next problems)

Verification, enforcement, classification, persistence, profile update and
recommendation are all deterministic, so the whole function is unit-testable
with a StubTutorAgent and in-memory stores — no LLM, no Supabase.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from pydantic import BaseModel

from verifier import verify_answer

from .agent import TutorAgentProtocol
from .classify import classify_math_error, coarse_bucket
from .persistence import AttemptStore, ProfileStore, TeachingStateStore
from .state import (
    EvidenceRecord,
    Grade,
    GradeStatus,
    HintLevel,
    MisconceptionType,
    Problem,
    ProblemPhase,
    StudentAttempt,
    TeachingDecision,
    ToolName,
    TutorAction,
    enforce,
)

logger = logging.getLogger(__name__)


class TutorTurnResult(BaseModel):
    """Everything a caller (API/UI) needs after one graded turn."""

    grade: Grade
    decision: TeachingDecision
    phase: ProblemPhase
    hint_level: HintLevel
    misconception: Optional[MisconceptionType]
    attempt_id: Optional[str]
    recommendations: List[dict]


class TeachingTurnResult(BaseModel):
    """Everything a caller needs after one follow-up teaching turn (no grading)."""

    decision: TeachingDecision
    phase: ProblemPhase
    hint_level: HintLevel
    ended: bool                       # problem resolved/abandoned — stop the dialogue
    redirect_to_submit: bool          # student pasted a final answer → use /api/attempt
    tool_used: Optional[ToolName] = None
    evidence: Optional[EvidenceRecord] = None


def _grade(problem: Problem, attempt: StudentAttempt) -> Grade:
    result = verify_answer(
        student_answer=attempt.answer,
        official_answer=problem.official_answer,
        problem_context=problem.text,
        problem_type=problem.problem_type,
    )
    return Grade.from_verification(result)


def _resolve_error(
    grade: Grade, decision: TeachingDecision, attempt: StudentAttempt, problem: Problem
) -> Tuple[Optional[MisconceptionType], Optional[str]]:
    """Deterministic-first error classification.

    Symbolic evidence wins; when it's inconclusive (UNKNOWN) we fall back to the
    agent's self-diagnosed misconception. Returns (misconception, coarse_bucket).
    """
    if grade.status == GradeStatus.CORRECT:
        return None, None

    misconception = classify_math_error(
        attempt.answer, problem.official_answer, grade
    )
    if misconception == MisconceptionType.UNKNOWN and decision.diagnosed_misconception:
        misconception = decision.diagnosed_misconception

    # We can't verify the answer at all — keep the (pedagogical) misconception
    # label but DON'T count it as a graded error bucket in the mastery profile.
    if grade.status == GradeStatus.UNVERIFIABLE:
        return misconception, "uncertain"

    return misconception, coarse_bucket(misconception)


def _profile_summary(profile, problem: Problem) -> str:
    """A short, DISPLAYABLE mastery digest for the agent prompt (no raw dumps)."""
    from taxonomy import normalize_to_topic

    lines = [f"STUDENT MASTERY (course {profile.course}):"]
    total = profile.total_correct + profile.total_incorrect
    if total:
        lines.append(
            f"  overall: {profile.overall_accuracy:.0%} correct "
            f"({profile.total_correct}✓/{profile.total_incorrect}✗)"
        )
    canonical = normalize_to_topic(problem.topic, profile.course)
    te = profile.topic_estimates.get(canonical)
    if te is not None:
        lines.append(
            f"  {canonical}: {te.status_label} (score {te.score:.2f}, "
            f"{te.total_attempts} attempts)"
        )
        sub = te.subtopics.get(problem.subtopic) if problem.subtopic else None
        if sub is not None and sub.attempts:
            dep = sub.hint_dependency
            note = " — relies on hints" if dep >= 0.5 else ""
            lines.append(
                f"  {problem.subtopic}: {sub.status_label}, "
                f"hint-dependency {dep:.0%}{note}"
            )
    dominant = profile.get_dominant_error_type()
    if dominant:
        lines.append(f"  most common error type: {dominant}")
    if len(lines) == 1:
        return "STUDENT MASTERY: (no history yet)"
    return "\n".join(lines)


def _recommend(course: str, profile, recent: List[dict], limit: int) -> List[dict]:
    """Call the existing recommender, but never let it break the loop."""
    try:
        from recommender_v2 import recommend_problems_for_api

        return recommend_problems_for_api(
            course=course, profile=profile, recent_attempts=recent, limit=limit
        )
    except Exception as exc:  # pragma: no cover - data-dependent
        logger.warning("recommendation step failed, returning []: %s", exc)
        return []


def run_tutor_turn(
    *,
    problem: Problem,
    attempt: StudentAttempt,
    user_id: str,
    workspace_id: str,
    agent: TutorAgentProtocol,
    attempt_store: AttemptStore,
    profile_store: ProfileStore,
    teaching_state_store: TeachingStateStore,
    recommend_limit: int = 3,
) -> TutorTurnResult:
    """Run one full graded turn and persist its effects. See module docstring."""

    # 1. Ground truth.
    grade = _grade(problem, attempt)

    # 2. Load per-problem teaching memory and register this attempt.
    state = teaching_state_store.load(user_id, problem.id)
    state.register_attempt()

    # 3. Load long-term mastery and summarize it for the agent.
    profile = profile_store.load(user_id, problem.course)
    summary = _profile_summary(profile, problem)

    # 4. Agent proposes (history-aware), 5. enforcement disposes.
    proposed = agent.decide(problem, attempt, grade, state, summary)
    decision = enforce(proposed, grade, state)

    # 6. Deterministic-first error classification.
    misconception, error_bucket = _resolve_error(grade, decision, attempt, problem)

    # 7. Was this attempt scaffolded? (hints given on prior turns of THIS problem)
    used_hint = state.used_hint

    # 8. Advance the teaching state (attempt count already bumped; sets phase).
    state.advance(decision, grade)

    # 9. Persist the attempt (write side — this is what closes the loop).
    attempt_id = attempt_store.record(
        {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "question_id": problem.id,
            "source": attempt.source,
            "grade_status": grade.status.value,
            "is_correct": grade.is_correct,
            "action": decision.action.value,
            "final_answer": attempt.answer,
            "error_type": error_bucket,
            "misconception": misconception.value if misconception else None,
            "hint_level": decision.hint_level.value,
            "used_hint": used_hint,
            "topic": problem.topic,
            "concept": problem.subtopic,
        }
    )

    # 10. Update mastery memory (with the deterministic bucket + hint signal).
    profile.record_attempt(
        topic=problem.topic,
        subtopic=problem.subtopic,
        correct=grade.is_correct,
        error_type=error_bucket,
        question_id=problem.id,
        used_hint=used_hint,
    )
    profile_store.save(user_id, profile)

    # 11. Save the advanced teaching state.
    teaching_state_store.save(user_id, state)

    # 12. Recompute what to study next, now informed by this attempt.
    recent = attempt_store.recent(user_id, limit=20)
    recommendations = _recommend(problem.course, profile, recent, recommend_limit)

    return TutorTurnResult(
        grade=grade,
        decision=decision,
        phase=state.phase,
        hint_level=decision.hint_level,
        misconception=misconception,
        attempt_id=attempt_id,
        recommendations=recommendations,
    )


# --------------------------------------------------------------------------- #
# Follow-up teaching turn — the multi-turn dialogue loop (no grading)
# --------------------------------------------------------------------------- #
def _carried_grade(state) -> Grade:
    """Reconstruct the background verdict for a teaching turn from the last graded
    attempt. Defaults to INCORRECT (the common teaching case) if none recorded."""
    status = state.last_grade_status or GradeStatus.INCORRECT
    return Grade(
        is_correct=status == GradeStatus.CORRECT,
        is_uncertain=status == GradeStatus.UNVERIFIABLE,
        verifier_type="carried",
        confidence=1.0,
        reason=f"Original attempt was {status.value} (carried as background).",
    )


def _ended_result(decision: TeachingDecision, phase: ProblemPhase) -> TeachingTurnResult:
    return TeachingTurnResult(
        decision=decision,
        phase=phase,
        hint_level=decision.hint_level,
        ended=True,
        redirect_to_submit=False,
    )


def run_teaching_turn(
    *,
    problem: Problem,
    student_message: str,
    user_id: str,
    agent: TutorAgentProtocol,
    profile_store: ProfileStore,
    teaching_state_store: TeachingStateStore,
) -> TeachingTurnResult:
    """Advance one follow-up teaching turn on a problem already in TEACHING.

    Unlike `run_tutor_turn`, this does NOT run the verifier on the student's
    message, does NOT create an attempt, and does NOT touch mastery. It carries
    the original verdict as background, lets the agent make at most ONE tool call
    and ONE teaching move, then advances + persists the per-problem teaching
    state. The verifier remains the sole authority on the final answer: if the
    student pastes a complete answer here, the agent flags `redirect_to_submit`
    and the caller routes them to the formal `/api/attempt` path.
    """
    state = teaching_state_store.load(user_id, problem.id)

    # A problem that's already done gets no further teaching.
    if state.phase in (ProblemPhase.RESOLVED, ProblemPhase.ABANDONED):
        return _ended_result(
            TeachingDecision(
                action=TutorAction.END_PROBLEM,
                message="This problem is already wrapped up — pick a new one to keep going.",
                reasoning=f"Problem already {state.phase.value}; teaching locked.",
            ),
            state.phase,
        )

    state.teach_turn_count += 1
    carried = _carried_grade(state)
    profile = profile_store.load(user_id, problem.course)
    summary = _profile_summary(profile, problem)

    # 1. First decision — the agent may finalize OR request one tool.
    decision = agent.propose(
        problem, student_message, carried, state, summary, allow_tools=True
    )

    # 2. At most one tool: run it, feed the structured evidence back, finalize.
    evidence: Optional[EvidenceRecord] = None
    if decision.tool_request is not None:
        from .tools import run_tool

        evidence = run_tool(decision.tool_request, problem, state.teach_turn_count)
        decision = agent.propose(
            problem,
            student_message,
            carried,
            state,
            summary,
            allow_tools=False,
            evidence=evidence,
        )

    # 3a. Pasted-answer redirect: this is NOT a teaching move — do not enforce or
    #     advance one (which could escalate a hint or change phase). Persist the
    #     context and hand off to the formal submit path with a fixed, safe action.
    if decision.redirect_to_submit:
        msg = decision.message or (
            "That looks like a complete answer — submit it with the answer box so "
            "I can check it."
        )
        if evidence is not None:
            state.append_evidence(evidence)
        state.append_transcript("student", student_message)
        state.append_transcript("tutor", msg)
        teaching_state_store.save(user_id, state)
        return TeachingTurnResult(
            decision=TeachingDecision(
                action=TutorAction.ASK_CLARIFICATION, message=msg, redirect_to_submit=True
            ),
            phase=state.phase,
            hint_level=state.hint_level,
            ended=False,
            redirect_to_submit=True,
            tool_used=evidence.tool if evidence is not None else None,
            evidence=evidence,
        )

    # 3b. Enforce the move against grade + state, then fold it into the state.
    enforced = enforce(decision, carried, state)
    state.advance(enforced, carried)

    # 4. Persist bounded context: structured evidence + the two dialogue lines.
    if evidence is not None:
        state.append_evidence(evidence)
    state.append_transcript("student", student_message)
    state.append_transcript("tutor", enforced.message)
    teaching_state_store.save(user_id, state)

    return TeachingTurnResult(
        decision=enforced,
        phase=state.phase,
        hint_level=enforced.hint_level,
        ended=state.phase in (ProblemPhase.RESOLVED, ProblemPhase.ABANDONED),
        redirect_to_submit=False,
        tool_used=evidence.tool if evidence is not None else None,
        evidence=evidence,
    )
