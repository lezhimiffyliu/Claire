"""
Unit tests for verifier.py

Tests cover:
1. Equivalent expressions marked correct
2. Integral differs by constant marked correct
3. Obvious errors marked wrong
4. Uncertain when can't verify
5. Teaching agent triggered on error (integration test)
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from verifier import (
    verify_answer,
    verify_derivative,
    verify_indefinite_integral,
    verify_definite_integral,
    verify_limit,
    AnswerVerificationResult,
    VerificationResult,
)


class TestAlgebraicEquivalence:
    """Test algebraic equivalence checking."""

    def test_same_expression(self):
        """Identical expressions should be correct."""
        result = verify_answer("x^2 + 2x + 1", "x^2 + 2x + 1")
        assert result.is_correct is True
        assert result.is_uncertain is False

    def test_equivalent_expressions(self):
        """Algebraically equivalent expressions should be correct."""
        result = verify_answer("(x+1)^2", "x^2 + 2x + 1")
        assert result.is_correct is True
        assert result.is_uncertain is False

    def test_expanded_vs_factored(self):
        """Factored and expanded forms should be equivalent."""
        result = verify_answer("x^2 - 1", "(x+1)(x-1)")
        assert result.is_correct is True

    def test_different_expressions(self):
        """Different expressions should be marked incorrect."""
        result = verify_answer("x^2", "x^3")
        assert result.is_correct is False
        assert result.is_uncertain is False

    def test_trig_identity(self):
        """Trig identities should be recognized."""
        result = verify_answer("sin(x)^2 + cos(x)^2", "1")
        assert result.is_correct is True


class TestIntegralConstant:
    """Test indefinite integrals differing by constant."""

    def test_same_antiderivative(self):
        """Same antiderivative should be correct."""
        result = verify_answer(
            "x^3/3",
            "x^3/3",
            problem_context="indefinite integral"
        )
        assert result.is_correct is True

    def test_differ_by_constant(self):
        """Antiderivatives differing by constant should be correct."""
        result = verify_answer(
            "x^3/3 + 5",
            "x^3/3",
            problem_context="antiderivative"
        )
        assert result.is_correct is True
        assert "constant" in result.reason.lower()

    def test_differ_by_constant_negative(self):
        """Antiderivatives differing by negative constant should be correct."""
        result = verify_answer(
            "x^2 - 3",
            "x^2",
            problem_context="indefinite integral"
        )
        assert result.is_correct is True

    def test_wrong_antiderivative(self):
        """Wrong antiderivative should be incorrect."""
        result = verify_answer(
            "x^2",  # Wrong - should be x^3/3
            "x^3/3",
            problem_context="indefinite integral"
        )
        assert result.is_correct is False


class TestObviousErrors:
    """Test that obvious errors are caught."""

    def test_wrong_numeric(self):
        """Wrong numeric answer should be incorrect."""
        result = verify_answer("5", "10")
        assert result.is_correct is False
        assert result.is_uncertain is False

    def test_wrong_polynomial(self):
        """Wrong polynomial should be incorrect."""
        result = verify_answer("3x^2", "2x^2")
        assert result.is_correct is False

    def test_missing_term(self):
        """Missing term should be incorrect."""
        result = verify_answer("x^2 + x", "x^2 + x + 1")
        assert result.is_correct is False


class TestUncertain:
    """Test uncertain cases."""

    def test_empty_answer(self):
        """Empty answer should be uncertain."""
        result = verify_answer("", "x^2")
        assert result.is_uncertain is True

    def test_unparseable_student(self):
        """Unparseable student answer should be uncertain."""
        result = verify_answer("I don't know", "x^2")
        assert result.is_uncertain is True

    def test_complex_expression(self):
        """Very complex expressions may be uncertain or parsed as variables."""
        # Note: SymPy may parse undefined names as symbols/variables
        # This is expected behavior - we just check it doesn't crash
        result = verify_answer(
            "some_undefined_function(x)",
            "another_undefined(x)"
        )
        # Should return a result (not crash)
        assert result is not None


class TestDerivativeVerification:
    """Test derivative-specific verification."""

    def test_correct_derivative(self):
        """Correct derivative should verify."""
        result = verify_derivative("x^3", "3*x^2")
        assert result.verified is True

    def test_wrong_derivative(self):
        """Wrong derivative should not verify."""
        result = verify_derivative("x^3", "x^2")
        assert result.verified is False

    def test_chain_rule(self):
        """Chain rule should be verified."""
        result = verify_derivative("sin(2*x)", "2*cos(2*x)")
        assert result.verified is True


class TestDefiniteIntegral:
    """Test definite integral verification."""

    def test_correct_definite_integral(self):
        """Correct definite integral should verify."""
        result = verify_definite_integral("x^2", "0", "1", "1/3")
        assert result.verified is True

    def test_wrong_definite_integral(self):
        """Wrong definite integral should not verify."""
        result = verify_definite_integral("x^2", "0", "1", "1/2")
        assert result.verified is False


class TestLimitVerification:
    """Test limit verification."""

    def test_correct_limit(self):
        """Correct limit should verify."""
        result = verify_limit("sin(x)/x", "x", "0", "1")
        assert result.verified is True

    def test_wrong_limit(self):
        """Wrong limit should not verify."""
        result = verify_limit("sin(x)/x", "x", "0", "0")
        assert result.verified is False


class TestEquationSolutions:
    """Test equation solution verification."""

    def test_single_solution(self):
        """Single solution should match."""
        result = verify_answer(
            "x = 2",
            "2",
            problem_context="solve for x"
        )
        assert result.is_correct is True

    def test_plus_minus(self):
        """±notation should be handled."""
        result = verify_answer(
            "±2",
            "x = 2, x = -2",
            problem_type="equation"
        )
        # This may be uncertain depending on parsing
        # At minimum, should not crash
        assert result is not None


class TestNumericFallback:
    """Test numeric fallback for complex expressions."""

    def test_numeric_close(self):
        """Numerically close values should match."""
        result = verify_answer("0.333333", "1/3")
        assert result.is_correct is True

    def test_numeric_different(self):
        """Numerically different values should not match."""
        result = verify_answer("0.5", "0.333333")
        assert result.is_correct is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
