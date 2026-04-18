"""
Session State Management for Teaching Modes

Defines explicit teaching modes and agent actions to prevent
the agent from free-wheeling when teaching rules are clear.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TeachingMode(str, Enum):
    """Explicit teaching session modes."""
    SOLVE_NEW_PROBLEM = "solve_new_problem"  # Student asks a new problem
    GRADE_UPLOADED_ATTEMPT = "grade_uploaded_attempt"  # Just graded handwritten work
    CONTINUE_TEACHING = "continue_teaching"  # Ongoing Socratic dialogue
    FULL_SOLUTION = "full_solution"  # Student requested complete solution


class AgentAction(str, Enum):
    """Structured actions the agent can take."""
    CONFIRM_CORRECT_AND_STOP = "confirm_correct_and_stop"  # Answer is correct, acknowledge and end
    GIVE_HINT = "give_hint"  # Provide a hint for next step
    GIVE_FEEDBACK = "give_feedback"  # Explain what went wrong
    ASK_CLARIFICATION = "ask_clarification"  # Ask student to clarify/explain
    SHOW_FULL_SOLUTION = "show_full_solution"  # Provide complete worked solution


@dataclass
class TeachingDecision:
    """Structured decision from the agent."""
    action: AgentAction
    message: str  # What to show the student
    reasoning: str  # Why this action was chosen (for debugging)
    confidence: float = 1.0  # How confident the agent is (0-1)


@dataclass
class TeachingContext:
    """
    Complete context for a teaching session.

    This bundles all the information needed to make teaching decisions
    and enforce rules based on verifier results.
    """
    # Problem info
    problem_id: str
    problem_stem: str
    question_text: str
    official_answer: Optional[str]
    topic: str
    concepts: list[str]

    # Student's work
    student_answer: Optional[str]
    student_steps: list[str]

    # Verifier result (GROUND TRUTH)
    is_correct: bool  # From verifier, NOT from LLM guess
    is_uncertain: bool  # True if verifier couldn't determine
    verifier_result: Optional[dict]

    # Error analysis (from vision LLM, NOT authoritative)
    error_type: Optional[str]  # concept|algebra|logic|careless
    error_candidates: list[dict]  # Suspected error locations
    feedback: str  # Initial feedback from vision analysis
    hint: str  # Initial hint from vision analysis
    confidence: float  # Vision model's confidence in extraction

    # Session state
    mode: TeachingMode
    conversation_history: list[dict]  # Previous messages in this session


def get_teaching_mode_description(mode: TeachingMode) -> str:
    """Get human-readable description of a teaching mode."""
    descriptions = {
        TeachingMode.SOLVE_NEW_PROBLEM: "Guiding student through a new problem",
        TeachingMode.GRADE_UPLOADED_ATTEMPT: "Analyzing uploaded handwritten work",
        TeachingMode.CONTINUE_TEACHING: "Continuing Socratic dialogue",
        TeachingMode.FULL_SOLUTION: "Providing complete solution (requested by student)",
    }
    return descriptions.get(mode, str(mode))


def get_action_description(action: AgentAction) -> str:
    """Get human-readable description of an agent action."""
    descriptions = {
        AgentAction.CONFIRM_CORRECT_AND_STOP: "Confirm correct answer and stop teaching",
        AgentAction.GIVE_HINT: "Provide hint for next step",
        AgentAction.GIVE_FEEDBACK: "Explain the error",
        AgentAction.ASK_CLARIFICATION: "Ask student to clarify their thinking",
        AgentAction.SHOW_FULL_SOLUTION: "Show complete worked solution",
    }
    return descriptions.get(action, str(action))
