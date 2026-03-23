"""
Google OAuth via Supabase Auth for Claire (Streamlit).

Flow:
1. User clicks "Sign in with Google" → redirected to Google
2. Google redirects back to app with ?code=...
3. App exchanges code for session → user is logged in
"""

from __future__ import annotations
import streamlit as st

_supabase = None


def _client():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        _supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return _supabase


def handle_oauth_callback() -> bool:
    """Call once at the top of app.py. Returns True if a login just happened."""
    params = st.query_params
    if "code" not in params or "user" in st.session_state:
        return False
    try:
        resp = _client().auth.exchange_code_for_session({"auth_code": params["code"]})
        if resp.user:
            st.session_state.user = resp.user
            st.session_state.supabase_session = resp.session
            st.query_params.clear()
            return True
    except Exception as e:
        # PKCE error - code_verifier lost during redirect
        # Clear params so user can retry
        st.query_params.clear()
        if "code challenge" in str(e).lower() or "code verifier" in str(e).lower():
            st.warning("Login session expired. Please try signing in again.")
        else:
            st.error(f"Login failed: {e}")
    return False


def get_user():
    """Return the current user object, or None if not logged in."""
    return st.session_state.get("user")


def show_login_button(label: str = "Sign in with Google to upload materials"):
    """Render a Google OAuth button. Reads APP_URL from secrets for redirect."""
    redirect = st.secrets.get("APP_URL", "http://localhost:8501")
    try:
        resp = _client().auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect},
        })
        st.link_button("🔑 " + label, resp.url, use_container_width=True)
    except Exception as e:
        st.error(f"Auth setup error: {e}")


def sign_out():
    try:
        _client().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("user", None)
    st.session_state.pop("supabase_session", None)
