"""
Attempt Tracker - records student attempts to Supabase.

Writes to attempt_history table for logged-in users.
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
import json


@dataclass
class AttemptRecord:
    """A single attempt record to be saved."""
    user_id: str  # Required for RLS
    workspace_id: str
    question_id: str
    source: str  # 'diagnostic' | 'practice' | 'handwritten_upload'
    is_correct: Optional[bool] = None
    final_answer: Optional[str] = None
    error_type: Optional[str] = None  # 'concept' | 'algebra' | 'logic' | 'careless' | 'uncertain'
    topic: Optional[str] = None
    concept: Optional[str] = None
    upload_session_id: Optional[str] = None
    analysis_summary: Optional[str] = None
    analysis_data: Optional[dict] = None
    uploaded_image_id: Optional[str] = None


def _get_supabase_client():
    """Get authenticated Supabase client (with user session for RLS)."""
    try:
        from auth import get_authenticated_client
        return get_authenticated_client()
    except ImportError:
        return None


def record_attempt(attempt: AttemptRecord) -> Optional[str]:
    """
    Record an attempt to the database.

    Args:
        attempt: AttemptRecord with all fields

    Returns:
        attempt_id (UUID) on success, None on failure
    """
    client = _get_supabase_client()
    if not client:
        print("[attempt_tracker] No Supabase client")
        return None

    try:
        data = {
            "user_id": attempt.user_id,
            "workspace_id": attempt.workspace_id,
            "question_id": attempt.question_id,
            "source": attempt.source,
            "is_correct": attempt.is_correct,
            "final_answer": attempt.final_answer,
            "error_type": attempt.error_type,
            "topic": attempt.topic,
            "concept": attempt.concept,
            "upload_session_id": attempt.upload_session_id,
            "analysis_summary": attempt.analysis_summary,
            "analysis_data": attempt.analysis_data,
            "uploaded_image_id": attempt.uploaded_image_id,
        }

        # Remove None values to let DB use defaults
        data = {k: v for k, v in data.items() if v is not None}

        result = client.table("attempt_history").insert(data).execute()

        if result.data:
            return result.data[0]["id"]
        return None

    except Exception as e:
        print(f"[attempt_tracker] record_attempt error: {e}")
        return None


def record_handwritten_attempt(
    user_id: str,
    workspace_id: str,
    question_id: str,
    analysis_result: dict,
    upload_session_id: Optional[str] = None,
    uploaded_image_id: Optional[str] = None,
) -> Optional[str]:
    """
    Convenience function to record a handwritten upload attempt.

    Args:
        user_id: The user ID (required for RLS)
        workspace_id: The workspace ID
        question_id: The problem ID (e.g., "uw_math_125_a25_p3")
        analysis_result: Full analysis result from vision analyzer
        upload_session_id: Optional upload session ID
        uploaded_image_id: Optional uploaded image ID

    Returns:
        attempt_id on success, None on failure
    """
    # Extract key fields from analysis result
    is_correct = None
    error_type = None
    summary = None

    if analysis_result:
        parts = analysis_result.get("parts", [])
        if parts:
            # Use first part's results as primary
            first_part = parts[0]
            is_correct = first_part.get("is_correct")
            error_type = first_part.get("error_type")

        summary = analysis_result.get("overall_summary", "")

    attempt = AttemptRecord(
        user_id=user_id,
        workspace_id=workspace_id,
        question_id=question_id,
        source="handwritten_upload",
        is_correct=is_correct,
        error_type=error_type,
        analysis_summary=summary,
        analysis_data=analysis_result,
        upload_session_id=upload_session_id,
        uploaded_image_id=uploaded_image_id,
    )

    return record_attempt(attempt)


def get_recent_attempts(
    workspace_id: str,
    limit: int = 20,
    question_id: Optional[str] = None,
) -> list[dict]:
    """
    Get recent attempts for a workspace.

    Args:
        workspace_id: The workspace ID
        limit: Max number of attempts to return
        question_id: Optional filter by question

    Returns:
        List of attempt records (most recent first)
    """
    client = _get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("attempt_history").select("*").eq(
            "workspace_id", workspace_id
        ).order("submitted_at", desc=True).limit(limit)

        if question_id:
            query = query.eq("question_id", question_id)

        result = query.execute()
        return result.data or []

    except Exception as e:
        print(f"[attempt_tracker] get_recent_attempts error: {e}")
        return []


def get_error_stats(workspace_id: str) -> dict:
    """
    Get error type statistics for a workspace.

    Returns:
        {"concept": 5, "algebra": 3, ...}
    """
    client = _get_supabase_client()
    if not client:
        return {}

    try:
        result = client.table("attempt_history").select(
            "error_type"
        ).eq("workspace_id", workspace_id).eq(
            "is_correct", False
        ).not_.is_("error_type", "null").execute()

        stats = {}
        for row in result.data or []:
            et = row.get("error_type")
            if et:
                stats[et] = stats.get(et, 0) + 1

        return stats

    except Exception as e:
        print(f"[attempt_tracker] get_error_stats error: {e}")
        return {}
