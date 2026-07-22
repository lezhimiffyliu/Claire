"""
claire_core.tools — LangChain tools exposed to the tutor agent loop.

These wrap the existing pure-Python assets (the SymPy verifier, the heuristic
templates) as LangChain `@tool`s so the agent can call them inside its ReAct
loop. The verifier is ALSO run deterministically outside the agent (see
loop.py) as ground truth — exposing it as a tool just lets the agent reason
about intermediate checks during Socratic dialogue.
"""
from __future__ import annotations

import logging

from langchain_core.tools import tool

from verifier import verify_answer

from .state import EvidenceRecord, Problem, ToolName, ToolRequest

logger = logging.getLogger(__name__)

# Keep persisted tool findings short — we store a summary, never raw output.
_RESULT_SUMMARY_CAP = 300


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


# --------------------------------------------------------------------------- #
# Deterministic dispatcher for the teaching-turn tool loop.
#
# The multi-turn teaching path (loop.run_teaching_turn) does NOT use the ReAct
# `chat()` loop. Instead the agent emits a strict `ToolRequest`, and this pure
# function runs the corresponding underlying implementation and normalizes the
# outcome into a short, structured `EvidenceRecord`. No LLM summarization, no raw
# scratchpad — the record is the only tool output that is ever persisted.
# --------------------------------------------------------------------------- #
def _clip(text: str, cap: int = _RESULT_SUMMARY_CAP) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= cap else text[: cap - 1].rstrip() + "…"


def run_tool(req: ToolRequest, problem: Problem, turn: int) -> EvidenceRecord:
    """Execute one requested tool and return a short structured evidence record.

    Never raises for tool-internal failures — a failed tool becomes an evidence
    record whose result explains the miss, so the second agent call can adapt.
    """
    try:
        if req.tool == ToolName.VERIFY_STEP:
            expected = (req.expected or "").strip()
            result = verify_answer(
                student_answer=req.expression or "",
                official_answer=expected,
                problem_context=problem.text or None,
            )
            if result.is_uncertain:
                verdict = "UNCERTAIN"
            else:
                verdict = "CORRECT" if result.is_correct else "INCORRECT"
            return EvidenceRecord(
                tool=req.tool,
                input=_clip(f"{req.expression} =? {expected}" if expected else f"{req.expression}"),
                result=_clip(f"{verdict}: {result.reason}"),
                turn=turn,
            )

        if req.tool == ToolName.LOOKUP_HEURISTIC:
            from pattern_tools import get_heuristic

            # get_heuristic is a LangChain @tool; call its underlying function.
            _fn = getattr(get_heuristic, "func", get_heuristic)
            text = _fn(req.pattern) or ""
            summary = text or f"No heuristic template for pattern '{req.pattern}'."
            return EvidenceRecord(
                tool=req.tool,
                input=_clip(req.pattern or ""),
                result=_clip(summary),
                turn=turn,
            )

        # RETRIEVE_EXAMPLE
        from .problem_retrieval import retrieve_examples

        # Pull a few, then drop the student's CURRENT problem — returning it would
        # leak its own answer under the guise of a "similar" example.
        candidates = retrieve_examples(
            req.topic or "", req.error_type or None, course=problem.course, limit=4
        )
        records = [
            r for r in candidates
            if str(r.get("id", "")).split(":", 1)[0] != problem.id
        ][:1]
        if not records:
            summary = f"No worked example found for topic '{req.topic}'."
        else:
            r = records[0]
            summary = f"{r['source']}: Q: {r['question_text']} A: {r['final_answer'] or '(no answer)'}"
        return EvidenceRecord(
            tool=req.tool,
            input=_clip(f"{req.topic}" + (f" / {req.error_type}" if req.error_type else "")),
            result=_clip(summary),
            turn=turn,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("run_tool(%s) failed: %s", req.tool.value, exc)
        return EvidenceRecord(
            tool=req.tool,
            input=_clip(str(req.model_dump(exclude_none=True))),
            result=f"tool unavailable ({type(exc).__name__})",
            turn=turn,
        )
