"""
Usage quota tracking for Claire.

Anonymous users: localStorage + session (3 free queries)
Logged-in users: Supabase user_id tracking (5 free premium queries/day)
"""

from __future__ import annotations
from datetime import datetime, timezone
import streamlit as st

# Limits
ANON_FREE_QUERIES = 3       # Anonymous users get 3 total
USER_FREE_PREMIUM = 5       # Logged-in users get 5 premium/day

_supabase = None


def _client():
    """Get Supabase client (lazy init)."""
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client
            _supabase = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"],
            )
        except Exception:
            return None
    return _supabase


def get_user_id() -> str | None:
    """Get current user's ID if logged in."""
    user = st.session_state.get("user")
    if user:
        return user.id
    return None


def _today_key() -> str:
    """Get today's date string for daily reset."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ────────────────────────────────────────────────────────────
# Anonymous user quota (localStorage-backed)
# ────────────────────────────────────────────────────────────

def inject_localstorage_sync():
    """
    Inject JavaScript to sync localStorage query count to a hidden div.
    Call this once at the top of the app.
    """
    import streamlit.components.v1 as components

    # JavaScript to read localStorage and write to a data attribute
    components.html("""
    <div id="claire-quota-data"
         data-count="0"
         data-synced="false"
         style="display:none;">
    </div>
    <script>
    (function() {
        const KEY = 'claire_anon_queries';
        const stored = localStorage.getItem(KEY);
        const count = stored ? parseInt(stored, 10) : 0;

        // Write to hidden div for Streamlit to read
        const el = document.getElementById('claire-quota-data');
        if (el) {
            el.setAttribute('data-count', count);
            el.setAttribute('data-synced', 'true');
        }

        // Expose increment function globally
        window.claireIncrementQuota = function() {
            const current = parseInt(localStorage.getItem(KEY) || '0', 10);
            localStorage.setItem(KEY, current + 1);
            return current + 1;
        };
    })();
    </script>
    """, height=0)


def increment_anon_quota_js():
    """
    Return JavaScript snippet to increment localStorage quota.
    Inject this after a query is made.
    """
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        const KEY = 'claire_anon_queries';
        const current = parseInt(localStorage.getItem(KEY) || '0', 10);
        localStorage.setItem(KEY, current + 1);
    })();
    </script>
    """, height=0)


def get_anon_query_count() -> int:
    """
    Get anonymous user's query count from session.
    Since we can't directly read localStorage from Python,
    we track it in session and sync via JS on page load.
    """
    return st.session_state.get("anon_query_count", 0)


def increment_anon_count():
    """Increment anonymous query count in session + localStorage."""
    current = st.session_state.get("anon_query_count", 0)
    st.session_state.anon_query_count = current + 1
    # Also trigger JS to update localStorage
    increment_anon_quota_js()


def anon_can_query() -> bool:
    """Check if anonymous user can still make queries."""
    return get_anon_query_count() < ANON_FREE_QUERIES


def anon_queries_remaining() -> int:
    """Get remaining queries for anonymous user."""
    return max(0, ANON_FREE_QUERIES - get_anon_query_count())


# ────────────────────────────────────────────────────────────
# Logged-in user quota (Supabase-backed)
# ────────────────────────────────────────────────────────────

def _get_user_usage(user_id: str) -> dict:
    """
    Get user's usage from Supabase.
    Returns: {"premium_today": int, "last_date": str}
    """
    client = _client()
    if not client:
        return {"premium_today": 0, "last_date": _today_key()}

    try:
        resp = client.table("user_quota").select("*").eq("user_id", user_id).execute()
        if resp.data:
            row = resp.data[0]
            # Reset if it's a new day
            if row.get("last_date") != _today_key():
                return {"premium_today": 0, "last_date": _today_key()}
            return {
                "premium_today": row.get("premium_today", 0),
                "last_date": row.get("last_date", _today_key()),
            }
    except Exception as e:
        print(f"[quota] Error getting user usage: {e}")

    return {"premium_today": 0, "last_date": _today_key()}


def _set_user_usage(user_id: str, premium_today: int):
    """Update user's usage in Supabase."""
    client = _client()
    if not client:
        return

    try:
        client.table("user_quota").upsert({
            "user_id": user_id,
            "premium_today": premium_today,
            "last_date": _today_key(),
        }).execute()
    except Exception as e:
        print(f"[quota] Error setting user usage: {e}")


def get_user_premium_today(user_id: str) -> int:
    """Get how many premium queries user has made today."""
    usage = _get_user_usage(user_id)
    return usage["premium_today"]


def increment_user_premium(user_id: str):
    """Increment user's premium query count for today."""
    usage = _get_user_usage(user_id)
    new_count = usage["premium_today"] + 1
    _set_user_usage(user_id, new_count)
    return new_count


def user_can_use_premium(user_id: str) -> bool:
    """Check if user can still use premium model today."""
    return get_user_premium_today(user_id) < USER_FREE_PREMIUM


def user_premium_remaining(user_id: str) -> int:
    """Get remaining premium queries for user today."""
    return max(0, USER_FREE_PREMIUM - get_user_premium_today(user_id))


# ────────────────────────────────────────────────────────────
# Unified API
# ────────────────────────────────────────────────────────────

def can_use_premium() -> bool:
    """
    Check if current user (anon or logged in) can use premium model.
    """
    user_id = get_user_id()
    if user_id:
        return user_can_use_premium(user_id)
    else:
        return anon_can_query()


def record_query(used_premium: bool = True):
    """
    Record a query. Call after each successful query.
    """
    user_id = get_user_id()
    if user_id:
        if used_premium:
            increment_user_premium(user_id)
    else:
        increment_anon_count()


def get_quota_status() -> dict:
    """
    Get current quota status for display.
    Returns: {"is_logged_in": bool, "remaining": int, "limit": int, "used_premium": bool}
    """
    user_id = get_user_id()
    if user_id:
        remaining = user_premium_remaining(user_id)
        return {
            "is_logged_in": True,
            "remaining": remaining,
            "limit": USER_FREE_PREMIUM,
            "can_premium": remaining > 0,
        }
    else:
        remaining = anon_queries_remaining()
        return {
            "is_logged_in": False,
            "remaining": remaining,
            "limit": ANON_FREE_QUERIES,
            "can_premium": remaining > 0,
        }
