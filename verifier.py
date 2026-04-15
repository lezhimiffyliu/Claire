"""
SymPy-based verification layer for calculus answers.

Provides verification for:
- Derivatives: verify d/dx[f] = g by comparing symbolic results
- Indefinite integrals: verify by differentiating and comparing
- Definite integrals: verify by symbolic or numeric evaluation

Uses symbolic comparison first, then numeric fallback if symbolic fails.
"""

from dataclasses import dataclass
from typing import Optional, Literal
import sympy as sp
from sympy import symbols, diff, integrate, simplify, Abs, N
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)
import random

# Reuse safe namespace from sympy_tools
x, y, z, t = symbols("x y z t")

SAFE_NAMESPACE = {
    "x": x, "y": y, "z": z, "t": t,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "sec": sp.sec, "csc": sp.csc, "cot": sp.cot,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp, "log": sp.log, "ln": sp.log,
    "sqrt": sp.sqrt, "abs": sp.Abs,
    "pi": sp.pi, "e": sp.E, "E": sp.E,
    "oo": sp.oo, "inf": sp.oo,
}


@dataclass
class VerificationResult:
    """Result of a verification check."""
    verified: bool
    method: Literal["symbolic", "numeric", "failed"]
    reason: str
    details: Optional[str] = None


@dataclass
class AnswerVerificationResult:
    """Result of unified answer verification."""
    is_correct: bool
    is_uncertain: bool  # True if we can't determine correctness
    verifier_type: str  # "algebraic" | "derivative" | "integral" | "limit" | "equation" | "numeric" | "uncertain"
    normalized_student: Optional[str]
    normalized_official: Optional[str]
    reason: str
    confidence: float  # 0-1, how confident we are in this judgment


def parse_expression(expr_str: str) -> sp.Expr:
    """Parse a string into a SymPy expression."""
    if isinstance(expr_str, sp.Expr):
        return expr_str

    expr_str = str(expr_str).strip()

    # Common notation conversions
    expr_str = expr_str.replace("^", "**")
    expr_str = expr_str.replace("ln(", "log(")

    # Handle implicit multiplication
    transformations = standard_transformations + (implicit_multiplication_application,)

    try:
        return parse_expr(
            expr_str, local_dict=SAFE_NAMESPACE, transformations=transformations
        )
    except Exception:
        # Fallback
        return eval(expr_str, {"__builtins__": {}}, SAFE_NAMESPACE)


def _symbolic_equal(expr1: sp.Expr, expr2: sp.Expr) -> Optional[bool]:
    """
    Check if two expressions are symbolically equal.
    Returns True/False if can determine, None if uncertain.
    """
    try:
        diff_expr = simplify(expr1 - expr2)
        if diff_expr == 0:
            return True
        if diff_expr.is_number and diff_expr != 0:
            return False
        # Try expand then simplify
        diff_expr = simplify(sp.expand(expr1) - sp.expand(expr2))
        if diff_expr == 0:
            return True
        # Try trigsimp for trig expressions
        diff_expr = sp.trigsimp(expr1 - expr2)
        if diff_expr == 0:
            return True
        return None  # Uncertain
    except Exception:
        return None


def _numeric_equal(expr1: sp.Expr, expr2: sp.Expr, var: sp.Symbol,
                   test_points: int = 5, tolerance: float = 1e-5) -> Optional[bool]:
    """
    Check if two expressions are numerically equal at random test points.
    Returns True if equal at all points, False if not, None if can't test.
    """
    try:
        # If both are constant (no free symbols), compare directly
        if not expr1.free_symbols and not expr2.free_symbols:
            try:
                val1 = complex(N(expr1))
                val2 = complex(N(expr2))
                if val1 == val1 and val2 == val2:  # not nan
                    rel_diff = abs(val1 - val2) / max(abs(val1), abs(val2), 1e-10)
                    return rel_diff < tolerance
            except Exception:
                pass

        # Generate test points avoiding common problem spots
        points = []
        for _ in range(test_points):
            val = random.uniform(0.5, 3.0) * random.choice([1, -1])
            points.append(val)

        tested = 0
        for pt in points:
            try:
                val1 = complex(N(expr1.subs(var, pt)))
                val2 = complex(N(expr2.subs(var, pt)))

                # Skip if either is nan/inf
                if not (val1 == val1 and val2 == val2):  # nan check
                    continue
                if abs(val1) > 1e10 or abs(val2) > 1e10:
                    continue

                tested += 1
                # Check equality
                if abs(val1 - val2) > tolerance * max(abs(val1), abs(val2), 1):
                    return False
            except Exception:
                continue

        # Need at least 2 successful test points
        return True if tested >= 2 else None
    except Exception:
        return None


