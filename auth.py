"""
Google OAuth via Supabase Auth for Claire (Streamlit).

Flow:
1. User clicks "Sign in with Google" → redirected to Google
2. Google redirects back to app with ?code=...
3. App exchanges code for session → user is logged in
4. Session tokens stored in encrypted browser cookies for persistence
5. On page refresh, session automatically restored from cookies
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
_cookies = None


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


def get_cookie_manager():
    """Get or create encrypted cookie manager singleton."""
    global _cookies
    if _cookies is None:
        try:
            from streamlit_cookies_manager import EncryptedCookieManager

            # Get encryption password from env
            password = os.environ.get("COOKIE_PASSWORD", "default-insecure-password")

            _cookies = EncryptedCookieManager(
                prefix="claire_auth_",
                password=password
            )

        except ImportError:
            print("[AUTH DEBUG] streamlit-cookies-manager not installed")
            return None
        except Exception as e:
            print(f"[AUTH DEBUG] Cookie manager error: {e}")
            return None

    # Check if ready (JavaScript loaded)
    if _cookies and not _cookies.ready():
        # Wait for cookies to be ready
        st.stop()

    return _cookies


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
        if resp.user and resp.session:
            # Save to session_state
            st.session_state.user = resp.user
            st.session_state.supabase_session = resp.session

            # 🆕 Save to encrypted cookies for persistence across page refreshes
            cookies = get_cookie_manager()
            if cookies:
                try:
                    cookies["access_token"] = resp.session.access_token
                    cookies["refresh_token"] = resp.session.refresh_token
                    cookies["user_id"] = str(resp.user.id)
                    cookies["user_email"] = resp.user.email
                    cookies.save()
                    print(f"[AUTH DEBUG] Saved session to cookies for user {resp.user.email}")
                except Exception as e:
                    print(f"[AUTH DEBUG] Failed to save cookies: {e}")

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


def restore_session_from_cookie() -> bool:
    """
    🆕 Restore user session from encrypted cookies.
    Call this at app startup BEFORE handle_oauth_callback().
    Returns True if session was successfully restored.
    """
    # Skip if already logged in
    if "user" in st.session_state:
        print("[AUTH DEBUG] Already logged in via session_state")
        return True

    try:
        cookies = get_cookie_manager()
    except Exception as e:
        print(f"[AUTH DEBUG] Cookie manager initialization error: {e}")
        return False

    if not cookies:
        print("[AUTH DEBUG] Cookie manager not available")
        return False

    # Get tokens from cookies
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")
    user_id = cookies.get("user_id")
    user_email = cookies.get("user_email")

    if not (access_token and refresh_token and user_id):
        print("[AUTH DEBUG] No valid session in cookies")
        return False

    client = _client()
    if not client:
        print("[AUTH DEBUG] Supabase client not available")
        return False

    try:
        # Restore session using tokens
        print(f"[AUTH DEBUG] Attempting to restore session for {user_email}")
        resp = client.auth.set_session(access_token, refresh_token)

        if resp.user:
            # Successfully restored!
            st.session_state.user = resp.user
            st.session_state.supabase_session = resp.session

            # Update cookies with refreshed tokens
            try:
                cookies["access_token"] = resp.session.access_token
                cookies["refresh_token"] = resp.session.refresh_token
                cookies.save()
                print(f"[AUTH DEBUG] ✅ Session restored for {resp.user.email}")
            except Exception as e:
                print(f"[AUTH DEBUG] Failed to update cookies: {e}")

            return True
        else:
            print("[AUTH DEBUG] set_session returned no user")

    except Exception as e:
        print(f"[AUTH DEBUG] Session restore failed: {e}")
        # Token expired or invalid - clear cookies
        try:
            for key in ["access_token", "refresh_token", "user_id", "user_email"]:
                if key in cookies:
                    del cookies[key]
            cookies.save()
            print("[AUTH DEBUG] Cleared invalid cookies")
        except Exception as clear_error:
            print(f"[AUTH DEBUG] Failed to clear cookies: {clear_error}")

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
    """Sign out and clear both session_state and cookies."""
    try:
        _client().auth.sign_out()
    except Exception:
        pass

    # Clear session_state
    st.session_state.pop("user", None)
    st.session_state.pop("supabase_session", None)
    st.session_state.pop("workspace_context", None)

    # 🆕 Clear cookies
    cookies = get_cookie_manager()
    if cookies:
        try:
            for key in ["access_token", "refresh_token", "user_id", "user_email"]:
                if key in cookies:
                    del cookies[key]
            cookies.save()
            print("[AUTH DEBUG] Cleared cookies on sign out")
        except Exception as e:
            print(f"[AUTH DEBUG] Failed to clear cookies: {e}")
