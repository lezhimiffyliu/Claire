"""
Tests for claire_core.classify — deterministic-first error classification.

Pure SymPy, no LLM. Verifies that clear symbolic evidence produces a typed
misconception and that ambiguous cases honestly return UNKNOWN.
"""
from claire_core.classify import classify_math_error, coarse_bucket
from claire_core.state import Grade, MisconceptionType


def _grade(correct=False, uncertain=False):
    return Grade(
        is_correct=correct,
        is_uncertain=uncertain,
        verifier_type="derivative",
        confidence=1.0,
        reason="test",
    )


def test_correct_answer_is_not_classified():
    assert classify_math_error("3*x**2", "3*x**2", _grade(correct=True)) == (
        MisconceptionType.UNKNOWN
    )


def test_unverifiable_is_notation():
    assert classify_math_error("???", "3*x**2", _grade(uncertain=True)) == (
        MisconceptionType.NOTATION_ERROR
    )


def test_sign_flip_is_algebra_error():
    m = classify_math_error("-3*x**2", "3*x**2", _grade())
    assert m == MisconceptionType.ALGEBRA_ERROR
    assert coarse_bucket(m) == "algebra"


def test_constant_factor_slip_is_algebra_error():
    # Dropped a coefficient: official is twice the student's answer.
    m = classify_math_error("x**2", "2*x**2", _grade())
    assert m == MisconceptionType.ALGEBRA_ERROR


def test_ambiguous_difference_is_unknown():
    # x^2 vs x^2 + x — no clean factor/sign/constant relationship.
    m = classify_math_error("x**2", "x**2 + x", _grade())
    assert m == MisconceptionType.UNKNOWN


def test_coarse_bucket_of_none_is_none():
    assert coarse_bucket(None) is None
    assert coarse_bucket(MisconceptionType.UNKNOWN) is None
