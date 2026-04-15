"""
Google OAuth via Supabase Auth for Claire (Streamlit).

Flow:
1. User clicks "Sign in with Google" → redirected to Google
2. Google redirects back to app with ?code=...
3. App exchanges code for session → user is logged in
"""

from __future__ import annotations
import streamlit as st
import os

# Load .env file
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

_supabase = None


def _client():
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client

            # Try st.secrets first, then environment variables
            url = None
            key = None

            try:
                url = st.secrets.get("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_KEY")
            except Exception:
                pass

            # Fallback to environment variables
            if not url:
                url = os.environ.get("SUPABASE_URL")
            if not key:
                key = os.environ.get("SUPABASE_KEY")

            # Debug
            print(f"[AUTH DEBUG] url={url[:30] if url else None}... key={key[:20] if key else None}...")

            if not url or not key:
                return None

            _supabase = create_client(url, key)
        except Exception as e:
            print(f"[AUTH DEBUG] Exception: {e}")
            return None
    return _supabase


def get_authenticated_client():
    """
    Get Supabase client with current user's session.
    This is needed for RLS to work properly.
    """
    client = _client()
    if not client:
        return None

    # Get stored session
    session = st.session_state.get("supabase_session")
    if session:
        try:
            # Set the session on the client
            client.auth.set_session(session.access_token, session.refresh_token)
        except Exception as e:
            print(f"[AUTH DEBUG] Failed to set session: {e}")

    return client


def handle_oauth_callback() -> bool:
    """Call once at the top of app.py. Returns True if a login just happened."""
    params = st.query_params
    if "code" not in params or "user" in st.session_state:
        return False
    client = _client()
    if not client:
        return False
    try:
        resp = client.auth.exchange_code_for_session({"auth_code": params["code"]})
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
    client = _client()
    if not client:
        # Show warning that auth isn't configured
        st.caption("⚠️ Auth not configured (missing SUPABASE_URL/KEY)")
        return

    try:
        redirect = st.secrets.get("APP_URL", None)
    except Exception:
        redirect = None
    if not redirect:
        redirect = os.environ.get("APP_URL", "http://localhost:8501")

    try:
        resp = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect},
        })
        st.link_button("🔑 " + label, resp.url, use_container_width=True)
    except Exception as e:
        st.caption(f"⚠️ OAuth error: {e}")


def sign_out():
    try:
        _client().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("user", None)
    st.session_state.pop("supabase_session", None)