def verify_derivative(original: str, proposed_derivative: str,
                      variable: str = "x") -> VerificationResult:
    """
    Verify that proposed_derivative is the derivative of original.

    Args:
        original: The original expression f(x)
        proposed_derivative: The claimed derivative f'(x)
        variable: Variable of differentiation

    Returns:
        VerificationResult with verified status and method
    """
    try:
        orig_expr = parse_expression(original)
        prop_expr = parse_expression(proposed_derivative)
        var = symbols(variable)

        # Compute actual derivative
        actual_deriv = diff(orig_expr, var)

        # Try symbolic comparison
        sym_result = _symbolic_equal(actual_deriv, prop_expr)
        if sym_result is True:
            return VerificationResult(
                verified=True,
                method="symbolic",
                reason="Symbolic comparison confirms derivative is correct."
            )
        elif sym_result is False:
            return VerificationResult(
                verified=False,
                method="symbolic",
                reason="Symbolic comparison shows derivative is incorrect.",
                details=f"Expected: {actual_deriv}, Got: {prop_expr}"
            )

        # Symbolic uncertain, try numeric
        num_result = _numeric_equal(actual_deriv, prop_expr, var)
        if num_result is True:
            return VerificationResult(
                verified=True,
                method="numeric",
                reason="Numeric spot checks confirm derivative is correct."
            )
        elif num_result is False:
            return VerificationResult(
                verified=False,
                method="numeric",
                reason="Numeric comparison shows derivative is incorrect.",
                details=f"Expected: {actual_deriv}, Got: {prop_expr}"
            )

        # Can't verify either way
        return VerificationResult(
            verified=False,
            method="failed",
            reason="Could not verify derivative (expressions too complex)."
        )

    except Exception as e:
        return VerificationResult(
            verified=False,
            method="failed",
            reason=f"Verification failed: {str(e)}"
        )


def verify_indefinite_integral(integrand: str, proposed_antiderivative: str,
                                variable: str = "x") -> VerificationResult:
    """
    Verify indefinite integral by differentiating the proposed antiderivative.

    The antiderivative F(x) is correct if F'(x) = f(x), where f is the integrand.
    Note: We ignore constants of integration.

    Args:
        integrand: The function being integrated f(x)
        proposed_antiderivative: The claimed antiderivative F(x)
        variable: Variable of integration

    Returns:
        VerificationResult with verified status and method
    """
    try:
        integ_expr = parse_expression(integrand)
        prop_expr = parse_expression(proposed_antiderivative)
        var = symbols(variable)

        # Differentiate the proposed antiderivative
        deriv_of_prop = diff(prop_expr, var)

        # Compare with integrand
        sym_result = _symbolic_equal(deriv_of_prop, integ_expr)
        if sym_result is True:
            return VerificationResult(
                verified=True,
                method="symbolic",
                reason="Differentiating the antiderivative gives the integrand."
            )
        elif sym_result is False:
            return VerificationResult(
                verified=False,
                method="symbolic",
                reason="Antiderivative incorrect: its derivative doesn't match integrand.",
                details=f"d/dx[{prop_expr}] = {deriv_of_prop}, but integrand is {integ_expr}"
            )

        # Try numeric
        num_result = _numeric_equal(deriv_of_prop, integ_expr, var)
        if num_result is True:
            return VerificationResult(
                verified=True,
                method="numeric",
                reason="Numeric checks confirm antiderivative is correct."
            )
        elif num_result is False:
            return VerificationResult(
                verified=False,
                method="numeric",
                reason="Antiderivative incorrect based on numeric checks.",
                details=f"d/dx[{prop_expr}] doesn't match {integ_expr}"
            )

        return VerificationResult(
            verified=False,
            method="failed",
            reason="Could not verify antiderivative (expressions too complex)."
        )

    except Exception as e:
        return VerificationResult(
            verified=False,
            method="failed",
            reason=f"Verification failed: {str(e)}"
        )


