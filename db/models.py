"""
db.models — SQLAlchemy ORM tables for the tutoring loop.

Three tables mirror the three storage ports:

    attempts          <- AttemptStore        (append-only graded attempts)
    student_profiles  <- ProfileStore         (mastery memory, JSON blob)
    teaching_states   <- TeachingStateStore    (per (user, problem, session) memory)

Design notes:
  * JSON columns use JSONB on Postgres and plain JSON on SQLite so the SAME
    models power both production (Neon) and the offline test suite.
  * `teaching_states` keeps BOTH normalized columns (queryable / assertable) AND
    a `state_data` blob, so a TeachingState round-trips with zero field loss even
    if the model grows fields the columns don't mirror.
  * `attempt_session_id` defaults to "default" (never NULL) so the uniqueness
    that gives us session/reset semantics is enforceable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

# JSONB on Postgres, JSON elsewhere (SQLite in tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")

DEFAULT_SESSION = "default"


def _uuid() -> str:
    return uuid.uuid4().hex


class AttemptRow(Base):
    """One graded attempt. Written by run_tutor_turn via SQLAlchemyAttemptStore."""

    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    attempt_session_id: Mapped[str] = mapped_column(
        String(128), index=True, nullable=False, default=DEFAULT_SESSION
    )
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="practice")

    submitted_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    action: Mapped[str | None] = mapped_column(String(48), nullable=True)
    hint_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    misconception: Mapped[str | None] = mapped_column(String(48), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    used_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    topic: Mapped[str | None] = mapped_column(String(128), nullable=True)
    concept: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StudentProfileRow(Base):
    """Mastery memory for one (user, course). Body is a StudentProfileV2 dump."""

    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "course", name="uq_profile_user_course"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    course: Mapped[str] = mapped_column(String(16), nullable=False, default="124")
    profile_data: Mapped[dict] = mapped_column(JSONType, default=dict)

    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TeachingStateRow(Base):
    """Per (user, problem, session) teaching memory — what advances the dialogue
    across attempts and marks a problem RESOLVED once solved."""

    __tablename__ = "teaching_states"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "problem_id",
            "attempt_session_id",
            name="uq_teaching_user_problem_session",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    attempt_session_id: Mapped[str] = mapped_column(
        String(128), index=True, nullable=False, default=DEFAULT_SESSION
    )

    # Normalized, queryable projection of TeachingState.
    phase: Mapped[str] = mapped_column(String(32), default="awaiting_attempt")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    hint_level: Mapped[str] = mapped_column(String(32), default="none")
    misconception: Mapped[str | None] = mapped_column(String(48), nullable=True)
    explained_concepts: Mapped[list] = mapped_column(JSONType, default=list)
    hints_given: Mapped[list] = mapped_column(JSONType, default=list)
    last_action: Mapped[str | None] = mapped_column(String(48), nullable=True)
    last_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    used_hint: Mapped[bool] = mapped_column(Boolean, default=False)

    # Full-fidelity round-trip blob (authoritative on load).
    state_data: Mapped[dict] = mapped_column(JSONType, default=dict)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
