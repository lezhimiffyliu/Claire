"""
claire_core.persistence — storage ports + in-memory implementations.

These ports are the seam that finally CLOSES the adaptive loop. The old
codebase read attempt history everywhere but never wrote it, so every student
looked brand-new forever. Here the write side is a first-class, injectable
dependency:

    AttemptStore  — append-only log of graded attempts
    ProfileStore  — load/save a StudentProfileV2 (mastery memory)

The in-memory implementations make the whole loop testable with zero external
services. The production implementation lives in `persistence_sqlalchemy.py`
(SQLAlchemy 2.x over Postgres, Alembic-managed) and is swapped in without
touching loop.py. `NullAttemptStore` / `NullProfileStore` /
`NullTeachingStateStore` below are the explicit non-persistent stores for the
anonymous path.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Protocol

from student_profile_v2 import StudentProfileV2

from .state import TeachingState


# --------------------------------------------------------------------------- #
# Ports (interfaces)
# --------------------------------------------------------------------------- #
class AttemptStore(Protocol):
    def record(self, attempt_row: dict) -> Optional[str]:
        """Persist one graded attempt. Returns an attempt id (or None on failure)."""
        ...

    def recent(self, user_id: str, limit: int = 20) -> List[dict]:
        """Most-recent-first attempts for a user."""
        ...


class ProfileStore(Protocol):
    def load(self, user_id: str, course: str) -> StudentProfileV2:
        """Load the student's mastery profile (create an empty one if none)."""
        ...

    def save(self, user_id: str, profile: StudentProfileV2) -> None:
        """Persist the mastery profile."""
        ...


class TeachingStateStore(Protocol):
    """Per-(user, problem) teaching memory — what lets a problem advance across
    attempts instead of restarting the dialogue every turn."""

    def load(self, user_id: str, problem_id: str) -> TeachingState:
        """Load teaching state (create a fresh one if none exists)."""
        ...

    def save(self, user_id: str, state: TeachingState) -> None:
        """Persist teaching state."""
        ...


# --------------------------------------------------------------------------- #
# In-memory implementations (tests / local dev)
# --------------------------------------------------------------------------- #
class InMemoryAttemptStore:
    """Non-persistent AttemptStore backed by a dict of lists."""

    def __init__(self) -> None:
        self._by_user: Dict[str, List[dict]] = {}

    def record(self, attempt_row: dict) -> Optional[str]:
        attempt_id = uuid.uuid4().hex
        row = {"id": attempt_id, **attempt_row}
        self._by_user.setdefault(attempt_row["user_id"], []).append(row)
        return attempt_id

    def recent(self, user_id: str, limit: int = 20) -> List[dict]:
        rows = self._by_user.get(user_id, [])
        return list(reversed(rows[-limit:]))

    # Convenience for tests / introspection
    def all_for(self, user_id: str) -> List[dict]:
        return list(self._by_user.get(user_id, []))


class InMemoryProfileStore:
    """Non-persistent ProfileStore that serializes via to_dict/from_dict."""

    def __init__(self) -> None:
        self._by_user: Dict[str, dict] = {}

    def load(self, user_id: str, course: str) -> StudentProfileV2:
        data = self._by_user.get(user_id)
        if data is None:
            return StudentProfileV2(course=course)
        return StudentProfileV2.from_dict(data)

    def save(self, user_id: str, profile: StudentProfileV2) -> None:
        self._by_user[user_id] = profile.to_dict()


class InMemoryTeachingStateStore:
    """Non-persistent TeachingStateStore keyed by (user_id, problem_id)."""

    def __init__(self) -> None:
        self._by_key: Dict[tuple, dict] = {}

    def load(self, user_id: str, problem_id: str) -> TeachingState:
        data = self._by_key.get((user_id, problem_id))
        if data is None:
            return TeachingState(problem_id=problem_id)
        return TeachingState(**data)

    def save(self, user_id: str, state: TeachingState) -> None:
        self._by_key[(user_id, state.problem_id)] = state.model_dump()


# --------------------------------------------------------------------------- #
# Explicit NON-persistent stores (anonymous path)
# --------------------------------------------------------------------------- #
# For anonymous users we grade + teach a single turn but deliberately DO NOT
# persist anything. These stores make that choice explicit rather than silently
# stashing teaching progression in process memory (which would leak across
# requests and misrepresent anonymous users as having durable state). Each turn
# starts from a fresh TeachingState; the API reports persisted=False.
class NullAttemptStore:
    """Discards attempts. Returns an ephemeral id so the turn still has one."""

    def record(self, attempt_row: dict) -> Optional[str]:
        return uuid.uuid4().hex

    def recent(self, user_id: str, limit: int = 20) -> List[dict]:
        return []


class NullProfileStore:
    """Always a fresh profile; saves are no-ops."""

    def load(self, user_id: str, course: str) -> StudentProfileV2:
        return StudentProfileV2(course=course)

    def save(self, user_id: str, profile: StudentProfileV2) -> None:
        return None


class NullTeachingStateStore:
    """Always a fresh state; saves are no-ops (no cross-request progression)."""

    def load(self, user_id: str, problem_id: str) -> TeachingState:
        return TeachingState(problem_id=problem_id)

    def save(self, user_id: str, state: TeachingState) -> None:
        return None