def verify_definite_integral(integrand: str, lower: str, upper: str,
                              proposed_value: str, variable: str = "x",
                              tolerance: float = 1e-6) -> VerificationResult:
    """
    Verify a definite integral result.

    Args:
        integrand: The function being integrated
        lower: Lower bound of integration
        upper: Upper bound of integration
        proposed_value: The claimed value of the integral
        variable: Variable of integration
        tolerance: Relative tolerance for numeric comparison

    Returns:
        VerificationResult with verified status and method
    """
    try:
        integ_expr = parse_expression(integrand)
        lower_val = parse_expression(lower)
        upper_val = parse_expression(upper)
        prop_val = parse_expression(proposed_value)
        var = symbols(variable)

        # Compute actual definite integral
        actual_val = integrate(integ_expr, (var, lower_val, upper_val))

        # Try symbolic comparison
        sym_result = _symbolic_equal(actual_val, prop_val)
        if sym_result is True:
            return VerificationResult(
                verified=True,
                method="symbolic",
                reason="Symbolic evaluation confirms definite integral is correct."
            )
        elif sym_result is False:
            return VerificationResult(
                verified=False,
                method="symbolic",
                reason="Definite integral value is incorrect.",
                details=f"Expected: {actual_val}, Got: {prop_val}"
            )

        # Try numeric comparison
        try:
            actual_numeric = complex(N(actual_val))
            prop_numeric = complex(N(prop_val))

            if abs(actual_numeric) < 1e-10 and abs(prop_numeric) < 1e-10:
                return VerificationResult(
                    verified=True,
                    method="numeric",
                    reason="Both values are approximately zero."
                )

            rel_diff = abs(actual_numeric - prop_numeric) / max(abs(actual_numeric), 1e-10)
            if rel_diff < tolerance:
                return VerificationResult(
                    verified=True,
                    method="numeric",
                    reason=f"Numeric evaluation confirms value (rel. diff: {rel_diff:.2e})."
                )
            else:
                return VerificationResult(
                    verified=False,
                    method="numeric",
                    reason="Definite integral value doesn't match.",
                    details=f"Expected: {actual_numeric}, Got: {prop_numeric}"
                )
        except Exception:
            pass

        return VerificationResult(
            verified=False,
            method="failed",
            reason="Could not verify definite integral."
        )

    except Exception as e:
        return VerificationResult(
            verified=False,
            method="failed",
            reason=f"Verification failed: {str(e)}"
        )


def verify_limit(expression: str, variable: str, approaching: str,
                 proposed_value: str, direction: str = None) -> VerificationResult:
    """
    Verify a limit result.

    Args:
        expression: The expression whose limit is being computed
        variable: The variable approaching a value
        approaching: The value being approached
        proposed_value: The claimed limit value
        direction: '+' for right-hand, '-' for left-hand, None for two-sided

    Returns:
        VerificationResult with verified status and method
    """
    try:
        expr = parse_expression(expression)
        prop_val = parse_expression(proposed_value)
        var = symbols(variable)

        # Parse approaching value
        if approaching in ["oo", "inf", "infinity"]:
            approach_val = sp.oo
        elif approaching in ["-oo", "-inf", "-infinity"]:
            approach_val = -sp.oo
        else:
            approach_val = parse_expression(approaching)

        # Compute actual limit
        if direction == "+":
            actual_val = sp.limit(expr, var, approach_val, "+")
        elif direction == "-":
            actual_val = sp.limit(expr, var, approach_val, "-")
        else:
            actual_val = sp.limit(expr, var, approach_val)

        # Compare
        sym_result = _symbolic_equal(actual_val, prop_val)
        if sym_result is True:
            return VerificationResult(
                verified=True,
                method="symbolic",
                reason="Limit value is correct."
            )
        elif sym_result is False:
            return VerificationResult(
                verified=False,
                method="symbolic",
                reason="Limit value is incorrect.",
                details=f"Expected: {actual_val}, Got: {prop_val}"
            )

        # Try numeric if both are finite numbers
        try:
            actual_num = complex(N(actual_val))
            prop_num = complex(N(prop_val))
            if abs(actual_num - prop_num) < 1e-8:
                return VerificationResult(
                    verified=True,
                    method="numeric",
                    reason="Numeric comparison confirms limit."
                )
            else:
                return VerificationResult(
                    verified=False,
                    method="numeric",
                    reason="Limit value doesn't match.",
                    details=f"Expected: {actual_num}, Got: {prop_num}"
                )
        except Exception:
            pass

        return VerificationResult(
            verified=False,
            method="failed",
            reason="Could not verify limit."
        )

    except Exception as e:
        return VerificationResult(
            verified=False,
            method="failed",
            reason=f"Verification failed: {str(e)}"
        )


