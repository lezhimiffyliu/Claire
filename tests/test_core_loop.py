"""
Tests for claire_core.loop — the closed adaptive loop.

These use the REAL SymPy verifier, REAL StudentProfileV2, and REAL recommender,
with in-memory stores and a stub (no-LLM) agent. They prove the loop is CLOSED:
a graded attempt is persisted AND flows into the mastery profile.
"""
import pytest

from claire_core import (
    InMemoryAttemptStore,
    InMemoryProfileStore,
    Problem,
    StubTutorAgent,
    StudentAttempt,
    TeachingDecision,
    TutorAction,
    run_tutor_turn,
)


@pytest.fixture
def stores():
    return InMemoryAttemptStore(), InMemoryProfileStore()


DERIV_PROBLEM = Problem(
    id="q_deriv_1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="derivative",
    course="124",
)


def _run(problem, answer, stores, agent=None):
    attempt_store, profile_store = stores
    return run_tutor_turn(
        problem=problem,
        attempt=StudentAttempt(problem_id=problem.id, answer=answer),
        user_id="u1",
        workspace_id="w1",
        agent=agent or StubTutorAgent(),
        attempt_store=attempt_store,
        profile_store=profile_store,
    )


# --------------------------------------------------------------------------- #
# Correct answer path
# --------------------------------------------------------------------------- #
def test_correct_answer_confirms_and_records(stores):
    result = _run(DERIV_PROBLEM, "3*x**2", stores)

    assert result.grade.is_correct is True
    assert result.decision.action == TutorAction.CONFIRM_CORRECT_AND_STOP
    assert result.phase.value == "resolved"
    assert result.attempt_id is not None


def test_correct_answer_updates_profile(stores):
    attempt_store, profile_store = stores
    _run(DERIV_PROBLEM, "3*x**2", stores)

    # The write side actually persisted:
    assert len(attempt_store.all_for("u1")) == 1
    profile = profile_store.load("u1", "124")
    assert profile.total_correct == 1
    assert profile.total_incorrect == 0
    assert "derivatives" in profile.topic_estimates


# --------------------------------------------------------------------------- #
# Incorrect answer path
# --------------------------------------------------------------------------- #
def test_incorrect_answer_does_not_confirm(stores):
    result = _run(DERIV_PROBLEM, "2*x", stores)

    assert result.grade.is_correct is False
    assert result.decision.action != TutorAction.CONFIRM_CORRECT_AND_STOP
    assert result.phase.value == "teaching"


def test_incorrect_answer_recorded_as_incorrect(stores):
    attempt_store, profile_store = stores
    _run(DERIV_PROBLEM, "2*x", stores)

    rows = attempt_store.all_for("u1")
    assert rows[0]["is_correct"] is False
    profile = profile_store.load("u1", "124")
    assert profile.total_incorrect == 1


# --------------------------------------------------------------------------- #
# Enforcement is applied inside the loop, not just in unit tests
# --------------------------------------------------------------------------- #
def test_loop_enforces_against_a_rogue_agent(stores):
    """A misbehaving agent that congratulates a wrong answer is overridden."""
    rogue = StubTutorAgent(
        TeachingDecision(
            action=TutorAction.CONFIRM_CORRECT_AND_STOP,
            message="Perfect, that's right!",
        )
    )
    result = _run(DERIV_PROBLEM, "2*x", stores, agent=rogue)
    assert result.grade.is_correct is False
    assert result.decision.action != TutorAction.CONFIRM_CORRECT_AND_STOP


# --------------------------------------------------------------------------- #
# The loop feeds the recommender
# --------------------------------------------------------------------------- #
def test_turn_returns_recommendations_list(stores):
    result = _run(DERIV_PROBLEM, "2*x", stores)
    assert isinstance(result.recommendations, list)


def test_multiple_attempts_accumulate(stores):
    attempt_store, profile_store = stores
    _run(DERIV_PROBLEM, "3*x**2", stores)  # correct
    _run(DERIV_PROBLEM, "2*x", stores)     # incorrect

    assert len(attempt_store.all_for("u1")) == 2
    profile = profile_store.load("u1", "124")
    assert profile.total_correct == 1
    assert profile.total_incorrect == 1
