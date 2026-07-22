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
    Grade,
    GradeStatus,
    HintLevel,
    MisconceptionType,
    Problem,
    ProblemPhase,
    StudentAttempt,
    TeachingDecision,
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
