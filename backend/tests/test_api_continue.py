"""Endpoint tests for POST /api/attempt/continue — one follow-up teaching turn
(wraps claire_core.run_teaching_turn). Offline: stub agent, injected problem,
anonymous (ephemeral stores).
"""
import uuid

import pytest
from fastapi.testclient import TestClient

import api
from claire_core import Problem as CoreProblem
from claire_core import StubTutorAgent, TeachingDecision, ToolRequest, TutorAction, HintLevel


DERIV = CoreProblem(
    id="q_deriv_1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    course="124",
)


@pytest.fixture
def client():
    with TestClient(api.app) as c:
        yield c


def _headers():
    return {"X-User-ID": uuid.uuid4().hex}


def _stub_propose(monkeypatch, returns):
    monkeypatch.setattr(api, "_build_tutor_agent", lambda: StubTutorAgent(propose_returns=returns))


def _inject_problem(monkeypatch, problem=DERIV):
    monkeypatch.setattr(api, "_load_core_problem", lambda course, pid, part: problem)


def test_hint_turn_happy_path(client, monkeypatch):
    hint = TeachingDecision(action=TutorAction.GIVE_HINT, message="Use the power rule.", hint_level=HintLevel.NUDGE)
    _stub_propose(monkeypatch, [hint])
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt/continue",
        json={"problem_id": "q_deriv_1", "message": "I'm stuck"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == TutorAction.GIVE_HINT.value
    assert data["tool_used"] is None
    assert data["ended"] is False
    assert data["redirect_to_submit"] is False
    assert data["persisted"] is False  # anonymous


def test_tool_use_is_surfaced(client, monkeypatch):
    tool_req = TeachingDecision(tool_request=ToolRequest(tool="verify_step", expression="2x", expected="3x^2"))
    final = TeachingDecision(action=TutorAction.GIVE_HINT, message="Recheck the exponent.", hint_level=HintLevel.NUDGE)
    _stub_propose(monkeypatch, [tool_req, final])
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt/continue",
        json={"problem_id": "q_deriv_1", "message": "I got 2x"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["tool_used"] == "verify_step"


def test_pasted_final_answer_redirects(client, monkeypatch):
    redirect = TeachingDecision(
        action=TutorAction.ASK_CLARIFICATION,
        message="Submit that in the answer box so I can check it.",
        redirect_to_submit=True,
    )
    _stub_propose(monkeypatch, [redirect])
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt/continue",
        json={"problem_id": "q_deriv_1", "message": "3x^2"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["redirect_to_submit"] is True


def test_unknown_problem_returns_404(client, monkeypatch):
    _stub_propose(monkeypatch, [TeachingDecision(action=TutorAction.GIVE_HINT, message="x")])
    monkeypatch.setattr(api, "_load_core_problem", lambda course, pid, part: None)

    resp = client.post(
        "/api/attempt/continue",
        json={"problem_id": "nope", "message": "help"},
        headers=_headers(),
    )
    assert resp.status_code == 404
