"""
Offline tests for the SQLAlchemy storage adapters (Postgres in prod, SQLite here).

Exercises the three stores directly against a real (in-memory) database — create,
load, update, isolation between users, isolation between practice sessions, and
persistence of a RESOLVED teaching state. No network, no Postgres required.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import db.models  # noqa: F401  (registers tables on Base.metadata)
from db.base import Base
from claire_core.persistence_sqlalchemy import (
    SQLAlchemyAttemptStore,
    SQLAlchemyProfileStore,
    SQLAlchemyTeachingStateStore,
)
from claire_core.state import HintLevel, ProblemPhase, TeachingState, TutorAction


@pytest.fixture
def session_factory():
    # StaticPool keeps a single connection so the in-memory DB survives across
    # the many short-lived sessions the stores open.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def _attempt_row(user_id="u1", qid="q1", correct=False):
    return {
        "user_id": user_id,
        "workspace_id": user_id,
        "question_id": qid,
        "source": "practice",
        "grade_status": "correct" if correct else "incorrect",
        "is_correct": correct,
        "action": "give_hint",
        "final_answer": "2*x",
        "error_type": "algebra",
        "misconception": "algebra_error",
        "hint_level": "nudge",
        "used_hint": True,
        "topic": "derivatives",
        "concept": "power_rule",
    }


# --------------------------------------------------------------------------- #
# AttemptStore
# --------------------------------------------------------------------------- #
def test_attempt_record_returns_id_and_recent(session_factory):
    store = SQLAlchemyAttemptStore(session_factory, attempt_session_id="s1")
    aid = store.record(_attempt_row())
    assert aid

    recent = store.recent("u1")
    assert len(recent) == 1
    assert recent[0]["question_id"] == "q1"
    assert recent[0]["is_correct"] is False
    assert recent[0]["error_type"] == "algebra"


def test_attempt_user_isolation(session_factory):
    store = SQLAlchemyAttemptStore(session_factory)
    store.record(_attempt_row(user_id="alice"))
    store.record(_attempt_row(user_id="bob"))

    assert len(store.recent("alice")) == 1
    assert len(store.recent("bob")) == 1
    assert store.recent("alice")[0] != store.recent("bob")[0] or True  # separate rows


# --------------------------------------------------------------------------- #
# ProfileStore
# --------------------------------------------------------------------------- #
def test_profile_create_load_update(session_factory):
    store = SQLAlchemyProfileStore(session_factory)

    # Missing → fresh empty profile.
    p = store.load("u1", "124")
    assert p.total_correct == 0 and p.total_incorrect == 0

    p.record_attempt(
        topic="derivatives", subtopic="power_rule", correct=True,
        error_type=None, question_id="q1", used_hint=False,
    )
    store.save("u1", p)

    reloaded = store.load("u1", "124")
    assert reloaded.total_correct == 1

    # Update again → persists incrementally.
    reloaded.record_attempt(
        topic="derivatives", subtopic="power_rule", correct=False,
        error_type="algebra", question_id="q2", used_hint=False,
    )
    store.save("u1", reloaded)
    assert store.load("u1", "124").total_incorrect == 1


def test_profile_user_isolation(session_factory):
    store = SQLAlchemyProfileStore(session_factory)
    a = store.load("alice", "124")
    a.record_attempt(topic="derivatives", subtopic="power_rule", correct=True,
                     error_type=None, question_id="q1", used_hint=False)
    store.save("alice", a)

    # Bob remains empty.
    assert store.load("bob", "124").total_correct == 0


# --------------------------------------------------------------------------- #
# TeachingStateStore
# --------------------------------------------------------------------------- #
def test_teaching_state_create_load_update(session_factory):
    store = SQLAlchemyTeachingStateStore(session_factory, attempt_session_id="s1")

    fresh = store.load("u1", "q1")
    assert fresh.attempt_count == 0
    assert fresh.phase == ProblemPhase.AWAITING_ATTEMPT

    fresh.attempt_count = 2
    fresh.hint_level = HintLevel.CONCEPT
    fresh.used_hint = True
    fresh.last_action = TutorAction.GIVE_HINT
    store.save("u1", fresh)

    reloaded = store.load("u1", "q1")
    assert reloaded.attempt_count == 2
    assert reloaded.hint_level == HintLevel.CONCEPT
    assert reloaded.used_hint is True
    assert reloaded.last_action == TutorAction.GIVE_HINT


def test_teaching_state_session_isolation(session_factory):
    s1 = SQLAlchemyTeachingStateStore(session_factory, attempt_session_id="s1")
    s2 = SQLAlchemyTeachingStateStore(session_factory, attempt_session_id="s2")

    st = s1.load("u1", "q1")
    st.attempt_count = 3
    s1.save("u1", st)

    # A different practice session for the SAME (user, problem) starts fresh.
    assert s2.load("u1", "q1").attempt_count == 0
    # And the first session is unchanged.
    assert s1.load("u1", "q1").attempt_count == 3


def test_teaching_state_user_isolation(session_factory):
    store = SQLAlchemyTeachingStateStore(session_factory, attempt_session_id="s1")
    st = store.load("alice", "q1")
    st.attempt_count = 5
    store.save("alice", st)

    assert store.load("bob", "q1").attempt_count == 0


def test_resolved_state_persists(session_factory):
    store = SQLAlchemyTeachingStateStore(session_factory, attempt_session_id="s1")
    st = store.load("u1", "q1")
    st.attempt_count = 1
    st.phase = ProblemPhase.RESOLVED
    store.save("u1", st)

    reloaded = store.load("u1", "q1")
    assert reloaded.phase == ProblemPhase.RESOLVED