def auto_verify(problem_type: str, **kwargs) -> VerificationResult:
    """
    Automatically route to the appropriate verification function.

    Args:
        problem_type: One of "derivative", "indefinite_integral", "definite_integral", "limit"
        **kwargs: Arguments for the specific verification function

    Returns:
        VerificationResult
    """
    if problem_type == "derivative":
        return verify_derivative(
            kwargs.get("original", ""),
            kwargs.get("proposed", ""),
            kwargs.get("variable", "x")
        )
    elif problem_type == "indefinite_integral":
        return verify_indefinite_integral(
            kwargs.get("integrand", ""),
            kwargs.get("proposed", ""),
            kwargs.get("variable", "x")
        )
    elif problem_type == "definite_integral":
        return verify_definite_integral(
            kwargs.get("integrand", ""),
            kwargs.get("lower", ""),
            kwargs.get("upper", ""),
            kwargs.get("proposed", ""),
            kwargs.get("variable", "x")
        )
    elif problem_type == "limit":
        return verify_limit(
            kwargs.get("expression", ""),
            kwargs.get("variable", "x"),
            kwargs.get("approaching", ""),
            kwargs.get("proposed", ""),
            kwargs.get("direction")
        )
    else:
        return VerificationResult(
            verified=False,
            method="failed",
            reason=f"Unknown problem type: {problem_type}"
        )


def _detect_answer_type(official_answer: str, problem_context: Optional[str] = None) -> str:
    """
    Detect the type of answer for routing to appropriate verifier.

    Returns: "derivative" | "indefinite_integral" | "definite_integral" |
             "limit" | "equation" | "algebraic" | "numeric"
    """
    context = (problem_context or "").lower()
    answer = official_answer.lower()

    # Check problem context first
    # IMPORTANT: Check integrals BEFORE derivatives (antiderivative contains "derivative")
    if any(kw in context for kw in ["indefinite integral", "antiderivative", "indefinite", "∫"]):
        return "indefinite_integral"

    if any(kw in context for kw in ["derivative", "differentiate", "d/dx", "f'(x)"]):
        return "derivative"

    if any(kw in context for kw in ["definite integral", "evaluate"]) and any(kw in context for kw in ["from", "to", "between"]):
        return "definite_integral"

    if any(kw in context for kw in ["limit", "lim", "approaches"]):
        return "limit"

    if any(kw in context for kw in ["solve", "find x", "find the roots", "solution"]):
        return "equation"

    # Check answer format
    if "+ c" in answer or "+c" in answer:
        return "indefinite_integral"  # Likely has +C

    # Default to algebraic comparison
    return "algebraic"


def _normalize_expression(expr_str: str) -> str:
    """Normalize an expression string for comparison."""
    if not expr_str:
        return ""

    s = str(expr_str).strip()

    # Remove common LaTeX artifacts
    s = s.replace("\\", "")
    s = s.replace("$", "")
    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("frac", "")
    s = s.replace("cdot", "*")
    s = s.replace("times", "*")

    # Normalize notation
    s = s.replace("^", "**")
    s = s.replace("ln(", "log(")

    return s.strip()


