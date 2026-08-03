"""
Claire Evaluator v2.0
Mathematical expression equivalence checking using SymPy.

Features:
- SymPy symbolic equivalence (NOT string matching)
- Set comparison for equations/multi-solution problems
- LaTeX parsing support
- Numeric fallback for edge cases

Design:
    ┌─────────────────────────────────────────────────────────────────┐
    │                      Evaluator Pipeline                         │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Input: (predicted_answer, ground_truth)                        │
    │                     │                                           │
    │                     ▼                                           │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │  1. Preprocessing                                        │   │
    │  │     - Strip whitespace                                   │   │
    │  │     - Convert LaTeX to SymPy format                      │   │
    │  │     - Normalize symbols (π→pi, √→sqrt)                   │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                     │                                           │
    │                     ▼                                           │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │  2. Type Detection                                       │   │
    │  │     - Single expression?                                 │   │
    │  │     - Set/List (multiple solutions)?                     │   │
    │  │     - Tuple/Coordinate?                                  │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                     │                                           │
    │          ┌─────────┴─────────┐                                 │
    │          ▼                   ▼                                 │
    │  ┌──────────────┐   ┌──────────────────┐                       │
    │  │ Expression   │   │ Set/List         │                       │
    │  │ Equivalence  │   │ Comparison       │                       │
    │  │              │   │                  │                       │
    │  │ - Parse both │   │ - Parse elements │                       │
    │  │ - simplify() │   │ - Compare as set │                       │
    │  │ - equals()   │   │ - Order agnostic │                       │
    │  └──────────────┘   └──────────────────┘                       │
    │          │                   │                                 │
    │          └─────────┬─────────┘                                 │
    │                    ▼                                           │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │  3. Fallback: Numeric Evaluation                         │   │
    │  │     - If symbolic fails, try numeric comparison          │   │
    │  │     - Evaluate at multiple test points                   │   │
    │  │     - Check within tolerance (1e-9)                      │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                     │                                           │
    │                     ▼                                           │
    │  Output: (is_equivalent: bool, method: str, details: str)       │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
"""

import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from sympy.parsing.latex import parse_latex
from typing import Tuple, Optional, List, Set, Union
from dataclasses import dataclass


# =============================================================================
# CONFIGURATION
# =============================================================================

# SymPy parsing transformations
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Common symbols
SYMBOLS = {
    'x': sp.Symbol('x'),
    'y': sp.Symbol('y'),
    'z': sp.Symbol('z'),
    'n': sp.Symbol('n'),
    't': sp.Symbol('t'),
    'a': sp.Symbol('a'),
    'b': sp.Symbol('b'),
    'c': sp.Symbol('c'),
    'k': sp.Symbol('k'),
    'pi': sp.pi,
    'e': sp.E,
    'E': sp.E,
    'i': sp.I,
    'I': sp.I,
    'inf': sp.oo,
    'oo': sp.oo,
}

# Numeric comparison tolerance
NUMERIC_TOLERANCE = 1e-9

# Test points for numeric evaluation
TEST_POINTS = [0.5, 1.0, 1.5, 2.0, -0.5, -1.0]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EvalResult:
    """Result of equivalence evaluation."""
    is_equivalent: bool
    method: str  # 'symbolic', 'numeric', 'set_match', 'exact_match', 'failed'
    details: str
    predicted_parsed: Optional[str] = None
    ground_truth_parsed: Optional[str] = None


# =============================================================================
# LATEX TO SYMPY CONVERSION
# =============================================================================

