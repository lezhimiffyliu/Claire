"""
Tests for sympy_tools.py - Expression parsing and error handling.

Focus: Test OUR code (parsing, error handling), not SymPy's math.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sympy_tools import parse_expression
import sympy as sp


class TestExpressionParsing:
    """Test parse_expression() - our custom parsing logic."""

    def test_caret_to_power_conversion(self):
        """Test our code: expr.replace('^', '**')"""
        result = parse_expression("x^2")
        expected = sp.Symbol("x") ** 2
        assert result == expected

    def test_ln_to_log_conversion(self):
        """Test our code: expr.replace('ln(', 'log(')"""
        result = parse_expression("ln(x)")
        expected = sp.log(sp.Symbol("x"))
        assert result == expected

    def test_implicit_multiplication(self):
        """Test our code: implicit_multiplication_application transform."""
        result = parse_expression("2x")
        expected = 2 * sp.Symbol("x")
        assert result == expected

    def test_implicit_multiplication_with_parentheses(self):
        """Test our code: 2(x+1) parsed as 2*(x+1)."""
        result = parse_expression("2(x+1)")
        expected = 2 * (sp.Symbol("x") + 1)
        assert result.expand() == expected.expand()

    def test_whitespace_stripped(self):
        """Test our code: expr.strip()"""
        result = parse_expression("  x^2  ")
        expected = sp.Symbol("x") ** 2
        assert result == expected


class TestToolErrorHandling:
    """Test our try/catch blocks return friendly error messages."""

    def test_derivative_invalid_expression_returns_error(self):
        """Test our code: except block returns 'Error...' string."""
        from sympy_tools import calculate_derivative

        result = calculate_derivative.invoke({"expression": "invalid[[["})
        assert "Error" in result
        assert isinstance(result, str)

    def test_integral_unclosed_paren_returns_error(self):
        """Test our code: except block handles syntax errors."""
        from sympy_tools import calculate_integral

        result = calculate_integral.invoke({"expression": "sin(x"})
        assert "Error" in result

    def test_limit_invalid_expression_returns_error(self):
        """Test our code: except block in calculate_limit."""
        from sympy_tools import calculate_limit

        result = calculate_limit.invoke({
            "expression": "invalid[[[",
            "variable": "x",
            "approaching": "0"
        })
        assert "Error" in result

    def test_solve_invalid_equation_returns_error(self):
        """Test our code: except block in solve_equation."""
        from sympy_tools import solve_equation

        result = solve_equation.invoke({"equation": "[[invalid"})
        assert "Error" in result


class TestToolOutputFormat:
    """Test our string formatting in tool return values."""

    def test_derivative_includes_latex(self):
        """Test our code: f'LaTeX: ${latex_result}$' formatting."""
        from sympy_tools import calculate_derivative

        result = calculate_derivative.invoke({"expression": "x^2"})
        assert "LaTeX" in result
        assert "$" in result

    def test_integral_indefinite_includes_constant(self):
        """Test our code: '+ C' appended for indefinite integrals."""
        from sympy_tools import calculate_integral

        result = calculate_integral.invoke({"expression": "x"})
        assert "+ C" in result

    def test_integral_definite_shows_bounds_label(self):
        """Test our code: 'Definite integral from X to Y' formatting."""
        from sympy_tools import calculate_integral

        result = calculate_integral.invoke({
            "expression": "x",
            "lower_bound": "0",
            "upper_bound": "1"
        })
        assert "Definite" in result
        assert "from" in result
