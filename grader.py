"""
Grader - VLM image parsing + LLM solution grading.
"""

import base64
import json
from dataclasses import dataclass
from typing import Optional

from claire_agent_old import get_secret


@dataclass
class GradingResult:
    """Result of grading a student's solution."""
    error_step: Optional[int]  # 0-indexed step where error occurred (None if correct)
    error_type: Optional[str]  # concept | algebra | logic | careless
    feedback: str              # Explanation of the error
    hint: str                  # Hint for next step
    is_correct: bool


@dataclass
class ParsedSolution:
    """Parsed student work from image."""
    steps: list[str]
    final_answer: Optional[str]
    raw_text: str


def parse_image(image_bytes: bytes) -> ParsedSolution:
    """
    Use VLM to parse handwritten math from image.

    Args:
        image_bytes: Raw image bytes (PNG, JPG, etc.)

    Returns:
        ParsedSolution with extracted steps
    """
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return ParsedSolution(steps=[], final_answer=None, raw_text="[No API key]")

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage

        # Encode image as base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Detect image type from magic bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        else:
            media_type = "image/png"  # Default

        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0,
            max_tokens=1500,
        )

        prompt = """Analyze this handwritten math solution. Extract:

1. Each step the student wrote (in order)
2. The final answer (if visible)

Output JSON:
{
  "steps": ["step 1 text", "step 2 text", ...],
  "final_answer": "the final answer or null",
  "raw_text": "full transcription of all writing"
}

Rules:
- Convert math to LaTeX where appropriate
- Keep steps in the order written
- Include all work shown, even if messy
- If unclear, make best guess with [?] marker

Output ONLY valid JSON."""

        message = HumanMessage(
            content=[
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ]
        )

        result = llm.invoke([message])
        output = result.content.strip()

        # Extract JSON from response
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
        output = output.strip()

        data = json.loads(output)

        return ParsedSolution(
            steps=data.get("steps", []),
            final_answer=data.get("final_answer"),
            raw_text=data.get("raw_text", ""),
        )

    except Exception as e:
        print(f"[parse_image] Error: {e}")
        return ParsedSolution(steps=[], final_answer=None, raw_text=f"[Error: {e}]")


def grade_solution(parsed: ParsedSolution, problem: dict, diagram_url: Optional[str] = None) -> GradingResult:
    """
    Compare student solution to correct solution.

    Args:
        parsed: ParsedSolution from parse_image()
        problem: Problem dict with solution_steps and final_answer
        diagram_url: Optional URL to problem diagram (for vision)

    Returns:
        GradingResult with feedback
    """
    import streamlit as st

    # Only use DeepSeek if user explicitly chose basic mode
    use_basic = st.session_state.get("use_basic_mode", False)

    if use_basic:
        api_key = get_secret("DEEPSEEK_API_KEY")
        if api_key:
            return _grade_with_deepseek(parsed, problem, api_key)
        # Fall through to Claude if no DeepSeek key

    # Use Claude (default)
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return GradingResult(
            error_step=None,
            error_type=None,
            feedback="Unable to grade - no API key",
            hint="",
            is_correct=False,
        )

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage

        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0,
            max_tokens=800,
        )

        prompt = f"""Compare student solution to correct solution.

PROBLEM:
{problem.get('question', '')}

CORRECT SOLUTION:
Steps: {json.dumps(problem.get('solution_steps', []))}
Final Answer: {problem.get('final_answer', '')}

STUDENT SOLUTION:
Steps: {json.dumps(parsed.steps)}
Final Answer: {parsed.final_answer}

Analyze and output JSON:
{{
  "is_correct": true/false,
  "error_step": null or 0-indexed step number where first error occurs,
  "error_type": null or "concept" | "algebra" | "logic" | "careless",
  "feedback": "explanation of the error or 'Correct!' if right",
  "hint": "hint for fixing/continuing (empty if correct)"
}}

Error types:
- concept: Wrong formula or approach
- algebra: Arithmetic/algebraic mistake
- logic: Wrong reasoning or setup
- careless: Minor slip (sign error, forgot term)

Output ONLY valid JSON."""

        # Build message content - include diagram if available
        content = []
        if diagram_url:
            content.append({
                "type": "image",
                "source": {"type": "url", "url": diagram_url},
            })
        content.append({"type": "text", "text": prompt})

        result = llm.invoke([HumanMessage(content=content)])
        output = result.content.strip()

        # Extract JSON
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
        output = output.strip()

        data = json.loads(output)

        return GradingResult(
            error_step=data.get("error_step"),
            error_type=data.get("error_type"),
            feedback=data.get("feedback", ""),
            hint=data.get("hint", ""),
            is_correct=data.get("is_correct", False),
        )

    except Exception as e:
        print(f"[grade_solution] Error: {e}")
        return GradingResult(
            error_step=None,
            error_type=None,
            feedback=f"Grading error: {e}",
            hint="",
            is_correct=False,
        )


def _grade_with_deepseek(parsed: ParsedSolution, problem: dict, api_key: str) -> GradingResult:
    """Fallback grading with DeepSeek (no vision, text only)."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0,
            max_tokens=800,
        )

        prompt = f"""Compare student solution to correct solution.

PROBLEM:
{problem.get('question', '')}

CORRECT SOLUTION:
Steps: {json.dumps(problem.get('solution_steps', []))}
Final Answer: {problem.get('final_answer', '')}

STUDENT SOLUTION:
Steps: {json.dumps(parsed.steps)}
Final Answer: {parsed.final_answer}

Output JSON:
{{
  "is_correct": true/false,
  "error_step": null or step number (0-indexed),
  "error_type": null or "concept" | "algebra" | "logic" | "careless",
  "feedback": "explanation",
  "hint": "next step hint"
}}

Output ONLY valid JSON."""

        result = llm.invoke([HumanMessage(content=prompt)])
        output = result.content.strip()

        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
        output = output.strip()

        data = json.loads(output)

        return GradingResult(
            error_step=data.get("error_step"),
            error_type=data.get("error_type"),
            feedback=data.get("feedback", ""),
            hint=data.get("hint", ""),
            is_correct=data.get("is_correct", False),
        )

    except Exception as e:
        print(f"[_grade_with_deepseek] Error: {e}")
        return GradingResult(
            error_step=None,
            error_type=None,
            feedback=f"Grading error: {e}",
            hint="",
            is_correct=False,
        )
