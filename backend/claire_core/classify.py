"""
claire_core.classify — deterministic-first error classification.

Turning a wrong answer into a *typed* misconception used to rely on the agent's
self-report. This module puts symbolic evidence first: it inspects the algebraic
relationship between the student's answer and the official one and only labels a
misconception it can actually justify. When the symbolic check is inconclusive
it returns UNKNOWN, and the caller (loop.py) falls back to the agent's
self-diagnosed misconception.

Pure and offline: SymPy only, no LLM, no I/O.
"""
from __future__ import annotations

from typing import Optional

import sympy as sp

from app.grading.verifier import parse_expression, x

from .state import Grade, GradeStatus, MisconceptionType


def classify_math_error(
    student_answer: str,
    official_answer: str,
    grade: Grade,
) -> MisconceptionType:
    """Classify the error in a graded attempt using symbolic evidence.

    Returns a `MisconceptionType`. `UNKNOWN` means "no deterministic evidence" —
    the caller should defer to the agent's self-report.
    """
    if grade.status == GradeStatus.CORRECT:
        return MisconceptionType.UNKNOWN  # nothing to classify
    if grade.status == GradeStatus.UNVERIFIABLE:
        # We could not even parse/verify the answer — likely notation.
        return MisconceptionType.NOTATION_ERROR

    try:
        student = parse_expression(student_answer)
        official = parse_expression(official_answer)
    except Exception:
        return MisconceptionType.NOTATION_ERROR

    try:
        # Sign flip: student == -official  →  a dropped/extra negative sign.
        if sp.simplify(student + official) == 0:
            return MisconceptionType.ALGEBRA_ERROR

        # Constant-factor slip: official / student is a nonzero constant ≠ 1
        # (e.g. dropped a coefficient) → arithmetic/algebra.
        if _is_nonzero(student):
            ratio = sp.simplify(official / student)
            if ratio.is_number and ratio != 1 and ratio != 0:
                return MisconceptionType.ALGEBRA_ERROR

            # Non-constant ratio that still involves the variable suggests a
            # whole missing factor — the classic chain-rule omission shape.
            if ratio.free_symbols and _looks_like_missing_factor(ratio):
                return MisconceptionType.CHAIN_RULE_OMISSION
    except Exception:
        return MisconceptionType.UNKNOWN

    return MisconceptionType.UNKNOWN


def _is_nonzero(expr: sp.Expr) -> bool:
    try:
        return expr != 0 and sp.simplify(expr) != 0
    except Exception:
        return False


def _looks_like_missing_factor(ratio: sp.Expr) -> bool:
    """A ratio that is a clean monomial / simple factor in the variable (not a
    messy rational) reads as 'you left off a multiplicative factor'."""
    try:
        r = sp.simplify(ratio)
        # Reject ratios that blow up or vanish; accept polynomial-ish factors.
        return r.is_polynomial(x) or r.is_polynomial()
    except Exception:
        return False


def coarse_bucket(misconception: Optional[MisconceptionType]) -> Optional[str]:
    """Map a fine misconception to the profile's coarse bucket, or None."""
    from .state import MISCONCEPTION_TO_BUCKET

    if misconception is None:
        return None
    return MISCONCEPTION_TO_BUCKET.get(misconception)
