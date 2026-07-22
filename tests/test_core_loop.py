"""
Tests for claire_core.loop — the closed adaptive loop.

These use the REAL SymPy verifier, REAL StudentProfileV2, REAL classifier and
REAL recommender, with in-memory stores and a stub (no-LLM) agent. They prove
the loop is CLOSED: a graded attempt is persisted, flows into mastery, and the
per-problem teaching state advances across attempts.
"""
import pytest

from claire_core import (
    HintLevel,
    InMemoryAttemptStore,
    InMemoryProfileStore,
    InMemoryTeachingStateStore,
    Problem,
    StubTutorAgent,
    StudentAttempt,
    TeachingDecision,
    TutorAction,
    run_tutor_turn,
)


@pytest.fixture
def stores():
    return (
        InMemoryAttemptStore(),
        InMemoryProfileStore(),
        InMemoryTeachingStateStore(),
    )


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
    attempt_store, profile_store, state_store = stores
    return run_tutor_turn(
        problem=problem,
        attempt=StudentAttempt(problem_id=problem.id, answer=answer),
        user_id="u1",
        workspace_id="w1",
        agent=agent or StubTutorAgent(),
        attempt_store=attempt_store,
        profile_store=profile_store,
        teaching_state_store=state_store,
    )


# --------------------------------------------------------------------------- #
# Correct answer path
# --------------------------------------------------------------------------- #
def test_correct_answer_confirms_and_records(stores):
    result = _run(DERIV_PROBLEM, "3*x**2", stores)

    assert result.grade.is_correct is True
    assert result.decision.action == TutorAction.CONFIRM_CORRECT
    assert result.phase.value == "resolved"
    assert result.attempt_id is not None


def test_correct_answer_updates_profile(stores):
    attempt_store, profile_store, _ = stores
    _run(DERIV_PROBLEM, "3*x**2", stores)

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
    assert result.decision.action != TutorAction.CONFIRM_CORRECT
    assert result.phase.value == "teaching"


def test_incorrect_answer_recorded_as_incorrect(stores):
    attempt_store, profile_store, _ = stores
    _run(DERIV_PROBLEM, "2*x", stores)

    rows = attempt_store.all_for("u1")
    assert rows[0]["is_correct"] is False
    profile = profile_store.load("u1", "124")
    assert profile.total_incorrect == 1


# --------------------------------------------------------------------------- #
# Enforcement is applied inside the loop, not just in unit tests
# --------------------------------------------------------------------------- #
def test_loop_enforces_against_a_rogue_agent(stores):
    rogue = StubTutorAgent(
        TeachingDecision(
            action=TutorAction.CONFIRM_CORRECT, message="Perfect, that's right!"
        )
    )
    result = _run(DERIV_PROBLEM, "2*x", stores, agent=rogue)
    assert result.grade.is_correct is False
    assert result.decision.action != TutorAction.CONFIRM_CORRECT


# --------------------------------------------------------------------------- #
# Teaching state advances across attempts on the same problem
# --------------------------------------------------------------------------- #
def test_teaching_state_accumulates_attempts(stores):
    _, _, state_store = stores
    hint = TeachingDecision(
        action=TutorAction.GIVE_HINT, message="think exponent", hint_level=HintLevel.NUDGE
    )
    _run(DERIV_PROBLEM, "2*x", stores, agent=StubTutorAgent(hint))
    _run(DERIV_PROBLEM, "x", stores, agent=StubTutorAgent(hint))

    state = state_store.load("u1", DERIV_PROBLEM.id)
    assert state.attempt_count == 2
    assert state.used_hint is True
    # The second identical hint was escalated by enforce().
    assert state.hint_level != HintLevel.NONE


def test_hint_then_correct_records_hint_dependency(stores):
    _, profile_store, _ = stores
    hint = TeachingDecision(
        action=TutorAction.GIVE_HINT, message="recall power rule", hint_level=HintLevel.NUDGE
    )
    _run(DERIV_PROBLEM, "2*x", stores, agent=StubTutorAgent(hint))   # wrong, hint given
    _run(DERIV_PROBLEM, "3*x**2", stores)                            # correct after a hint

    profile = profile_store.load("u1", "124")
    sub = profile.topic_estimates["derivatives"].subtopics["power_rule"]
    assert sub.correct_after_hint == 1
    assert sub.hint_dependency > 0.0


# --------------------------------------------------------------------------- #
# Deterministic error classification writes into the profile
# --------------------------------------------------------------------------- #
def test_sign_error_classified_deterministically(stores):
    # Official 3x^2, student -3x^2 → pure sign flip → algebra bucket.
    attempt_store, profile_store, _ = stores
    result = _run(DERIV_PROBLEM, "-3*x**2", stores)
    assert result.misconception is not None
    profile = profile_store.load("u1", "124")
    assert profile.error_counts["algebra"] >= 1


# --------------------------------------------------------------------------- #
# The loop feeds the recommender
# --------------------------------------------------------------------------- #
def test_turn_returns_recommendations_list(stores):
    result = _run(DERIV_PROBLEM, "2*x", stores)
    assert isinstance(result.recommendations, list)


def test_multiple_attempts_accumulate(stores):
    attempt_store, profile_store, _ = stores
    _run(DERIV_PROBLEM, "3*x**2", stores)  # correct
    _run(DERIV_PROBLEM, "2*x", stores)     # incorrect

    assert len(attempt_store.all_for("u1")) == 2
    profile = profile_store.load("u1", "124")
    assert profile.total_correct == 1
    assert profile.total_incorrect == 1
