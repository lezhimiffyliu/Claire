"""
claire_core.persistence_supabase — production storage adapters.

These implement the same AttemptStore / ProfileStore ports as the in-memory
versions, backed by Supabase (RLS-enforced) and the existing `attempt_tracker`.
Swapping them into `run_tutor_turn` requires NO change to loop.py:

    from claire_core.persistence_supabase import (
        SupabaseAttemptStore, SupabaseProfileStore,
    )
    run_tutor_turn(..., attempt_store=SupabaseAttemptStore(client),
                        profile_store=SupabaseProfileStore(client))

They require a valid authenticated Supabase client (user JWT), so they are
exercised by integration tests, not the offline unit suite. This module is the
"how to go to production" seam — kept thin and honest on purpose.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from student_profile_v2 import StudentProfileV2

logger = logging.getLogger(__name__)


class SupabaseAttemptStore:
    """AttemptStore backed by the `attempt_history` table via attempt_tracker."""

    def __init__(self, client) -> None:
        # `client` is an authenticated Supabase client (RLS: user_id = auth.uid()).
        self._client = client

    def record(self, attempt_row: dict) -> Optional[str]:
        from attempt_tracker import AttemptRecord, record_attempt

        record = AttemptRecord(
            user_id=attempt_row["user_id"],
            workspace_id=attempt_row["workspace_id"],
            question_id=attempt_row["question_id"],
            source=attempt_row.get("source", "practice"),
            is_correct=attempt_row.get("is_correct"),
            final_answer=attempt_row.get("final_answer"),
            error_type=attempt_row.get("error_type"),
            topic=attempt_row.get("topic"),
            concept=attempt_row.get("concept"),
        )
        return record_attempt(record)

    def recent(self, user_id: str, limit: int = 20) -> List[dict]:
        try:
            resp = (
                self._client.table("attempt_history")
                .select("question_id, topic, concept, is_correct, error_type, submitted_at")
                .eq("user_id", user_id)
                .order("submitted_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("SupabaseAttemptStore.recent failed: %s", exc)
            return []


class SupabaseProfileStore:
    """ProfileStore backed by `student_profiles.profile_data` (JSONB)."""

    def __init__(self, client) -> None:
        self._client = client

    def load(self, user_id: str, course: str) -> StudentProfileV2:
        try:
            resp = (
                self._client.table("student_profiles")
                .select("profile_data")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            data = (resp.data or {}).get("profile_data")
            if data:
                return StudentProfileV2.from_dict(data)
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("SupabaseProfileStore.load failed, using empty: %s", exc)
        return StudentProfileV2(course=course)

    def save(self, user_id: str, profile: StudentProfileV2) -> None:
        try:
            self._client.table("student_profiles").upsert(
                {"user_id": user_id, "profile_data": profile.to_dict()},
                on_conflict="user_id",
            ).execute()
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("SupabaseProfileStore.save failed: %s", exc)
