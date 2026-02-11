"""
Tests for claire_agent.py - System commands and state management.

Focus: Test OUR code (command handling, state), not LangChain/Claude.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSystemCommands:
    """Test system command handling."""

    def test_help_command(self, mock_agent):
        """Test that 'help' command returns help text."""
        result = mock_agent.process_query("help")
        assert "Help Commands" in result["output"]
        assert "intermediate_steps" in result
        assert result["intermediate_steps"] == []  # System commands have no steps

    def test_examples_command(self, mock_agent):
        """Test that 'examples' command returns example questions."""
        result = mock_agent.process_query("examples")
        assert "Example Questions" in result["output"]
        assert "Derivatives" in result["output"]
        assert "Integrals" in result["output"]

    def test_capabilities_command(self, mock_agent):
        """Test that 'capabilities' command shows available tools."""
        result = mock_agent.process_query("capabilities")
        output = result["output"]
        # Without API key, should show tools list or warning
        assert "calculate_derivative" in output or "Agent" in output

    def test_status_command(self, mock_agent):
        """Test that 'status' command shows system status."""
        result = mock_agent.process_query("status")
        output = result["output"]
        assert "Status" in output
        assert "beginner" in output.lower()  # Default level

    def test_clear_command_clears_history(self, mock_agent):
        """Test that 'clear' command clears conversation history."""
        # Add some history first
        mock_agent.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]

        result = mock_agent.process_query("clear")

        assert "cleared" in result["output"].lower()
        # After clear, history should only have the clear command itself
        assert mock_agent.conversation_history[0]["content"] == "clear"

    def test_reset_command_resets_all_state(self, mock_agent):
        """Test that 'reset' command resets agent state."""
        # Modify state
        mock_agent.user_level = "advanced"
        mock_agent.guided_mode = False
        mock_agent.conversation_history = [{"role": "user", "content": "old"}]

        result = mock_agent.process_query("reset")

        assert "reset" in result["output"].lower()
        assert mock_agent.user_level == "beginner"
        assert mock_agent.guided_mode is True


class TestLevelManagement:
    """Test student level management."""

    def test_set_level_beginner(self, mock_agent):
        """Test setting level to beginner."""
        mock_agent.user_level = "advanced"  # Start from different level
        result = mock_agent.process_query("level beginner")

        assert mock_agent.user_level == "beginner"
        assert "beginner" in result["output"].lower()

    def test_set_level_intermediate(self, mock_agent):
        """Test setting level to intermediate."""
        result = mock_agent.process_query("level intermediate")

        assert mock_agent.user_level == "intermediate"
        assert "intermediate" in result["output"].lower()

    def test_set_level_advanced(self, mock_agent):
        """Test setting level to advanced."""
        result = mock_agent.process_query("level advanced")

        assert mock_agent.user_level == "advanced"
        assert "advanced" in result["output"].lower()

    def test_set_level_invalid_rejected(self, mock_agent):
        """Test that invalid level is rejected and state unchanged."""
        mock_agent.user_level = "beginner"
        result = mock_agent.process_query("level expert")

        assert mock_agent.user_level == "beginner"  # Unchanged
        assert "invalid" in result["output"].lower()


class TestGuidedMode:
    """Test guided learning mode toggle."""

    def test_toggle_guided_mode_on_to_off(self, mock_agent):
        """Test toggling guided mode from ON to OFF."""
        mock_agent.guided_mode = True
        result = mock_agent.process_query("/study")

        assert mock_agent.guided_mode is False
        assert "OFF" in result["output"]

    def test_toggle_guided_mode_off_to_on(self, mock_agent):
        """Test toggling guided mode from OFF to ON."""
        mock_agent.guided_mode = False
        result = mock_agent.process_query("/study")

        assert mock_agent.guided_mode is True
        assert "ON" in result["output"]
        assert "Socratic" in result["output"]  # Should mention teaching method


class TestConversationHistory:
    """Test conversation history management."""

    def test_history_grows_on_command(self, mock_agent):
        """Test that conversation history is updated after processing."""
        mock_agent.conversation_history = []
        mock_agent.process_query("help")

        # Should have added user message and assistant response
        assert len(mock_agent.conversation_history) == 2
        assert mock_agent.conversation_history[0]["role"] == "user"
        assert mock_agent.conversation_history[1]["role"] == "assistant"

    def test_history_records_correct_content(self, mock_agent):
        """Test that user message is recorded correctly in history."""
        mock_agent.conversation_history = []
        mock_agent.process_query("examples")

        assert mock_agent.conversation_history[0]["content"] == "examples"
        assert "Example" in mock_agent.conversation_history[1]["content"]


class TestAgentInitialization:
    """Test agent initialization behavior."""

    def test_default_level_is_beginner(self, mock_agent):
        """Test that default level is beginner."""
        assert mock_agent.user_level == "beginner"

    def test_default_guided_mode_is_on(self, mock_agent):
        """Test that guided mode is on by default."""
        assert mock_agent.guided_mode is True

    def test_conversation_history_starts_empty(self):
        """Test that conversation history starts empty on fresh agent."""
        # Create fresh agent without using fixture
        from claire_agent import ClaireAgent
        original_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        fresh_agent = ClaireAgent()
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key

        assert len(fresh_agent.conversation_history) == 0

    def test_executor_none_without_api_key(self):
        """Test that executor is None when API key is missing."""
        from claire_agent import ClaireAgent
        original_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        agent = ClaireAgent()
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key

        assert agent.executor is None


class TestProcessQueryReturnFormat:
    """Test the return format of process_query."""

    def test_return_has_required_keys(self, mock_agent):
        """Test that process_query returns dict with required keys."""
        result = mock_agent.process_query("help")

        assert isinstance(result, dict)
        assert "output" in result
        assert "intermediate_steps" in result

    def test_output_is_string(self, mock_agent):
        """Test that output is a string."""
        result = mock_agent.process_query("status")
        assert isinstance(result["output"], str)

    def test_intermediate_steps_is_list(self, mock_agent):
        """Test that intermediate_steps is a list."""
        result = mock_agent.process_query("examples")
        assert isinstance(result["intermediate_steps"], list)