def _extract_numeric_value(expr_str: str) -> Optional[float]:
    """Try to extract a numeric value from an expression."""
    try:
        expr = parse_expression(expr_str)
        val = complex(N(expr))
        if val.imag == 0:
            return val.real
        return None
    except Exception:
        return None


def _compare_solution_sets(student: str, official: str) -> Optional[bool]:
    """
    Compare two solution sets (for equation solving).
    Handles: x = 2, x = {2, -2}, x = ±2, etc.
    Returns True if equivalent, False if different, None if uncertain.
    """
    try:
        # Parse both as sets of solutions
        def parse_solutions(s: str) -> set:
            s = s.strip()

            # Handle ± notation
            if "±" in s or "+-" in s:
                s = s.replace("±", "").replace("+-", "")
                val = parse_expression(s)
                return {val, -val}

            # Handle set notation {a, b, c}
            if "{" in s:
                s = s.replace("{", "").replace("}", "")
                parts = s.split(",")
                return {parse_expression(p.strip()) for p in parts}

            # Handle x = a or just a
            if "=" in s:
                s = s.split("=")[-1].strip()

            return {parse_expression(s)}

        student_set = parse_solutions(student)
        official_set = parse_solutions(official)

        # Compare sets (with simplification)
        if len(student_set) != len(official_set):
            return False

        for s_val in student_set:
            found = False
            for o_val in official_set:
                if _symbolic_equal(s_val, o_val) is True:
                    found = True
                    break
            if not found:
                return False

        return True

    except Exception:
        return None


