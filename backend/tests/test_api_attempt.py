"""
Endpoint-level tests for POST /api/attempt — the single execution path for one
typed student attempt (wraps claire_core.run_tutor_turn).

Runs fully offline:
  * the tutor LLM layer is replaced with a StubTutorAgent (no network),
  * the graded problem is injected (no dependence on question-bank IDs),
  * requests are anonymous → ephemeral in-memory stores (no Supabase).

A unique X-User-ID per request keeps the daily rate limit from bleeding across
tests.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

import api
from claire_core import Problem as CoreProblem
from claire_core import StubTutorAgent, TeachingDecision, TutorAction


DERIV = CoreProblem(
    id="q_deriv_1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="derivative",
    course="124",
)


@pytest.fixture
def client():
    with TestClient(api.app) as c:
        yield c


def _headers():
    # Unique identity per call → isolated usage counter, avoids 429 flakiness.
    return {"X-User-ID": uuid.uuid4().hex}


def _stub(monkeypatch, decision=None):
    monkeypatch.setattr(api, "_build_tutor_agent", lambda: StubTutorAgent(decision))


def _inject_problem(monkeypatch, problem=DERIV):
    monkeypatch.setattr(
        api, "_load_core_problem", lambda course, pid, part: problem
    )


# --------------------------------------------------------------------------- #
# Happy paths
# --------------------------------------------------------------------------- #
def test_correct_answer_confirms(client, monkeypatch):
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "3*x**2"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["grade_status"] == "correct"
    assert data["action"] == TutorAction.CONFIRM_CORRECT.value
    assert data["phase"] == "resolved"
    assert data["attempt_id"] is not None
    assert data["persisted"] is False  # anonymous → ephemeral
    assert isinstance(data["recommendations"], list)


def test_incorrect_answer_does_not_confirm(client, monkeypatch):
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "2*x"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["grade_status"] == "incorrect"
    assert data["action"] != TutorAction.CONFIRM_CORRECT.value
    assert data["phase"] == "teaching"


def test_response_exposes_full_structured_shape(client, monkeypatch):
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "2*x"},
        headers=_headers(),
    )
    data = resp.json()
    for key in (
        "is_correct", "is_uncertain", "grade_status", "action", "hint_level",
        "misconception", "message", "phase", "attempt_id", "recommendations",
        "persisted",
    ):
        assert key in data


# --------------------------------------------------------------------------- #
# Enforcement runs INSIDE the endpoint (no trust in the agent)
# --------------------------------------------------------------------------- #
def test_endpoint_enforces_against_rogue_agent(client, monkeypatch):
    rogue = TeachingDecision(
        action=TutorAction.CONFIRM_CORRECT, message="Perfect, that's right!"
    )
    _stub(monkeypatch, rogue)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "2*x"},  # wrong
        headers=_headers(),
    )
    data = resp.json()
    assert data["is_correct"] is False
    assert data["action"] != TutorAction.CONFIRM_CORRECT.value


# --------------------------------------------------------------------------- #
# Error handling
# --------------------------------------------------------------------------- #
def test_unknown_problem_returns_404(client, monkeypatch):
    _stub(monkeypatch)
    monkeypatch.setattr(api, "_load_core_problem", lambda course, pid, part: None)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "nope", "answer": "3*x**2"},
        headers=_headers(),
    )
    assert resp.status_code == 404


def test_problem_without_answer_returns_422(client, monkeypatch):
    _stub(monkeypatch)
    no_answer = DERIV.model_copy(update={"official_answer": ""})
    _inject_problem(monkeypatch, no_answer)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "3*x**2"},
        headers=_headers(),
    )
    assert resp.status_code == 422
