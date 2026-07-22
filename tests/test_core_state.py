"""
Tests for claire_core.state — the enforcement state machine.

These are pure (no LLM, no I/O) and assert the core safety properties:
the verifier's grade AND the per-problem teaching state clamp the agent's action.
"""
import pytest

from claire_core.state import (
    Grade,
    GradeStatus,
    HintLevel,
    ProblemPhase,
    TeachingDecision,
    TeachingState,
    TutorAction,
    allowed_actions,
    default_decision_for,
    enforce,
    next_hint_level,
)


def _grade(correct: bool, uncertain: bool = False) -> Grade:
    return Grade(
        is_correct=correct,
        is_uncertain=uncertain,
        verifier_type="derivative",
        confidence=1.0,
        reason="test",
    )


def _state(**kw) -> TeachingState:
    return TeachingState(problem_id="q1", **kw)


# --------------------------------------------------------------------------- #
# GradeStatus
# --------------------------------------------------------------------------- #
def test_grade_status_mapping():
    assert _grade(True).status == GradeStatus.CORRECT
    assert _grade(False).status == GradeStatus.INCORRECT
    assert _grade(False, uncertain=True).status == GradeStatus.UNVERIFIABLE
    # uncertain wins even if is_correct happens to be True
    assert _grade(True, uncertain=True).status == GradeStatus.UNVERIFIABLE


# --------------------------------------------------------------------------- #
# allowed_actions
# --------------------------------------------------------------------------- #
def test_correct_allows_only_confirm_or_end():
    assert allowed_actions(_grade(True)) == {
        TutorAction.CONFIRM_CORRECT,
        TutorAction.END_PROBLEM,
    }


def test_incorrect_forbids_confirm():
    legal = allowed_actions(_grade(False), _state(attempt_count=1))
    assert TutorAction.CONFIRM_CORRECT not in legal
    assert TutorAction.GIVE_HINT in legal
    assert TutorAction.IDENTIFY_ERROR in legal


def test_unverifiable_only_clarify_or_hint():
    legal = allowed_actions(_grade(False, uncertain=True))
    assert legal == {TutorAction.ASK_CLARIFICATION, TutorAction.GIVE_HINT}


# --------------------------------------------------------------------------- #
# Solution gate — no full solution before real effort
# --------------------------------------------------------------------------- #
def test_solution_locked_early():
    legal = allowed_actions(_grade(False), _state(attempt_count=1))
    assert TutorAction.SHOW_SOLUTION not in legal


def test_solution_unlocked_after_threshold():
    legal = allowed_actions(_grade(False), _state(attempt_count=3))
    assert TutorAction.SHOW_SOLUTION in legal


def test_solution_unlocked_after_near_solution_hint():
    legal = allowed_actions(
        _grade(False), _state(attempt_count=1, hint_level=HintLevel.NEAR_SOLUTION)
    )
    assert TutorAction.SHOW_SOLUTION in legal


def test_enforce_downgrades_premature_solution():
    grade = _grade(False)
    rogue = TeachingDecision(action=TutorAction.SHOW_SOLUTION, message="Answer: 3x^2")
    enforced = enforce(rogue, grade, _state(attempt_count=1))
    assert enforced.action != TutorAction.SHOW_SOLUTION
    assert "3x^2" not in enforced.message
    assert "ENFORCED" in enforced.reasoning


# --------------------------------------------------------------------------- #
# enforce — "LLM proposes, policy disposes"
# --------------------------------------------------------------------------- #
def test_enforce_overrides_congratulating_a_wrong_answer():
    grade = _grade(False)
    rogue = TeachingDecision(
        action=TutorAction.CONFIRM_CORRECT, message="Great job, that's correct!"
    )
    enforced = enforce(rogue, grade, _state(attempt_count=1))
    assert enforced.action != TutorAction.CONFIRM_CORRECT
    assert "correct" not in enforced.message.lower()
    assert "ENFORCED" in enforced.reasoning