def verify_answer(
    student_answer: str,
    official_answer: str,
    problem_context: Optional[str] = None,
    problem_type: Optional[str] = None,
) -> AnswerVerificationResult:
    """
    Unified entry point for answer verification.

    Supports:
    - Algebraic equivalence (e.g., x^2 + 2x + 1 vs (x+1)^2)
    - Derivatives
    - Integrals (allows constant difference for indefinite)
    - Limits
    - Equation solutions (handles ±, sets)
    - Numeric fallback

    Args:
        student_answer: The student's answer as string
        official_answer: The correct answer as string
        problem_context: Optional context about the problem (question text)
        problem_type: Optional explicit type override

    Returns:
        AnswerVerificationResult with is_correct, is_uncertain, verifier_type, etc.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Normalize inputs
    student_norm = _normalize_expression(student_answer)
    official_norm = _normalize_expression(official_answer)

    if not student_norm or not official_norm:
        logger.warning(f"[verifier] Empty input: student='{student_answer}', official='{official_answer}'")
        return AnswerVerificationResult(
            is_correct=False,
            is_uncertain=True,
            verifier_type="uncertain",
            normalized_student=student_norm,
            normalized_official=official_norm,
            reason="Empty or unparseable answer",
            confidence=0.0,
        )

    # Detect answer type
    answer_type = problem_type or _detect_answer_type(official_answer, problem_context)
    logger.info(f"[verifier] Detected answer type: {answer_type}")

    try:
        # Route to appropriate verifier

        # === ALGEBRAIC EQUIVALENCE ===
        if answer_type == "algebraic":
            student_expr = parse_expression(student_norm)
            official_expr = parse_expression(official_norm)

            # Try symbolic
            sym_result = _symbolic_equal(student_expr, official_expr)
            if sym_result is True:
                return AnswerVerificationResult(
                    is_correct=True,
                    is_uncertain=False,
                    verifier_type="algebraic",
                    normalized_student=str(student_expr),
                    normalized_official=str(official_expr),
                    reason="Expressions are algebraically equivalent",
                    confidence=1.0,
                )

            # Try numeric BEFORE declaring symbolic failure
            # (handles cases like 0.333333 vs 1/3)
            num_result = _numeric_equal(student_expr, official_expr, x)
            if num_result is True:
                return AnswerVerificationResult(
                    is_correct=True,
                    is_uncertain=False,
                    verifier_type="numeric",
                    normalized_student=str(student_expr),
                    normalized_official=str(official_expr),
                    reason="Numeric spot checks confirm equivalence",
                    confidence=0.85,
                )
            elif num_result is False:
                return AnswerVerificationResult(
                    is_correct=False,
                    is_uncertain=False,
                    verifier_type="numeric",
                    normalized_student=str(student_expr),
                    normalized_official=str(official_expr),
                    reason="Numeric comparison shows difference",
                    confidence=0.85,
                )

            # If symbolic said False and numeric couldn't help
            if sym_result is False:
                return AnswerVerificationResult(
                    is_correct=False,
                    is_uncertain=False,
                    verifier_type="algebraic",
                    normalized_student=str(student_expr),
                    normalized_official=str(official_expr),
                    reason="Expressions are not equivalent",
                    confidence=0.9,
                )

        # === INDEFINITE INTEGRAL (allow +C difference) ===
        elif answer_type == "indefinite_integral":
            # Remove +C if present (case insensitive)
            import re
            student_clean = re.sub(r'\+\s*[Cc]$', '', student_norm).strip()
            official_clean = re.sub(r'\+\s*[Cc]$', '', official_norm).strip()

            try:
                student_expr = parse_expression(student_clean)
                official_expr = parse_expression(official_clean)

                # Check if they differ by a constant
                diff_expr = simplify(student_expr - official_expr)

                if diff_expr.is_number:
                    # Differ by a constant - this is CORRECT for indefinite integrals
                    return AnswerVerificationResult(
                        is_correct=True,
                        is_uncertain=False,
                        verifier_type="integral",
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason="Antiderivatives differ by a constant (both correct)",
                        confidence=1.0,
                    )

                # Check if same
                sym_result = _symbolic_equal(student_expr, official_expr)
                if sym_result is True:
                    return AnswerVerificationResult(
                        is_correct=True,
                        is_uncertain=False,
                        verifier_type="integral",
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason="Antiderivatives are equivalent",
                        confidence=1.0,
                    )

                # Try numeric comparison
                num_result = _numeric_equal(student_expr, official_expr, x)
                if num_result is False:
                    return AnswerVerificationResult(
                        is_correct=False,
                        is_uncertain=False,
                        verifier_type="integral",
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason="Antiderivatives are different (not by constant)",
                        confidence=0.9,
                    )

            except Exception as e:
                logger.warning(f"[verifier] Integral comparison error: {e}")

        # === EQUATION SOLUTIONS ===
        elif answer_type == "equation":
            result = _compare_solution_sets(student_norm, official_norm)
            if result is True:
                return AnswerVerificationResult(
                    is_correct=True,
                    is_uncertain=False,
                    verifier_type="equation",
                    normalized_student=student_norm,
                    normalized_official=official_norm,
                    reason="Solution sets are equivalent",
                    confidence=0.95,
                )
            elif result is False:
                return AnswerVerificationResult(
                    is_correct=False,
                    is_uncertain=False,
                    verifier_type="equation",
                    normalized_student=student_norm,
                    normalized_official=official_norm,
                    reason="Solution sets are different",
                    confidence=0.9,
                )

        # === DERIVATIVE / LIMIT / DEFINITE INTEGRAL ===
        # For these types, we compare the answers directly (algebraically)
        # The specialized verifiers (verify_derivative, etc.) require the original expression,
        # which we don't always have. So fall back to direct comparison.
        elif answer_type in ["derivative", "limit", "definite_integral"]:
            # Compare the answers directly using algebraic comparison
            try:
                student_expr = parse_expression(student_norm)
                official_expr = parse_expression(official_norm)

                sym_result = _symbolic_equal(student_expr, official_expr)
                if sym_result is True:
                    return AnswerVerificationResult(
                        is_correct=True,
                        is_uncertain=False,
                        verifier_type=answer_type,
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason=f"{answer_type.replace('_', ' ').title()} answer is correct",
                        confidence=1.0,
                    )
                elif sym_result is False:
                    return AnswerVerificationResult(
                        is_correct=False,
                        is_uncertain=False,
                        verifier_type=answer_type,
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason=f"{answer_type.replace('_', ' ').title()} answer is incorrect",
                        confidence=0.9,
                    )

                # Try numeric
                num_result = _numeric_equal(student_expr, official_expr, x)
                if num_result is True:
                    return AnswerVerificationResult(
                        is_correct=True,
                        is_uncertain=False,
                        verifier_type="numeric",
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason="Numeric comparison confirms equivalence",
                        confidence=0.85,
                    )
                elif num_result is False:
                    return AnswerVerificationResult(
                        is_correct=False,
                        is_uncertain=False,
                        verifier_type="numeric",
                        normalized_student=str(student_expr),
                        normalized_official=str(official_expr),
                        reason="Numeric comparison shows difference",
                        confidence=0.85,
                    )
            except Exception as e:
                logger.warning(f"[verifier] {answer_type} comparison error: {e}")

        # === NUMERIC FALLBACK ===
        student_val = _extract_numeric_value(student_norm)
        official_val = _extract_numeric_value(official_norm)

        if student_val is not None and official_val is not None:
            # Both are numeric - compare with tolerance
            if abs(official_val) < 1e-10:
                is_close = abs(student_val) < 1e-8
            else:
                is_close = abs(student_val - official_val) / abs(official_val) < 0.001

            return AnswerVerificationResult(
                is_correct=is_close,
                is_uncertain=False,
                verifier_type="numeric",
                normalized_student=str(student_val),
                normalized_official=str(official_val),
                reason="Numeric comparison" + (" matches" if is_close else " shows difference"),
                confidence=0.9,
            )

        # === UNCERTAIN ===
        logger.warning(f"[verifier] Cannot verify: student='{student_norm}', official='{official_norm}'")
        return AnswerVerificationResult(
            is_correct=False,
            is_uncertain=True,
            verifier_type="uncertain",
            normalized_student=student_norm,
            normalized_official=official_norm,
            reason="Cannot symbolically or numerically verify this answer",
            confidence=0.0,
        )

    except Exception as e:
        logger.error(f"[verifier] Exception: {e}")
        return AnswerVerificationResult(
            is_correct=False,
            is_uncertain=True,
            verifier_type="uncertain",
            normalized_student=student_norm,
            normalized_official=official_norm,
            reason=f"Verification error: {str(e)}",
            confidence=0.0,
        )


# Quick self-test when run directly
if __name__ == "__main__":
    print("=== Verifier Self-Test ===\n")

    # Test derivative verification
    print("1. Derivative verification:")
    result = verify_derivative("x**3", "3*x**2")
    print(f"   d/dx[x^3] = 3x^2 ? {result.verified} ({result.method})")

    result = verify_derivative("sin(x)", "cos(x)")
    print(f"   d/dx[sin(x)] = cos(x) ? {result.verified} ({result.method})")

    result = verify_derivative("x**2", "x")  # Wrong!
    print(f"   d/dx[x^2] = x ? {result.verified} ({result.method})")

    # Test indefinite integral verification
    print("\n2. Indefinite integral verification:")
    result = verify_indefinite_integral("2*x", "x**2")
    print(f"   integral(2x) = x^2 ? {result.verified} ({result.method})")

    result = verify_indefinite_integral("cos(x)", "sin(x)")
    print(f"   integral(cos(x)) = sin(x) ? {result.verified} ({result.method})")

    result = verify_indefinite_integral("x", "x**3")  # Wrong!
    print(f"   integral(x) = x^3 ? {result.verified} ({result.method})")

    # Test definite integral verification
    print("\n3. Definite integral verification:")
    result = verify_definite_integral("x**2", "0", "1", "1/3")
    print(f"   integral(x^2, 0, 1) = 1/3 ? {result.verified} ({result.method})")

    result = verify_definite_integral("sin(x)", "0", "pi", "2")
    print(f"   integral(sin(x), 0, pi) = 2 ? {result.verified} ({result.method})")

    # Test limit verification
    print("\n4. Limit verification:")
    result = verify_limit("sin(x)/x", "x", "0", "1")
    print(f"   lim(x->0) sin(x)/x = 1 ? {result.verified} ({result.method})")

    result = verify_limit("(x**2-1)/(x-1)", "x", "1", "2")
    print(f"   lim(x->1) (x^2-1)/(x-1) = 2 ? {result.verified} ({result.method})")

    print("\n=== Self-Test Complete ===")
