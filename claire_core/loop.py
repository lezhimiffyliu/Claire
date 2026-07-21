"""
claire_core.loop — the closed adaptive loop.

This is the fix for the project's #1 gap. The old code READ attempt history and
mastery everywhere but never WROTE it, so personalization never engaged. Here a
single call runs the full cycle and persists the outcome:

    attempt
      -> verify        (verifier.py = ground truth)
      -> decide        (TutorAgent proposes an action + message)
      -> enforce       (clamp the action to what the grade allows)
      -> persist       (AttemptStore.record)
      -> update memory (StudentProfileV2.record_attempt -> ProfileStore.save)
      -> recommend     (recommender_v2 -> next problems)

Because verification, persistence, profile update and recommendation are all
deterministic, this whole function is unit-testable with a StubTutorAgent and
in-memory stores — no LLM, no Supabase.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from pydantic import BaseModel

from verifier import verify_answer

from .agent import TutorAgentProtocol
from .persistence import AttemptStore, ProfileStore
from .state import (
    Grade,
    Problem,
    SessionPhase,
    StudentAttempt,
    TeachingDecision,
    enforce,
    phase_after,
)

logger = logging.getLogger(__name__)


class TutorTurnResult(BaseModel):
    """Everything a caller (API/UI) needs after one graded turn."""

    grade: Grade
    decision: TeachingDecision
    phase: SessionPhase
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


def _error_type_for(grade: Grade, decision: TeachingDecision) -> Optional[str]:
    if grade.is_correct:
        return None
    if grade.is_uncertain:
        return "uncertain"
    return decision.error_type  # may be None if the agent didn't classify


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
    recommend_limit: int = 3,
) -> TutorTurnResult:
    """Run one full graded turn and persist its effects. See module docstring."""

    # 1. Ground truth.
    grade = _grade(problem, attempt)

    # 2. Agent proposes, 3. enforcement disposes.
    proposed = agent.decide(problem, attempt, grade)
    decision = enforce(proposed, grade)

    # 4. Persist the attempt (write side — this is what closes the loop).
    error_type = _error_type_for(grade, decision)
    attempt_id = attempt_store.record(
        {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "question_id": problem.id,
            "source": attempt.source,
            "is_correct": grade.is_correct,
            "final_answer": attempt.answer,
            "error_type": error_type,
            "topic": problem.topic,
            "concept": problem.subtopic,
        }
    )

    # 5. Update mastery memory.
    profile = profile_store.load(user_id, problem.course)
    profile.record_attempt(
        topic=problem.topic,
        subtopic=problem.subtopic,
        correct=grade.is_correct,
        error_type=error_type,
        question_id=problem.id,
    )
    profile_store.save(user_id, profile)

    # 6. Recompute what to study next, now informed by this attempt.
    recent = attempt_store.recent(user_id, limit=20)
    recommendations = _recommend(problem.course, profile, recent, recommend_limit)

    return TutorTurnResult(
        grade=grade,
        decision=decision,
        phase=phase_after(grade),
        attempt_id=attempt_id,
        recommendations=recommendations,
    )
