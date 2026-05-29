"""
Test script to verify auth persistence with cookies.

Run this after implementing cookie-based auth to verify:
1. Login → cookies saved
2. Refresh → session restored from cookies
3. Logout → cookies cleared
"""

import os
from pathlib import Path

# Load .env
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def test_cookie_manager():
    """Test that cookie manager can be initialized."""
    try:
        from streamlit_cookies_manager import EncryptedCookieManager

        password = os.environ.get("COOKIE_PASSWORD", "test-password")
        cookies = EncryptedCookieManager(prefix="test_", password=password)

        print("✅ Cookie manager initialized successfully")
        return True
    except ImportError:
        print("❌ streamlit-cookies-manager not installed")
        print("   Run: pip install streamlit-cookies-manager")
        return False
    except Exception as e:
        print(f"❌ Cookie manager error: {e}")
        return False

def test_env_variables():
    """Test that required environment variables are set."""
    required = ["SUPABASE_URL", "SUPABASE_KEY", "COOKIE_PASSWORD"]
    missing = []

    for var in required:
        value = os.environ.get(var)
        if not value:
            missing.append(var)
        else:
            print(f"✅ {var}: {value[:20]}...")

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False

    return True

def main():
    print("=" * 60)
    print("Testing Auth Persistence Setup")
    print("=" * 60)
    print()

    print("1. Checking environment variables...")
    env_ok = test_env_variables()
    print()

    print("2. Testing cookie manager...")
    cookie_ok = test_cookie_manager()
    print()

    print("=" * 60)
    if env_ok and cookie_ok:
        print("✅ All checks passed!")
        print()
        print("Next steps:")
        print("1. Run: streamlit run app.py")
        print("2. Sign in with Google")
        print("3. Refresh the page (Cmd+R or Ctrl+R)")
        print("4. You should remain logged in!")
    else:
        print("❌ Some checks failed. Fix issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
