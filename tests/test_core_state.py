"""
Tests for claire_core.state — the enforcement state machine.

These are pure (no LLM, no I/O) and assert the core safety property:
the verifier's grade is ground truth and clamps the agent's action.
"""
import pytest

from claire_core.state import (
    Grade,
    TeachingDecision,
    TutorAction,
    allowed_actions,
    default_decision_for,
    enforce,
    phase_after,
    SessionPhase,
)


def _grade(correct: bool, uncertain: bool = False) -> Grade:
    return Grade(
        is_correct=correct,
        is_uncertain=uncertain,
        verifier_type="derivative",
        confidence=1.0,
        reason="test",
    )


# --------------------------------------------------------------------------- #
# allowed_actions
# --------------------------------------------------------------------------- #
def test_correct_allows_only_confirm():
    assert allowed_actions(_grade(True)) == {TutorAction.CONFIRM_CORRECT_AND_STOP}


def test_incorrect_forbids_confirm():
    legal = allowed_actions(_grade(False))
    assert TutorAction.CONFIRM_CORRECT_AND_STOP not in legal
    assert TutorAction.GIVE_HINT in legal
    assert TutorAction.GIVE_FEEDBACK in legal


def test_uncertain_prefers_clarify_or_hint():
    legal = allowed_actions(_grade(False, uncertain=True))
    assert legal == {TutorAction.ASK_CLARIFICATION, TutorAction.GIVE_HINT}


# --------------------------------------------------------------------------- #
# enforce — the "LLM proposes, verifier disposes" property
# --------------------------------------------------------------------------- #
def test_enforce_overrides_congratulating_a_wrong_answer():
    """The classic bug: agent says 'great job!' on a wrong answer."""
    grade = _grade(False)
    rogue = TeachingDecision(
        action=TutorAction.CONFIRM_CORRECT_AND_STOP,
        message="Great job, that's correct!",
    )
    enforced = enforce(rogue, grade)
    assert enforced.action != TutorAction.CONFIRM_CORRECT_AND_STOP
    assert enforced.action == TutorAction.GIVE_FEEDBACK
    # The misleading message must be replaced, not kept.
    assert "correct" not in enforced.message.lower()
    assert "ENFORCED" in enforced.reasoning


def test_enforce_overrides_quizzing_a_correct_answer():
    grade = _grade(True)
    rogue = TeachingDecision(action=TutorAction.GIVE_HINT, message="Now try the next step...")
    enforced = enforce(rogue, grade)
    assert enforced.action == TutorAction.CONFIRM_CORRECT_AND_STOP


def test_enforce_keeps_legal_decision_untouched():
    grade = _grade(False)
    good = TeachingDecision(
        action=TutorAction.GIVE_HINT,
        message="Remember the power rule brings the exponent down.",
        error_type="concept",
    )
    enforced = enforce(good, grade)
    assert enforced.action == TutorAction.GIVE_HINT
    assert enforced.message == good.message
    assert enforced.error_type == "concept"


def test_enforce_preserves_error_type_on_override():
    grade = _grade(False)
    rogue = TeachingDecision(
        action=TutorAction.CONFIRM_CORRECT_AND_STOP,
        message="nice",
        error_type="algebra",
    )
    assert enforce(rogue, grade).error_type == "algebra"


# --------------------------------------------------------------------------- #
# defaults & phase
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "grade,expected",
    [
        (_grade(True), TutorAction.CONFIRM_CORRECT_AND_STOP),
        (_grade(False), TutorAction.GIVE_FEEDBACK),
        (_grade(False, uncertain=True), TutorAction.ASK_CLARIFICATION),
    ],
)
def test_default_decision_matches_grade(grade, expected):
    assert default_decision_for(grade).action == expected


def test_phase_after():
    assert phase_after(_grade(True)) == SessionPhase.RESOLVED
    assert phase_after(_grade(False)) == SessionPhase.TEACHING