def latex_to_sympy(latex: str) -> str:
    """
    Convert LaTeX notation to SymPy-parseable format.

    Examples:
        \\frac{1}{2} → (1)/(2)
        \\sqrt{x} → sqrt(x)
        \\pi → pi
        3\\sqrt{2} → 3*sqrt(2)
    """
    s = latex.strip()

    # Remove $ delimiters
    s = s.strip('$')

    # Remove \left and \right
    s = s.replace(r'\left', '').replace(r'\right', '')

    # \frac{a}{b} → (a)/(b) - handle nested braces
    while r'\frac' in s:
        match = re.search(r'\\frac\s*', s)
        if not match:
            break

        # Find first {
        start = match.end()
        if start >= len(s) or s[start] != '{':
            break

        # Extract numerator (balanced braces)
        num_start = start + 1
        depth = 1
        num_end = num_start
        while num_end < len(s) and depth > 0:
            if s[num_end] == '{':
                depth += 1
            elif s[num_end] == '}':
                depth -= 1
            num_end += 1

        if depth != 0:
            break

        numerator = s[num_start:num_end - 1]

        # Extract denominator
        denom_start = num_end
        if denom_start >= len(s) or s[denom_start] != '{':
            break

        denom_start += 1
        depth = 1
        denom_end = denom_start
        while denom_end < len(s) and depth > 0:
            if s[denom_end] == '{':
                depth += 1
            elif s[denom_end] == '}':
                depth -= 1
            denom_end += 1

        if depth != 0:
            break

        denominator = s[denom_start:denom_end - 1]

        # Replace
        s = s[:match.start()] + f'(({numerator})/({denominator}))' + s[denom_end:]

    # \sqrt[n]{x} → x**(1/n)
    s = re.sub(r'\\sqrt\[([^\]]+)\]\{([^}]+)\}', r'((\2))**(1/(\1))', s)

    # \sqrt{x} → sqrt(x)
    while r'\sqrt' in s:
        match = re.search(r'\\sqrt\s*\{', s)
        if not match:
            break

        start = match.end()
        depth = 1
        end = start
        while end < len(s) and depth > 0:
            if s[end] == '{':
                depth += 1
            elif s[end] == '}':
                depth -= 1
            end += 1

        if depth == 0:
            content = s[start:end - 1]
            s = s[:match.start()] + f'sqrt({content})' + s[end:]
        else:
            break

    # Trig and log functions
    for func in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc',
                 'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh',
                 'log', 'ln', 'exp']:
        s = s.replace(f'\\{func}', func)

    # \ln → log (SymPy uses log for natural log)
    s = s.replace('ln(', 'log(')

    # Greek letters
    s = s.replace(r'\pi', 'pi')
    s = s.replace('π', 'pi')
    s = s.replace(r'\theta', 'theta')
    s = s.replace(r'\alpha', 'alpha')
    s = s.replace(r'\beta', 'beta')
    s = s.replace(r'\gamma', 'gamma')
    s = s.replace(r'\infty', 'oo')
    s = s.replace('∞', 'oo')

    # Operators
    s = s.replace(r'\cdot', '*')
    s = s.replace(r'\times', '*')
    s = s.replace(r'\div', '/')
    s = s.replace(r'\pm', '±')

    # Remove text commands
    s = re.sub(r'\\text\s*\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathrm\s*\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\textbf\s*\{([^}]*)\}', r'\1', s)

    # Exponents: ^{...} → **(...) or ^x → **x
    s = re.sub(r'\^{([^}]+)}', r'**(\1)', s)
    s = re.sub(r'\^(\d+)', r'**\1', s)
    s = re.sub(r'\^([a-zA-Z])', r'**\1', s)

    # Remove formatting
    s = s.replace(r'\,', '')
    s = s.replace(r'\;', '')
    s = s.replace(r'\!', '')
    s = s.replace(r'\ ', '')
    s = s.replace(r'\quad', '')
    s = s.replace(r'\qquad', '')

    # Clean up remaining backslashes
    s = re.sub(r'\\[a-zA-Z]+', '', s)

    # Remove spaces around operators for cleaner parsing
    s = re.sub(r'\s*([+\-*/^])\s*', r'\1', s)

    return s.strip()


# =============================================================================
# EXPRESSION PARSING
# =============================================================================

def parse_expression(expr_str: str) -> Optional[sp.Expr]:
    """
    Parse a string expression into SymPy.
    Tries multiple parsing strategies.
    """
    if not expr_str or not expr_str.strip():
        return None

    # Clean input
    s = expr_str.strip()

    # Convert LaTeX to SymPy format
    s = latex_to_sympy(s)

    # Additional cleanup
    s = s.replace('^', '**')

    # Try parsing
    try:
        return parse_expr(s, local_dict=SYMBOLS, transformations=TRANSFORMATIONS)
    except:
        pass

    # Try with implicit multiplication disabled
    try:
        return parse_expr(s, local_dict=SYMBOLS, transformations=standard_transformations)
    except:
        pass

    # Try SymPy's sympify
    try:
        return sp.sympify(s, locals=SYMBOLS)
    except:
        pass

    return None


