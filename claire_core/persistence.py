"""
claire_core.persistence — storage ports + in-memory implementations.

These ports are the seam that finally CLOSES the adaptive loop. The old
codebase read attempt history everywhere but never wrote it, so every student
looked brand-new forever. Here the write side is a first-class, injectable
dependency:

    AttemptStore  — append-only log of graded attempts
    ProfileStore  — load/save a StudentProfileV2 (mastery memory)

The in-memory implementations make the whole loop testable with zero external
services. A Supabase-backed implementation lives in `persistence_supabase.py`
(thin adapter over the existing attempt_tracker + student_profiles table) and
is swapped in for production without touching loop.py.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Protocol

from student_profile_v2 import StudentProfileV2


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
