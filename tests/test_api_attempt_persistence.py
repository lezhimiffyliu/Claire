"""
API-level tests for POST /api/attempt with REAL Postgres-shaped persistence
(SQLAlchemy over in-memory SQLite) and Clerk identity.

Covers the security + correctness contract:
  * authenticated attempts persist (attempts + profile + teaching state),
  * a forged X-User-ID header cannot authenticate anyone,
  * correct → RESOLVED, incorrect → TEACHING,
  * a rogue agent confirming a wrong answer is overridden by enforce(),
  * the official answer is read only from the server-side question bank,
  * a database failure surfaces an explicit error (no silent anonymous fallback),
  * anonymous requests are graded but explicitly NOT persisted.

And the headline guarantee — teaching progression advances across THREE separate
HTTP requests, through the real DB store, with hint escalation and mastery update.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api
import db.base as db_base
import db.models  # noqa: F401
from db.base import Base
from db.models import AttemptRow, TeachingStateRow
from claire_core import Problem as CoreProblem
from claire_core import StubTutorAgent, TeachingDecision, TutorAction
from claire_core.persistence_sqlalchemy import SQLAlchemyProfileStore
from claire_core.state import HintLevel


DERIV = CoreProblem(
    id="q_deriv_1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="derivative",
    course="124",
)

AUTHED_USER = "user_authed_1"


@pytest.fixture
def db_sf():
    """Configure the process-wide engine to a fresh in-memory SQLite DB."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    db_base.configure_engine(engine=engine)
    yield sessionmaker(bind=engine, expire_on_commit=False, future=True)
    db_base.reset_engine()


@pytest.fixture
def client():
    with TestClient(api.app) as c:
        yield c


def _headers():
    return {"X-User-ID": uuid.uuid4().hex}


def _as_user(monkeypatch, user_id=AUTHED_USER):
    monkeypatch.setattr(api, "get_optional_identity", lambda request: user_id)


def _stub(monkeypatch, decision=None):
    monkeypatch.setattr(api, "_build_tutor_agent", lambda: StubTutorAgent(decision))


def _inject_problem(monkeypatch, problem=DERIV):
    monkeypatch.setattr(api, "_load_core_problem", lambda course, pid, part: problem)


def _post(client, answer, session_id="sess-a", pid="q_deriv_1"):
    return client.post(
        "/api/attempt",
        json={
            "problem_id": pid,
            "answer": answer,
            "attempt_session_id": session_id,
        },
        headers=_headers(),
    )


# --------------------------------------------------------------------------- #
# Authenticated persistence
# --------------------------------------------------------------------------- #
def test_authenticated_correct_persists_and_resolves(client, db_sf, monkeypatch):
    _as_user(monkeypatch)
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = _post(client, "3*x**2")
    data = resp.json()
    assert data["is_correct"] is True
    assert data["grade_status"] == "correct"
    assert data["phase"] == "resolved"
    assert data["persisted"] is True

    with db_sf() as s:
        attempts = s.execute(
            select(AttemptRow).where(AttemptRow.user_id == AUTHED_USER)
        ).scalars().all()
        assert len(attempts) == 1
        assert attempts[0].grade_status == "correct"

        state = s.execute(
            select(TeachingStateRow).where(TeachingStateRow.user_id == AUTHED_USER)
        ).scalar_one()
        assert state.phase == "resolved"
        assert state.attempt_session_id == "sess-a"


def test_incorrect_goes_teaching(client, db_sf, monkeypatch):
    _as_user(monkeypatch)
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    data = _post(client, "2*x").json()
    assert data["is_correct"] is False
    assert data["grade_status"] == "incorrect"
    assert data["phase"] == "teaching"
    assert data["action"] != TutorAction.CONFIRM_CORRECT.value


def test_rogue_confirm_on_wrong_answer_is_enforced(client, db_sf, monkeypatch):
    _as_user(monkeypatch)
    rogue = TeachingDecision(
        action=TutorAction.CONFIRM_CORRECT, message="Perfect, that's right!"
    )
    _stub(monkeypatch, rogue)
    _inject_problem(monkeypatch)

    data = _post(client, "2*x").json()  # wrong
    assert data["is_correct"] is False
    assert data["action"] != TutorAction.CONFIRM_CORRECT.value


def test_official_answer_comes_from_server_bank(client, db_sf, monkeypatch):
    """The client never supplies the answer key; grading uses the injected
    server-side problem. A body field claiming correctness has no effect."""
    _as_user(monkeypatch)
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={
            "problem_id": "q_deriv_1",
            "answer": "2*x",
            "official_answer": "2*x",   # bogus, must be ignored
            "is_correct": True,          # bogus, must be ignored
        },
        headers=_headers(),
    )
    assert resp.json()["is_correct"] is False


