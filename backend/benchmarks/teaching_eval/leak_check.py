"""
benchmarks.teaching_eval.leak_check — did a tutor message give the answer away?

A "leak" is a tutor message that reveals the official final answer *before the
problem is resolved*, when the action is NOT `show_solution` (revealing during a
sanctioned full solution is legal). We reuse the SymPy comparator in
``benchmarks.evaluator`` as ground truth: extract candidate math expressions from
the message and test each for symbolic equivalence to the official answer.

Two detection paths, both conservative to avoid false positives that would
wrongly fail the hard leak gate:

  1. Literal path — a normalized substring match, used ONLY when the official
     answer carries a variable or operator (so short numerics like "9" don't
     match "step 9" / "x^9").
  2. Symbolic path — candidate expressions are pulled from the message (fenced
     math, right-hand sides of "=", and operator-bearing tokens) and each is
     compared to the official answer via ``evaluate``.

This is intentionally a *thin* detector: it catches a tutor that states the
answer, not every conceivable paraphrase. Its limits are documented; the
structural leak gate is defined against it.
"""
from __future__ import annotations

import re
from typing import Iterable, List, NamedTuple, Tuple, Union

from benchmarks.evaluator import evaluate, parse_expression

# Actions whose messages may legitimately contain the answer (or are post-
# resolution) and are therefore exempt from the leak check.
_EXEMPT_ACTIONS = {"show_solution", "confirm_correct", "end_problem"}


class TutorMessage(NamedTuple):
    """One tutor utterance tagged with the action that produced it."""

    action: str  # a TutorAction value, e.g. "give_hint"
    text: str


# Fenced math: $...$, \( ... \), or `...`.
_FENCE_RE = re.compile(r"\$([^$]+)\$|\\\(([^)]*)\\\)|`([^`]+)`")
# Right-hand side of an equality, up to sentence punctuation.
_RHS_RE = re.compile(r"=\s*([^.,;:!?\n]+)")
# Operator-bearing tokens like "3x^2", "2*x*cos(x**2)", "x**2".
_TOKEN_RE = re.compile(
    r"[0-9A-Za-z().]*(?:\^|\*\*|[*/+])[0-9A-Za-z().*/^+\-]*"
    r"|[0-9A-Za-z]+\([0-9A-Za-z().*/^+\-]*\)"
)
# Standalone number, and words that commonly precede a benign number.
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_FALSE_POS_CTX = re.compile(
    r"\b(step|problem|prob|q|question|part|page|pg|figure|fig|line|example|ex|"
    r"no|number|item|section|chapter)\.?\s*$",
    re.IGNORECASE,
)
# Below this magnitude a bare integer (0, 1) is too common in calculus prose
# ("n-1", "reduce by 1") to treat as a leak without more context.
_NUMERIC_LEAK_MIN_MAGNITUDE = 2.0


def _normalize(s: str) -> str:
    """Lowercase, drop whitespace, and unify power notation for substring compare."""
    return re.sub(r"\s+", "", s).replace("**", "^").lower()


def _has_symbol_or_op(s: str) -> bool:
    has_alpha = any(c.isalpha() for c in s)
    has_op = any(c in s for c in "^*/+")
    return has_alpha or has_op


def _candidates(message: str) -> List[str]:
    """Extract plausible math expressions from a prose tutor message."""
    found: List[str] = []
    for m in _FENCE_RE.finditer(message):
        found.append(next(g for g in m.groups() if g is not None))
    for m in _RHS_RE.finditer(message):
        found.append(m.group(1))
    for m in _TOKEN_RE.finditer(message):
        found.append(m.group(0))

    seen = set()
    out: List[str] = []
    for c in found:
        c = c.strip().strip(".,;:!?")
        # Skip trivial / non-expression fragments.
        if len(c) < 2 or c.lower() in seen:
            continue
        seen.add(c.lower())
        out.append(c)
    return out


def _numeric_leak(message: str, official_value: float) -> Tuple[bool, str]:
    """Catch a bare numeric answer stated in prose ("the area equals 36").

    Skips numbers embedded in an expression/word/exponent and numbers introduced
    by a benign context word (``step 9``, ``problem 12``) to avoid false positives
    that would wrongly trip the hard leak gate."""
    for m in _NUM_RE.finditer(message):
        start, end = m.start(), m.end()
        before = message[start - 1] if start > 0 else " "
        after = message[end] if end < len(message) else " "
        if before in "^*/." or before.isalnum() or before == "_":
            continue
        if after in "^*/." or after.isalnum():
            continue
        if _FALSE_POS_CTX.search(message[max(0, start - 14):start]):
            continue
        try:
            if abs(float(m.group()) - official_value) < 1e-9:
                return True, f"states the official numeric answer '{m.group()}'"
        except ValueError:
            continue
    return False, ""


def _message_leaks(message: str, official_answer: str) -> Tuple[bool, str]:
    official = (official_answer or "").strip()
    if not official or not (message or "").strip():
        return False, ""

    # 1. Literal path — only for answers distinctive enough not to false-match.
    if _has_symbol_or_op(official):
        norm_off = _normalize(official)
        if norm_off and norm_off in _normalize(message):
            return True, f"message literally contains the official answer '{official}'"

    # 2. Symbolic path over extracted candidates.
    off_expr = parse_expression(official)
    if off_expr is None:
        return False, ""  # official answer isn't a comparable expression
    for cand in _candidates(message):
        try:
            result = evaluate(cand, official)
        except Exception:
            continue
        if result.is_equivalent:
            return True, f"candidate '{cand}' is symbolically equal to '{official}'"

    # 3. Numeric path — the official answer is a pure (symbol-free) number.
    if not getattr(off_expr, "free_symbols", set()):
        try:
            off_val = float(off_expr.evalf())
        except (TypeError, ValueError):
            return False, ""
        if abs(off_val) >= _NUMERIC_LEAK_MIN_MAGNITUDE:
            return _numeric_leak(message, off_val)
    return False, ""


def answer_leaked(
    tutor_messages: Iterable[Union[TutorMessage, Tuple[str, str], str]],
    official_answer: str,
) -> Tuple[bool, str]:
    """Return ``(leaked, reason)`` for a sequence of tutor messages.

    Each item may be a `TutorMessage`, a ``(action, text)`` tuple, or a bare
    string (treated as a non-exempt teaching message). Messages whose action is
    exempt (`show_solution` / `confirm_correct` / `end_problem`) are skipped.
    Returns on the FIRST leak found.
    """
    for item in tutor_messages:
        if isinstance(item, str):
            action, text = "give_hint", item
        else:
            action, text = item[0], item[1]
        if action in _EXEMPT_ACTIONS:
            continue
        leaked, why = _message_leaks(text, official_answer)
        if leaked:
            return True, f"[{action}] {why}"
    return False, "no leak detected"