def parse_set_or_list(expr_str: str) -> Optional[List[sp.Expr]]:
    """
    Parse a set or list of expressions.
    Handles formats like: {1, 2, 3}, [1, 2, 3], 1, 2, 3, x = 1 or x = 2
    """
    if not expr_str:
        return None

    s = expr_str.strip()

    # Remove outer brackets/braces
    s = s.strip('{}[]()$')

    # Handle "x = a, x = b" or "x = a or x = b" format
    s = re.sub(r'[a-zA-Z]\s*=\s*', '', s)
    s = s.replace(' or ', ',')
    s = s.replace(' and ', ',')

    # Split by comma
    parts = [p.strip() for p in s.split(',') if p.strip()]

    result = []
    for part in parts:
        parsed = parse_expression(part)
        if parsed is not None:
            result.append(parsed)

    return result if result else None


# =============================================================================
# EQUIVALENCE CHECKING
# =============================================================================

def check_symbolic_equivalence(expr1: sp.Expr, expr2: sp.Expr) -> Tuple[bool, str]:
    """
    Check if two SymPy expressions are mathematically equivalent.
    Returns (is_equivalent, method_used).
    """
    # Direct equality
    if expr1 == expr2:
        return True, "direct_equality"

    # Try simplify(expr1 - expr2) == 0
    try:
        diff = sp.simplify(expr1 - expr2)
        if diff == 0:
            return True, "simplify_diff"
    except:
        pass

    # Try expand and compare
    try:
        if sp.expand(expr1) == sp.expand(expr2):
            return True, "expand"
    except:
        pass

    # Try trigsimp
    try:
        if sp.trigsimp(expr1) == sp.trigsimp(expr2):
            return True, "trigsimp"
    except:
        pass

    # Try equals method
    try:
        if expr1.equals(expr2):
            return True, "equals_method"
    except:
        pass

    return False, "not_equivalent"


def check_numeric_equivalence(expr1: sp.Expr, expr2: sp.Expr) -> Tuple[bool, str]:
    """
    Check equivalence by numeric evaluation at multiple points.
    Fallback when symbolic methods fail.
    """
    # Get free symbols
    symbols1 = expr1.free_symbols
    symbols2 = expr2.free_symbols

    # If no free symbols, evaluate directly
    if not symbols1 and not symbols2:
        try:
            val1 = complex(expr1.evalf())
            val2 = complex(expr2.evalf())
            if abs(val1 - val2) < NUMERIC_TOLERANCE:
                return True, "numeric_constant"
        except:
            pass
        return False, "numeric_fail"

    # Must have same free symbols
    if symbols1 != symbols2:
        # Try anyway with union of symbols
        all_symbols = symbols1 | symbols2

    else:
        all_symbols = symbols1

    if not all_symbols:
        return False, "no_symbols"

    # Test at multiple points
    symbol_list = list(all_symbols)
    all_match = True

    for test_val in TEST_POINTS:
        try:
            subs = {s: test_val for s in symbol_list}
            val1 = complex(expr1.subs(subs).evalf())
            val2 = complex(expr2.subs(subs).evalf())

            if abs(val1 - val2) > NUMERIC_TOLERANCE:
                all_match = False
                break
        except:
            continue

    if all_match:
        return True, "numeric_eval"

    return False, "numeric_mismatch"


def check_set_equivalence(set1: List[sp.Expr], set2: List[sp.Expr]) -> Tuple[bool, str]:
    """
    Check if two sets of expressions are equivalent (order-independent).
    For equation solutions, roots, etc.
    """
    if len(set1) != len(set2):
        return False, f"size_mismatch ({len(set1)} vs {len(set2)})"

    # Try to match each element in set1 to an element in set2
    matched = [False] * len(set2)

    for expr1 in set1:
        found_match = False
        for i, expr2 in enumerate(set2):
            if matched[i]:
                continue

            # Check equivalence
            is_eq, _ = check_symbolic_equivalence(expr1, expr2)
            if not is_eq:
                is_eq, _ = check_numeric_equivalence(expr1, expr2)

            if is_eq:
                matched[i] = True
                found_match = True
                break

        if not found_match:
            return False, f"no_match_for_{expr1}"

    if all(matched):
        return True, "set_match"

    return False, "partial_match"


# =============================================================================
# MAIN EVALUATOR
# =============================================================================

