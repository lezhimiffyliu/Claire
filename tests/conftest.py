"""
Shared test fixtures for Claire tests.
"""

import pytest
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_agent():
    """
    Create a ClaireAgent without initializing the LLM.
    Useful for testing system commands and state management.
    """
    from claire_agent_old import ClaireAgent

    # Temporarily remove API key to avoid LLM initialization
    original_key = os.environ.pop("ANTHROPIC_API_KEY", None)

    agent = ClaireAgent()

    # Restore API key if it existed
    if original_key:
        os.environ["ANTHROPIC_API_KEY"] = original_key

    return agent