# --------------------------------------------------------------------------- #
# Identity cannot be forged
# --------------------------------------------------------------------------- #
def test_forged_user_id_header_does_not_authenticate(client, db_sf, monkeypatch):
    # NOTE: identity is NOT monkeypatched here → real Clerk path (unconfigured →
    # anonymous). A client-supplied X-User-ID must not authenticate as anyone.
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    resp = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "3*x**2"},
        headers={"X-User-ID": "victim_user"},
    )
    data = resp.json()
    assert data["persisted"] is False  # treated as anonymous

    # Nothing was written under the forged identity.
    with db_sf() as s:
        rows = s.execute(
            select(AttemptRow).where(AttemptRow.user_id == "victim_user")
        ).scalars().all()
        assert rows == []


# --------------------------------------------------------------------------- #
# Failure handling + anonymous policy
# --------------------------------------------------------------------------- #
def test_db_failure_returns_explicit_error(client, monkeypatch):
    """Authenticated user + a broken DB (no tables) → explicit 500, never a
    silent fallback to anonymous/in-memory."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    # Deliberately DO NOT create tables → store reads/writes fail.
    db_base.configure_engine(engine=engine)
    try:
        _as_user(monkeypatch)
        _stub(monkeypatch)
        _inject_problem(monkeypatch)

        resp = _post(client, "3*x**2")
        assert resp.status_code == 500
        assert resp.json()["detail"]["error"] == "grading_failed"
    finally:
        db_base.reset_engine()


def test_anonymous_is_graded_but_not_persisted(client, db_sf, monkeypatch):
    # No identity monkeypatch → anonymous. Graded + taught, but persisted=False.
    _stub(monkeypatch)
    _inject_problem(monkeypatch)

    data = client.post(
        "/api/attempt",
        json={"problem_id": "q_deriv_1", "answer": "2*x"},
        headers=_headers(),
    ).json()
    assert data["is_correct"] is False
    assert data["persisted"] is False

    with db_sf() as s:
        assert s.execute(select(AttemptRow)).scalars().all() == []


# --------------------------------------------------------------------------- #
# THE headline test: progression across three separate HTTP requests
# --------------------------------------------------------------------------- #
def test_progression_across_three_requests(client, db_sf, monkeypatch):
    _as_user(monkeypatch)
    _inject_problem(monkeypatch)
    # Agent always proposes a shallow nudge; enforce() escalates on repeat.
    hint = TeachingDecision(
        action=TutorAction.GIVE_HINT,
        message="Think about the power rule. What is the exponent doing?",
        hint_level=HintLevel.NUDGE,
    )
    _stub(monkeypatch, hint)

    sid = "progression-session"

    # --- Request 1: wrong → first (nudge) hint, attempt_count = 1 ---
    r1 = _post(client, "2*x", session_id=sid).json()
    assert r1["grade_status"] == "incorrect"
    assert r1["action"] == TutorAction.GIVE_HINT.value
    assert r1["hint_level"] == HintLevel.NUDGE.value

    # --- Request 2: wrong again → reloads prior state, hint ESCALATES ---
    r2 = _post(client, "x", session_id=sid).json()
    assert r2["grade_status"] == "incorrect"
    assert r2["hint_level"] == HintLevel.CONCEPT.value  # escalated by enforce()

    with db_sf() as s:
        state = s.execute(
            select(TeachingStateRow).where(
                TeachingStateRow.user_id == AUTHED_USER,
                TeachingStateRow.attempt_session_id == sid,
            )
        ).scalar_one()
        assert state.attempt_count == 2
        assert state.hint_level == HintLevel.CONCEPT.value
        assert state.used_hint is True

    # --- Request 3: correct → reloads state, RESOLVED, mastery updated ---
    r3 = _post(client, "3*x**2", session_id=sid).json()
    assert r3["grade_status"] == "correct"
    assert r3["phase"] == "resolved"

    with db_sf() as s:
        state = s.execute(
            select(TeachingStateRow).where(
                TeachingStateRow.user_id == AUTHED_USER,
                TeachingStateRow.attempt_session_id == sid,
            )
        ).scalar_one()
        assert state.attempt_count == 3
        assert state.phase == "resolved"

        attempts = s.execute(
            select(AttemptRow).where(AttemptRow.user_id == AUTHED_USER)
        ).scalars().all()
        assert len(attempts) == 3  # all three turns recorded

    # Mastery reflects a correct-after-hint on power_rule. (Topic key is
    # taxonomy-normalized, so locate the subtopic across all topic estimates.)
    profile = SQLAlchemyProfileStore(db_sf).load(AUTHED_USER, "124")
    assert profile.total_correct == 1
    assert profile.total_incorrect == 2

    subs = [
        sub
        for topic in profile.topic_estimates.values()
        for name, sub in topic.subtopics.items()
        if name == "power_rule"
    ]
    assert subs, "expected a power_rule subtopic estimate to be recorded"
    assert subs[0].correct_after_hint == 1
    assert subs[0].hint_dependency > 0.0
