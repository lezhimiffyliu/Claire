"""
claire_core.persistence_sqlalchemy — production storage adapters (Postgres).

These implement the SAME AttemptStore / ProfileStore / TeachingStateStore ports
as the in-memory versions, backed by SQLAlchemy 2.x against Postgres (Neon in
prod, local Postgres in dev, in-memory SQLite in tests). Swapping them into
`run_tutor_turn` requires NO change to loop.py / state.py / agent.py / verifier.

Session semantics
-----------------
`loop.py` calls ``teaching_state_store.load(user_id, problem_id)`` — it knows
nothing about practice sessions. We keep it that way by binding the
``attempt_session_id`` at STORE CONSTRUCTION (per request), so the same three
method signatures transparently scope to one practice session:

    * same session id  -> same TeachingState reloaded across HTTP requests
    * problem solved    -> row persists with phase = RESOLVED
    * restart problem   -> caller passes a NEW session id -> fresh state
    * different tab/run  -> different session id -> no shared hint history
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from student_profile_v2 import StudentProfileV2

from .state import TeachingState

logger = logging.getLogger(__name__)

DEFAULT_SESSION = "default"


def _factory(session_factory: Optional[sessionmaker]) -> sessionmaker:
    if session_factory is not None:
        return session_factory
    from db.base import get_sessionmaker

    return get_sessionmaker()


@contextmanager
def _scope(session_factory: sessionmaker) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class SQLAlchemyAttemptStore:
    """AttemptStore backed by the `attempts` table."""

    def __init__(
        self,
        session_factory: Optional[sessionmaker] = None,
        *,
        attempt_session_id: str = DEFAULT_SESSION,
    ) -> None:
        self._sf = _factory(session_factory)
        self._session_id = attempt_session_id or DEFAULT_SESSION

    def record(self, attempt_row: dict) -> Optional[str]:
        from db.models import AttemptRow

        row = AttemptRow(
            user_id=attempt_row["user_id"],
            problem_id=attempt_row["question_id"],
            attempt_session_id=self._session_id,
            workspace_id=attempt_row.get("workspace_id"),
            source=attempt_row.get("source", "practice"),
            submitted_answer=attempt_row.get("final_answer"),
            grade_status=attempt_row.get("grade_status"),
            is_correct=attempt_row.get("is_correct"),
            action=attempt_row.get("action"),
            hint_level=attempt_row.get("hint_level"),
            misconception=attempt_row.get("misconception"),
            error_type=attempt_row.get("error_type"),
            used_hint=bool(attempt_row.get("used_hint", False)),
            topic=attempt_row.get("topic"),
            concept=attempt_row.get("concept"),
        )
        with _scope(self._sf) as s:
            s.add(row)
            s.flush()
            return row.id

    def recent(self, user_id: str, limit: int = 20) -> List[dict]:
        from db.models import AttemptRow

        with _scope(self._sf) as s:
            rows = (
                s.execute(
                    select(AttemptRow)
                    .where(AttemptRow.user_id == user_id)
                    .order_by(AttemptRow.created_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "question_id": r.problem_id,
                    "topic": r.topic,
                    "concept": r.concept,
                    "is_correct": r.is_correct,
                    "error_type": r.error_type,
                    "submitted_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]


class SQLAlchemyProfileStore:
    """ProfileStore backed by `student_profiles.profile_data` (JSONB)."""

    def __init__(self, session_factory: Optional[sessionmaker] = None) -> None:
        self._sf = _factory(session_factory)

    def load(self, user_id: str, course: str) -> StudentProfileV2:
        from db.models import StudentProfileRow

        with _scope(self._sf) as s:
            row = s.execute(
                select(StudentProfileRow).where(
                    StudentProfileRow.user_id == user_id,
                    StudentProfileRow.course == course,
                )
            ).scalar_one_or_none()
            if row and row.profile_data:
                return StudentProfileV2.from_dict(row.profile_data)
        return StudentProfileV2(course=course)

    def save(self, user_id: str, profile: StudentProfileV2) -> None:
        from db.models import StudentProfileRow

        with _scope(self._sf) as s:
            row = s.execute(
                select(StudentProfileRow).where(
                    StudentProfileRow.user_id == user_id,
                    StudentProfileRow.course == profile.course,
                )
            ).scalar_one_or_none()
            data = profile.to_dict()
            if row is None:
                s.add(
                    StudentProfileRow(
                        user_id=user_id, course=profile.course, profile_data=data
                    )
                )
            else:
                row.profile_data = data


class SQLAlchemyTeachingStateStore:
    """TeachingStateStore backed by `teaching_states`, scoped to one practice
    session via `attempt_session_id` bound at construction."""

    def __init__(
        self,
        session_factory: Optional[sessionmaker] = None,
        *,
        attempt_session_id: str = DEFAULT_SESSION,
    ) -> None:
        self._sf = _factory(session_factory)
        self._session_id = attempt_session_id or DEFAULT_SESSION

    def load(self, user_id: str, problem_id: str) -> TeachingState:
        from db.models import TeachingStateRow

        with _scope(self._sf) as s:
            row = s.execute(
                select(TeachingStateRow).where(
                    TeachingStateRow.user_id == user_id,
                    TeachingStateRow.problem_id == problem_id,
                    TeachingStateRow.attempt_session_id == self._session_id,
                )
            ).scalar_one_or_none()
            if row and row.state_data:
                # state_data is the authoritative, full-fidelity snapshot.
                return TeachingState(**row.state_data)
        return TeachingState(problem_id=problem_id)

    def save(self, user_id: str, state: TeachingState) -> None:
        from db.models import TeachingStateRow

        with _scope(self._sf) as s:
            row = s.execute(
                select(TeachingStateRow).where(
                    TeachingStateRow.user_id == user_id,
                    TeachingStateRow.problem_id == state.problem_id,
                    TeachingStateRow.attempt_session_id == self._session_id,
                )
            ).scalar_one_or_none()
            projection = self._project(user_id, state)
            if row is None:
                s.add(TeachingStateRow(**projection))
            else:
                for k, v in projection.items():
                    setattr(row, k, v)

    def _project(self, user_id: str, state: TeachingState) -> dict:
        return {
            "user_id": user_id,
            "problem_id": state.problem_id,
            "attempt_session_id": self._session_id,
            "phase": state.phase.value,
            "attempt_count": state.attempt_count,
            "hint_level": state.hint_level.value,
            "misconception": (
                state.diagnosed_misconception.value
                if state.diagnosed_misconception
                else None
            ),
            "explained_concepts": list(state.explained_concepts),
            "hints_given": list(state.hints_given),
            "last_action": state.last_action.value if state.last_action else None,
            "last_question": state.last_question,
            "used_hint": state.used_hint,
            "state_data": state.model_dump(mode="json"),
        }
