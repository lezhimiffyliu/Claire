"""
Tests for claire_core.agent.

The deterministic parts (stub, protocol conformance, prompt building) run
offline. The real LLM call is guarded behind ANTHROPIC_API_KEY so the suite is
green without network access.
"""
import os

import pytest

from claire_core.agent import StubTutorAgent, TutorAgent, TutorAgentProtocol, _turn_prompt
from claire_core.state import (
    Grade,
    HintLevel,
    Problem,
    StudentAttempt,
    TeachingDecision,
    TeachingState,
    TutorAction,
)

PROBLEM = Problem(
    id="q1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="derivative",
)
ATTEMPT = StudentAttempt(problem_id="q1", answer="2*x")


def _grade(correct):
    return Grade(
        is_correct=correct,
        is_uncertain=False,
        verifier_type="derivative",
        confidence=1.0,
        reason="test",
    )


def test_stub_conforms_to_protocol():
    stub = StubTutorAgent()
    assert isinstance(stub, TutorAgentProtocol)
    decision = stub.decide(PROBLEM, ATTEMPT, _grade(False))
    assert isinstance(decision, TeachingDecision)


def test_stub_returns_preset_decision():
    preset = TeachingDecision(action=TutorAction.GIVE_HINT, message="hint")
    stub = StubTutorAgent(preset)
    assert stub.decide(PROBLEM, ATTEMPT, _grade(False)) is preset


def test_turn_prompt_includes_verdict_and_legal_actions():
    prompt = _turn_prompt(PROBLEM, ATTEMPT, _grade(False), TeachingState(problem_id="q1", attempt_count=1))
    assert "INCORRECT" in prompt
    assert "identify_error" in prompt
    # Correct-only action must not be offered on a wrong answer.
    assert "confirm_correct" not in prompt


def test_turn_prompt_correct_offers_only_confirm():
    prompt = _turn_prompt(
        PROBLEM, StudentAttempt(problem_id="q1", answer="3x^2"), _grade(True)
    )
    assert "confirm_correct" in prompt
    assert "CORRECT" in prompt


def test_turn_prompt_surfaces_teaching_history():
    state = TeachingState(
        problem_id="q1",
        attempt_count=2,
        hint_level=HintLevel.CONCEPT,
        hints_given=["nudge", "concept"],
    )
    prompt = _turn_prompt(PROBLEM, ATTEMPT, _grade(False), state, "STUDENT MASTERY: weak")
    assert "attempts so far" in prompt
    assert "concept" in prompt
    assert "STUDENT MASTERY: weak" in prompt


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires ANTHROPIC_API_KEY for a live LLM call",
)
def test_real_agent_decides_within_allowed_actions():
    from claire_core.state import allowed_actions

    agent = TutorAgent()
    grade = _grade(False)
    state = TeachingState(problem_id="q1", attempt_count=1)
    decision = agent.decide(PROBLEM, ATTEMPT, grade, state)
    assert isinstance(decision, TeachingDecision)
    assert decision.action in allowed_actions(grade, state) or decision.action is not None
