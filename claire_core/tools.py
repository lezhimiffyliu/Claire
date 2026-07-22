"""
claire_core.tools — LangChain tools exposed to the tutor agent loop.

These wrap the existing pure-Python assets (the SymPy verifier, the heuristic
templates) as LangChain `@tool`s so the agent can call them inside its ReAct
loop. The verifier is ALSO run deterministically outside the agent (see
loop.py) as ground truth — exposing it as a tool just lets the agent reason
about intermediate checks during Socratic dialogue.
"""
from __future__ import annotations

from langchain_core.tools import tool

from verifier import verify_answer


@tool
def verify_answer_tool(
    student_answer: str,
    official_answer: str,
    problem_context: str = "",
) -> str:
    """Check whether a student's math answer is equivalent to the official answer.

    Use this to confirm intermediate results during a Socratic dialogue. Returns
    a short status string. Do NOT reveal the official answer to the student.

    Args:
        student_answer: The student's expression, e.g. "3*x**2".
        official_answer: The known-correct expression, e.g. "3x^2".
        problem_context: The problem text, to help pick the right check.
    """
    result = verify_answer(
        student_answer=student_answer,
        official_answer=official_answer,
        problem_context=problem_context or None,
    )
    if result.is_uncertain:
        return f"UNCERTAIN ({result.verifier_type}): {result.reason}"
    verdict = "CORRECT" if result.is_correct else "INCORRECT"
    return f"{verdict} ({result.verifier_type}, confidence={result.confidence:.2f}): {result.reason}"


@tool
def lookup_heuristic_tool(pattern: str) -> str:
    """Look up the solving template / key formulas for a problem pattern.

    Args:
        pattern: A pattern name such as "optimization", "chain_rule",
            "u_substitution", "related_rates", "limits".
    """
    try:
        from pattern_tools import get_heuristic  # lazy: keeps import graph light

        text = get_heuristic(pattern)
        return text or f"No heuristic template found for pattern '{pattern}'."
    except Exception as exc:  # pragma: no cover - defensive
        return f"Heuristic lookup unavailable ({exc})."


from .problem_retrieval import retrieve_teaching_example

TUTOR_TOOLS = [verify_answer_tool, lookup_heuristic_tool, retrieve_teaching_example]
