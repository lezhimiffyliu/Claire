"""
Tests for api.py - Rate limiting and endpoint behavior.
"""

import sys
import os
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test database path before importing api
TEST_DB_PATH = Path(__file__).parent / "test_usage.db"


class TestRateLimiting:
    """Test the rate limiting logic."""

    def setup_method(self):
        """Create fresh test database before each test."""
        # Remove old test db if exists
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def teardown_method(self):
        """Clean up test database after each test."""
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def test_database_creates_table(self):
        """Test that init_db creates the usage table."""
        import api
        api.DB_PATH = TEST_DB_PATH
        api.init_db()

        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='usage'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_usage_increments(self):
        """Test that check_and_increment_usage increments count."""
        import api
        api.DB_PATH = TEST_DB_PATH
        api.init_db()

        result1 = api.check_and_increment_usage("test_user")
        assert result1["allowed"] is True
        assert result1["used"] == 1

        result2 = api.check_and_increment_usage("test_user")
        assert result2["allowed"] is True
        assert result2["used"] == 2

    def test_rate_limit_enforced(self):
        """Test that rate limit blocks after DAILY_LIMIT."""
        import api
        api.DB_PATH = TEST_DB_PATH
        api.DAILY_LIMIT = 3  # Set low limit for testing
        api.init_db()

        # Use up the limit
        for i in range(3):
            result = api.check_and_increment_usage("test_user")
            assert result["allowed"] is True

        # Next request should be blocked
        result = api.check_and_increment_usage("test_user")
        assert result["allowed"] is False
        assert result["used"] == 3

    def test_different_users_separate_limits(self):
        """Test that different users have separate limits."""
        import api
        api.DB_PATH = TEST_DB_PATH
        api.DAILY_LIMIT = 2
        api.init_db()

        # User A uses their limit
        api.check_and_increment_usage("user_a")
        api.check_and_increment_usage("user_a")
        result_a = api.check_and_increment_usage("user_a")
        assert result_a["allowed"] is False

        # User B should still have full limit
        result_b = api.check_and_increment_usage("user_b")
        assert result_b["allowed"] is True
        assert result_b["used"] == 1


class TestUserIdExtraction:
    """Test user ID extraction from requests."""

    def test_uuid_header_priority(self):
        """Test that X-User-ID header takes priority."""
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        import api
        api.DB_PATH = TEST_DB_PATH
        api.init_db()

        # Create mock request
        mock_request = MagicMock()
        mock_request.headers = {"X-User-ID": "abc123"}
        mock_request.client.host = "192.168.1.1"

        user_id = api.get_user_id(mock_request)
        assert user_id == "uuid:abc123"

    def test_forwarded_ip_used(self):
        """Test that X-Forwarded-For is used when no UUID."""
        from unittest.mock import MagicMock

        import api

        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"}
        mock_request.client.host = "127.0.0.1"

        user_id = api.get_user_id(mock_request)
        assert user_id == "ip:203.0.113.1"

    def test_fallback_to_client_ip(self):
        """Test fallback to client IP when no headers."""
        from unittest.mock import MagicMock

        import api

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.100"

        user_id = api.get_user_id(mock_request)
        assert user_id == "ip:192.168.1.100"
