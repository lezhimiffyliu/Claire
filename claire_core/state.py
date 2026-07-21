"""
claire_core.state — domain models + the teaching state machine.

This is the deterministic heart of the tutor. It has NO LLM and NO I/O, so it
is fast and fully unit-testable. The central idea (revived and actually wired
from the old, dead `teaching_orchestrator`):

    The LLM proposes, the verifier disposes.

The agent may *suggest* a teaching action, but the SymPy verifier result is
ground truth. `enforce()` clamps the agent's proposed action to the set that is
legal for the verified grade, so the tutor can never (for example) congratulate
a wrong answer or keep quizzing a correct one.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Set

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class SessionPhase(str, Enum):
    """Where a single problem-solving session currently sits."""

    AWAITING_ATTEMPT = "awaiting_attempt"  # student has not answered yet
    GRADED = "graded"                      # verifier has judged the attempt
    TEACHING = "teaching"                  # tutor is guiding after a wrong/uncertain try
    RESOLVED = "resolved"                  # correct answer confirmed, session done


class TutorAction(str, Enum):
    """The mutually-exclusive things the tutor can do on a turn."""

    CONFIRM_CORRECT_AND_STOP = "confirm_correct_and_stop"
    GIVE_HINT = "give_hint"
    GIVE_FEEDBACK = "give_feedback"
    ASK_CLARIFICATION = "ask_clarification"
    SHOW_SOLUTION = "show_solution"


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #
class Problem(BaseModel):
    """A problem the student is working on."""

    id: str
    text: str
    official_answer: str
    topic: str
    subtopic: Optional[str] = None
    # One of: derivative | indefinite_integral | definite_integral | limit |
    # equation | algebraic. If None, the verifier auto-detects.
    problem_type: Optional[str] = None
    course: str = "124"


class StudentAttempt(BaseModel):
    """A single answer submitted by the student."""

    problem_id: str
    answer: str
    work: Optional[str] = None
    source: str = "practice"  # diagnostic | practice | handwritten_upload


class Grade(BaseModel):
    """Ground-truth judgment of an attempt (produced by verifier.py)."""

    is_correct: bool
    is_uncertain: bool
    verifier_type: str
    confidence: float
    reason: str

    @classmethod
    def from_verification(cls, result) -> "Grade":
        """Adapt a verifier.AnswerVerificationResult into a Grade."""
        return cls(
            is_correct=bool(result.is_correct),
            is_uncertain=bool(result.is_uncertain),
            verifier_type=result.verifier_type,
            confidence=float(result.confidence),
            reason=result.reason,
        )


class TeachingDecision(BaseModel):
    """A tutor's turn: what to do + what to say."""

    action: TutorAction
    message: str
    reasoning: str = ""
    # Optional pedagogical error classification for profile tracking:
    # concept | algebra | logic | careless | uncertain
    error_type: Optional[str] = Field(default=None)


# --------------------------------------------------------------------------- #
# The enforcement rules — verifier is ground truth
# --------------------------------------------------------------------------- #
def allowed_actions(grade: Grade) -> Set[TutorAction]:
    """The set of teaching actions that are legal for a given grade."""
    if grade.is_correct:
        return {TutorAction.CONFIRM_CORRECT_AND_STOP}
    if grade.is_uncertain:
        return {TutorAction.ASK_CLARIFICATION, TutorAction.GIVE_HINT}
    # Verified incorrect: anything except claiming it was correct.
    return {
        TutorAction.GIVE_HINT,
        TutorAction.GIVE_FEEDBACK,
        TutorAction.ASK_CLARIFICATION,
        TutorAction.SHOW_SOLUTION,
    }


def _default_action(grade: Grade) -> TutorAction:
    if grade.is_correct:
        return TutorAction.CONFIRM_CORRECT_AND_STOP
    if grade.is_uncertain:
        return TutorAction.ASK_CLARIFICATION
    return TutorAction.GIVE_FEEDBACK


_DEFAULT_MESSAGE = {
    TutorAction.CONFIRM_CORRECT_AND_STOP: "That's correct — nice work. Let's move on.",
    TutorAction.GIVE_HINT: "Not quite. Here's a hint to get you unstuck.",
    TutorAction.GIVE_FEEDBACK: "That isn't right yet. Let's look at where it went off track.",
    TutorAction.ASK_CLARIFICATION: "I couldn't fully read your work — can you walk me through your steps?",
    TutorAction.SHOW_SOLUTION: "Let's work through the full solution together.",
}


def default_decision_for(grade: Grade) -> TeachingDecision:
    """A safe decision derived purely from the grade (used as LLM fallback)."""
    action = _default_action(grade)
    return TeachingDecision(
        action=action,
        message=_DEFAULT_MESSAGE[action],
        reasoning="Derived from verifier grade (no LLM).",
    )


def enforce(proposed: TeachingDecision, grade: Grade) -> TeachingDecision:
    """
    Clamp the agent's proposed decision to what the verifier permits.

    - If the proposed action is legal for this grade, keep the agent's message.
    - If it is illegal (e.g. "confirm correct" on a wrong answer), override the
      action to a safe default AND replace the message, since a message written
      for the wrong action cannot be trusted.
    """
    legal = allowed_actions(grade)
    if proposed.action in legal:
        return proposed

    safe = _default_action(grade)
    return TeachingDecision(
        action=safe,
        message=_DEFAULT_MESSAGE[safe],
        reasoning=(
            f"ENFORCED: agent proposed '{proposed.action.value}' but verifier grade "
            f"(correct={grade.is_correct}, uncertain={grade.is_uncertain}) only allows "
            f"{sorted(a.value for a in legal)}."
        ),
        error_type=proposed.error_type,
    )


def phase_after(grade: Grade) -> SessionPhase:
    """The session phase implied by a grade."""
    if grade.is_correct:
        return SessionPhase.RESOLVED
    return SessionPhase.TEACHING
