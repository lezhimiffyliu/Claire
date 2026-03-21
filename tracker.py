"""
Lightweight Supabase usage tracker for Claire.

All calls are fire-and-forget — failures are silently ignored so they
never break the main app. If SUPABASE_URL / SUPABASE_KEY are not set
in st.secrets (or env), tracking is simply skipped.
"""

from __future__ import annotations

import os
from typing import Any

_client = None
_init_attempted = False


def _get_client():
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True
    try:
        url = key = ""
        try:
            import streamlit as st
            url = st.secrets.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
        # Fallback to env vars (local dev)
        url = url or os.getenv("SUPABASE_URL", "")
        key = key or os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            return None
        from supabase import create_client
        _client = create_client(url, key)
    except Exception:
        pass
    return _client


def track(session_id: str, event_type: str, data: dict[str, Any] | None = None) -> None:
    """Log a usage event to Supabase. Silent on any failure."""
    try:
        client = _get_client()
        if client is None:
            return
        client.table("usage_events").insert({
            "session_id": session_id,
            "event_type": event_type,
            "data": data or {},
        }).execute()
    except Exception:
        pass


def track_feedback(session_id: str, feedback_text: str, rating: str | None = None) -> None:
    """Log user feedback."""
    track(session_id, "feedback", {"text": feedback_text[:1000], "rating": rating})