def test_enforce_overrides_quizzing_a_correct_answer():
    grade = _grade(True)
    rogue = TeachingDecision(action=TutorAction.GIVE_HINT, message="Now try the next step...")
    enforced = enforce(rogue, grade, _state(attempt_count=1))
    assert enforced.action == TutorAction.CONFIRM_CORRECT


def test_enforce_keeps_legal_decision_untouched():
    grade = _grade(False)
    good = TeachingDecision(
        action=TutorAction.GIVE_HINT,
        message="Remember the power rule brings the exponent down.",
        hint_level=HintLevel.NUDGE,
    )
    enforced = enforce(good, grade, _state(attempt_count=1))
    assert enforced.action == TutorAction.GIVE_HINT
    assert enforced.message == good.message


# --------------------------------------------------------------------------- #
# Hint escalation — a repeated hint must dig deeper
# --------------------------------------------------------------------------- #
def test_repeated_hint_escalates_level():
    grade = _grade(False)
    state = _state(
        attempt_count=2, hint_level=HintLevel.NUDGE, last_action=TutorAction.GIVE_HINT
    )
    # Agent lazily proposes the same shallow hint again.
    repeat = TeachingDecision(
        action=TutorAction.GIVE_HINT, message="Try again", hint_level=HintLevel.NUDGE
    )
    enforced = enforce(repeat, grade, state)
    assert enforced.hint_level == next_hint_level(HintLevel.NUDGE)
    assert enforced.hint_level == HintLevel.CONCEPT


def test_deeper_hint_is_not_downgraded():
    grade = _grade(False)
    state = _state(
        attempt_count=2, hint_level=HintLevel.NUDGE, last_action=TutorAction.GIVE_HINT
    )
    deeper = TeachingDecision(
        action=TutorAction.GIVE_HINT, message="here", hint_level=HintLevel.NEXT_STEP
    )
    enforced = enforce(deeper, grade, state)
    assert enforced.hint_level == HintLevel.NEXT_STEP


# --------------------------------------------------------------------------- #
# Resolved / abandoned problems can't be taught further
# --------------------------------------------------------------------------- #
def test_resolved_problem_locks_teaching():
    grade = _grade(False)
    state = _state(phase=ProblemPhase.RESOLVED)
    rogue = TeachingDecision(action=TutorAction.GIVE_HINT, message="one more hint")
    enforced = enforce(rogue, grade, state)
    assert enforced.action == TutorAction.END_PROBLEM


# --------------------------------------------------------------------------- #
# TeachingState.advance
# --------------------------------------------------------------------------- #
def test_state_advance_tracks_hint_and_phase():
    state = _state()
    state.register_attempt()
    assert state.attempt_count == 1
    assert state.phase == ProblemPhase.EVALUATING

    decision = TeachingDecision(
        action=TutorAction.GIVE_HINT, message="think about the exponent",
        hint_level=HintLevel.NUDGE,
    )
    state.advance(decision, _grade(False))
    assert state.used_hint is True
    assert state.hint_level == HintLevel.NUDGE
    assert state.phase == ProblemPhase.TEACHING
    assert state.last_action == TutorAction.GIVE_HINT


def test_state_advance_resolves_on_correct():
    state = _state()
    state.register_attempt()
    decision = TeachingDecision(action=TutorAction.CONFIRM_CORRECT, message="nice")
    state.advance(decision, _grade(True))
    assert state.phase == ProblemPhase.RESOLVED


def test_show_solution_resolves_problem():
    state = _state(attempt_count=3)
    decision = TeachingDecision(action=TutorAction.SHOW_SOLUTION, message="here it is")
    state.advance(decision, _grade(False))
    assert state.phase == ProblemPhase.RESOLVED


# --------------------------------------------------------------------------- #
# defaults
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "grade,expected",
    [
        (_grade(True), TutorAction.CONFIRM_CORRECT),
        (_grade(False), TutorAction.IDENTIFY_ERROR),
        (_grade(False, uncertain=True), TutorAction.ASK_CLARIFICATION),
    ],
)
def test_default_decision_matches_grade(grade, expected):
    assert default_decision_for(grade).action == expected