def evaluate(predicted: str, ground_truth: str) -> EvalResult:
    """
    Main evaluation function.
    Compares predicted answer to ground truth using SymPy.

    Args:
        predicted: The model's predicted answer
        ground_truth: The correct answer

    Returns:
        EvalResult with equivalence status, method used, and details
    """
    # Handle empty inputs
    if not predicted or not predicted.strip():
        return EvalResult(
            is_equivalent=False,
            method='failed',
            details='empty_prediction',
        )

    if not ground_truth or not ground_truth.strip():
        return EvalResult(
            is_equivalent=False,
            method='failed',
            details='empty_ground_truth',
        )

    pred_clean = predicted.strip()
    gt_clean = ground_truth.strip()

    # Detect if this is a set/list answer
    is_set_pred = any(c in pred_clean for c in '{}[]') or ',' in pred_clean or ' or ' in pred_clean.lower()
    is_set_gt = any(c in gt_clean for c in '{}[]') or ',' in gt_clean or ' or ' in gt_clean.lower()

    # Handle set/list answers
    if is_set_pred or is_set_gt:
        pred_set = parse_set_or_list(pred_clean)
        gt_set = parse_set_or_list(gt_clean)

        if pred_set and gt_set:
            is_eq, method = check_set_equivalence(pred_set, gt_set)
            return EvalResult(
                is_equivalent=is_eq,
                method=f'set_{method}',
                details=f'pred={[str(e) for e in pred_set]}, gt={[str(e) for e in gt_set]}',
                predicted_parsed=str(pred_set),
                ground_truth_parsed=str(gt_set),
            )

    # Parse as single expressions
    pred_expr = parse_expression(pred_clean)
    gt_expr = parse_expression(gt_clean)

    if pred_expr is None:
        return EvalResult(
            is_equivalent=False,
            method='failed',
            details=f'cannot_parse_prediction: {pred_clean}',
        )

    if gt_expr is None:
        return EvalResult(
            is_equivalent=False,
            method='failed',
            details=f'cannot_parse_ground_truth: {gt_clean}',
        )

    # Try symbolic equivalence
    is_eq, method = check_symbolic_equivalence(pred_expr, gt_expr)
    if is_eq:
        return EvalResult(
            is_equivalent=True,
            method=f'symbolic_{method}',
            details=f'pred={pred_expr}, gt={gt_expr}',
            predicted_parsed=str(pred_expr),
            ground_truth_parsed=str(gt_expr),
        )

    # Fallback to numeric
    is_eq, method = check_numeric_equivalence(pred_expr, gt_expr)
    return EvalResult(
        is_equivalent=is_eq,
        method=f'numeric_{method}' if is_eq else 'not_equivalent',
        details=f'pred={pred_expr}, gt={gt_expr}',
        predicted_parsed=str(pred_expr),
        ground_truth_parsed=str(gt_expr),
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def is_correct(predicted: str, ground_truth: str) -> bool:
    """Simple wrapper that returns True/False."""
    result = evaluate(predicted, ground_truth)
    return result.is_equivalent


def batch_evaluate(pairs: List[Tuple[str, str]]) -> List[EvalResult]:
    """Evaluate multiple (predicted, ground_truth) pairs."""
    return [evaluate(pred, gt) for pred, gt in pairs]


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Basic equivalence
        ("3*x^2", "3x^2", True),
        ("1/2", r"\frac{1}{2}", True),
        ("x**2 + 2*x + 1", "(x+1)^2", True),

        # Fractions
        ("2/4", "1/2", True),
        (r"\frac{3}{4}", "0.75", True),

        # Square roots
        ("3*sqrt(2)", r"3\sqrt{2}", True),
        ("sqrt(8)", "2*sqrt(2)", True),

        # Trigonometric
        ("sin(x)^2 + cos(x)^2", "1", True),
        ("2*sin(x)*cos(x)", "sin(2*x)", True),

        # Pi
        ("2*pi", r"2\pi", True),
        ("pi/6", r"\frac{\pi}{6}", True),

        # Sets (equation solutions)
        ("-2, 2", "2, -2", True),
        ("{1, 2, 3}", "[3, 1, 2]", True),
        ("x = 2, x = 3", "x = 3, x = 2", True),

        # Different values
        ("3", "4", False),
        ("x + 1", "x + 2", False),
    ]

    print("=" * 60)
    print("EVALUATOR TEST")
    print("=" * 60)

    passed = 0
    for pred, gt, expected in test_cases:
        result = evaluate(pred, gt)
        status = "PASS" if result.is_equivalent == expected else "FAIL"
        if result.is_equivalent == expected:
            passed += 1

        print(f"\n{status}: '{pred}' vs '{gt}'")
        print(f"  Expected: {expected}, Got: {result.is_equivalent}")
        print(f"  Method: {result.method}")
        print(f"  Details: {result.details}")

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{len(test_cases)} passed")
    print("=" * 60)
