"""
Pattern detection and heuristic retrieval for Claire 2.0.

Two-stage pattern detection:
1. Keyword-based (fast, for real-time use)
2. LLM-based (accurate, for batch processing or uncertain cases)
"""

import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Available patterns (must match filenames in heuristics/)
# COARSE patterns (legacy, still used for heuristic file lookup)
COARSE_PATTERNS = [
    "optimization",
    "constrained_optimization",
    "related_rates",
    "derivatives",
    "integration",
    "limits",
]

# FINE-GRAINED patterns for diagnostic method-choice questions
# These map to specific solving methods rather than broad categories
FINE_PATTERNS = [
    # Multivariable calculus
    "directional_derivative",
    "gradient",
    "tangent_plane",
    "partial_derivatives",
    "lagrange_multipliers",

    # Optimization
    "critical_points",
    "critical_points_multivariable",
    "second_derivative_test",
    "absolute_extrema",
    "extrema_on_bounded_region",  # Composite: interior + boundary analysis

    # Integration techniques
    "u_substitution",
    "integration_by_parts",
    "partial_fractions",
    "trig_substitution",
    "double_integrals",
    "triple_integrals",
    "improper_integrals",

    # Derivatives
    "chain_rule",
    "product_rule",
    "quotient_rule",
    "implicit_differentiation",

    # Related rates
    "related_rates",

    # Limits
    "limits",
    "lhopitals_rule",

    # Series
    "taylor_series",
    "power_series",
    "convergence_tests",
]

# For backwards compatibility
PATTERNS = COARSE_PATTERNS

HEURISTICS_DIR = Path(__file__).parent / "heuristics"

# Pattern descriptions for LLM classification (coarse)
PATTERN_DESCRIPTIONS = {
    "optimization": "Finding maximum or minimum values of a function (no constraints)",
    "constrained_optimization": "Optimization with constraints (Lagrange multipliers, subject to equations)",
    "related_rates": "Rates of change with respect to time (how fast something changes)",
    "derivatives": "Finding derivatives, differentiation rules, tangent lines, slopes",
    "integration": "Finding integrals, antiderivatives, area calculations",
    "limits": "Evaluating limits, L'Hopital's rule, continuity",
}

# Fine-grained pattern descriptions (for diagnostic accuracy)
FINE_PATTERN_DESCRIPTIONS = {
    # Multivariable
    "directional_derivative": "Rate of change in a specific direction (uses gradient dot unit vector)",
    "gradient": "Vector of partial derivatives, direction of steepest ascent",
    "tangent_plane": "Linear approximation to surface at a point",
    "partial_derivatives": "Derivatives with respect to one variable, holding others constant",
    "lagrange_multipliers": "Optimization with equality constraints using ∇f = λ∇g",

    # Optimization
    "critical_points": "Points where f'(x) = 0 or undefined",
    "critical_points_multivariable": "Points where ∇f = 0, classified using Hessian/discriminant",
    "second_derivative_test": "Using f'' or discriminant D to classify critical points",
    "absolute_extrema": "Global max/min on closed interval (1D)",
    "extrema_on_bounded_region": "Find extrema on closed 2D region: interior critical points + boundary analysis + compare all",

    # Integration
    "u_substitution": "Integral of composite function f(g(x))·g'(x)",
    "integration_by_parts": "Integral of product using ∫udv = uv - ∫vdu",
    "partial_fractions": "Decomposing rational functions for integration",
    "trig_substitution": "Using x = a·sin(θ) etc. for √(a²±x²) forms",
    "double_integrals": "Integration over 2D regions",
    "triple_integrals": "Integration over 3D regions",
    "improper_integrals": "Integrals with infinite limits or discontinuities",

    # Derivatives
    "chain_rule": "Derivative of composition f(g(x))",
    "product_rule": "Derivative of product fg",
    "implicit_differentiation": "Finding dy/dx when y is defined implicitly",

    # Related rates
    "related_rates": "Rates of change with respect to time",

    # Limits
    "limits": "Evaluating limits using algebraic techniques",
    "lhopitals_rule": "L'Hôpital's rule for 0/0 or ∞/∞ forms",

    # Series
    "taylor_series": "Power series expansion of functions",
    "power_series": "Series of the form Σaₙxⁿ",
    "convergence_tests": "Testing series convergence (ratio, root, comparison)",
}

# Keywords for fast detection (coarse patterns)
PATTERN_KEYWORDS = {
    "constrained_optimization": [
        "subject to", "constraint", "given that", "such that",
        "lagrange", "restricted to", "bounded by", "satisfying"
    ],
    "optimization": [
        "maximize", "minimize", "maximum", "minimum",
        "largest", "smallest", "optimize", "optimal",
        "greatest", "least", "extrema", "extreme value"
    ],
    "related_rates": [
        "rate of change", "how fast", "changing",
        "increasing at", "decreasing at", "per second",
        "per minute", "per hour", "velocity", "speed",
        "dv/dt", "dr/dt", "dh/dt", "da/dt", "dx/dt",
        "at what rate", "find the rate", "is sliding",
        "is rising", "is falling", "is growing", "is shrinking"
    ],
    "limits": [
        "limit", "lim", "approaches", "tends to",
        "as x →", "as x->", "l'hopital", "l'hôpital",
        "indeterminate", "continuous at", "→ 0", "→ ∞"
    ],
    "integration": [
        "integrate", "integral", "∫", "antiderivative",
        "area under", "accumulation", "find the integral",
        "indefinite integral", "definite integral", "evaluate the integral",
        "∫", "dx"
    ],
    "derivatives": [
        "derivative", "differentiate", "d/dx", "dy/dx",
        "f'(x)", "f'", "slope of tangent", "tangent line",
        "implicit differentiation", "chain rule", "product rule",
        "quotient rule", "rate of change"
    ],
}

# Keywords for fine-grained pattern detection
FINE_PATTERN_KEYWORDS = {
    # Multivariable - these should be checked BEFORE coarse "derivatives"
    "directional_derivative": [
        "directional derivative", "direction of", "in the direction",
        "rate of change in direction", "d_u f", "d_uf", "∇f · u",
        "unit vector direction"
    ],
    "gradient": [
        "gradient", "∇f", "grad f", "nabla", "steepest ascent",
        "steepest descent", "direction of fastest"
    ],
    "tangent_plane": [
        "tangent plane", "linear approximation", "linearization",
        "approximate using tangent", "plane tangent to"
    ],
    "partial_derivatives": [
        "partial derivative", "∂f/∂x", "∂f/∂y", "∂/∂",
        "fₓ", "fᵧ", "f_x", "f_y", "fxx", "fyy", "fxy",
        "hold constant", "treating y as constant"
    ],
    "lagrange_multipliers": [
        "lagrange", "multiplier", "∇f = λ∇g", "subject to",
        "constraint g", "constrained optimization"
    ],

    # Optimization - Single Variable
    "critical_points": [
        "critical point", "critical number", "f'(x) = 0",
        "where the derivative is zero", "derivative equals zero",
        "stationary point", "find where f' = 0",
        "set the derivative equal to zero"
    ],

    # Optimization - Multivariable
    "critical_points_multivariable": [
        "critical point", "classify the point", "saddle point",
        "local maximum", "local minimum", "discriminant",
        "hessian", "d = fxx·fyy", "fxx fyy fxy", "∇f = 0",
        "gradient equals zero", "f_x = 0 and f_y = 0"
    ],
    "second_derivative_test": [
        "second derivative test", "f''", "concave up", "concave down",
        "discriminant", "d > 0", "d < 0", "classify",
        "f''(c) > 0", "f''(c) < 0", "concavity"
    ],
    "absolute_extrema": [
        "absolute maximum", "absolute minimum", "global max",
        "global min", "closed interval", "on the interval",
        "endpoints", "extreme value theorem", "on [a,b]"
    ],
    # MUST be checked BEFORE lagrange_multipliers and second_derivative_test
    "extrema_on_bounded_region": [
        "over the region bounded by", "on the closed region",
        "on the region bounded", "bounded by the curve",
        "maxima and minima over the region", "extrema on the region",
        "maximum and minimum on the disk", "on the disk",
        "on the triangle", "on the square", "on the rectangle",
        "over the closed region", "inside the region",
        "find the maximum and minimum values on",
        "find maxima and minima of f(x,y)", "find max and min on",
    ],

    # Integration techniques
    "u_substitution": [
        "u-substitution", "u-sub", "let u =", "substitution",
        "change of variables", "u = g(x)", "substitute u",
        "using substitution", "by substitution"
    ],
    "integration_by_parts": [
        "integration by parts", "by parts", "∫udv", "uv - ∫vdu",
        "liate", "tabular method", "∫u dv", "parts formula",
        "choose u and dv"
    ],
    "partial_fractions": [
        "partial fractions", "partial fraction decomposition",
        "factor the denominator", "decompose into", "rational function",
        "a/(x-a) + b/(x-b)", "linear factors"
    ],
    "trig_substitution": [
        "trig substitution", "trigonometric substitution",
        "√(a² - x²)", "√(a² + x²)", "√(x² - a²)",
        "x = a sin", "x = a tan", "x = a sec",
        "sqrt(a^2 - x^2)", "sqrt(a^2 + x^2)", "sqrt(x^2 - a^2)",
        "√(1 - x²)", "√(1 + x²)", "√(x² - 1)"
    ],
    "double_integrals": [
        "double integral", "∬", "dxdy", "dydx", "dA",
        "iterated integral", "region of integration",
        "polar coordinates", "change order of integration",
        "integrate over the region", "area of region",
        "∫∫", "dx dy", "dy dx"
    ],
    "triple_integrals": [
        "triple integral", "∭", "dxdydz", "dV",
        "cylindrical", "spherical", "volume of solid",
        "∫∫∫", "dx dy dz", "cylindrical coordinates",
        "spherical coordinates"
    ],
    "improper_integrals": [
        "improper integral", "∞", "infinity", "converge",
        "diverge", "unbounded", "infinite limit",
        "integral from 1 to infinity", "as b → ∞",
        "does the integral converge"
    ],

    # Derivatives
    "chain_rule": [
        "chain rule", "composite function", "f(g(x))",
        "outer function", "inner function", "composition",
        "derivative of sin(x²)", "derivative of e^(x²)"
    ],
    "product_rule": [
        "product rule", "(fg)'", "f'g + fg'", "derivative of product",
        "differentiate the product", "uv rule"
    ],
    "quotient_rule": [
        "quotient rule", "(f/g)'", "derivative of quotient",
        "differentiate the quotient", "f/g derivative",
        "(f'g - fg')/g²"
    ],
    "implicit_differentiation": [
        "implicit differentiation", "implicitly defined",
        "dy/dx", "find dy/dx", "differentiate implicitly",
        "implicit equation", "x and y equation",
        "differentiate both sides"
    ],

    # Related Rates
    "related_rates": [
        "rate of change", "how fast", "related rates",
        "changing with respect to time", "per second", "per minute",
        "per hour", "at what rate", "find the rate",
        "dv/dt", "dr/dt", "dh/dt", "da/dt", "dx/dt", "dy/dt",
        "is increasing at", "is decreasing at", "is changing at",
        "when x =", "at the instant when", "at the moment",
        "ladder sliding", "water draining", "balloon inflating",
        "shadow lengthening", "distance changing"
    ],

    # Limits - Basic
    "limits": [
        "limit", "lim", "approaches", "tends to", "as x →",
        "as x->", "→ 0", "→ ∞", "one-sided limit",
        "left-hand limit", "right-hand limit", "x → a",
        "continuous at", "discontinuity", "evaluate the limit",
        "find the limit", "does the limit exist"
    ],

    # Limits - L'Hôpital
    "lhopitals_rule": [
        "l'hopital", "l'hôpital", "0/0", "∞/∞",
        "indeterminate form", "indeterminate", "apply l'hopital",
        "use l'hopital", "l'hospital"
    ],

    # Series
    "taylor_series": [
        "taylor series", "taylor polynomial", "taylor expansion",
        "maclaurin"
    ],
    "power_series": [
        "power series", "radius of convergence", "interval of convergence"
    ],
    "convergence_tests": [
        "ratio test", "root test", "comparison test",
        "integral test", "alternating series", "converge", "diverge"
    ],
}


def detect_pattern(problem: str) -> str:
    """
    Classify a calculus problem into a pattern type using keyword matching.

    Fast, rule-based classification for real-time use.

    Args:
        problem: The problem text to classify

    Returns:
        Pattern name (e.g., "optimization", "related_rates")
    """
    problem_lower = problem.lower()

    # Score each pattern
    scores = {}
    for pattern, keywords in PATTERN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in problem_lower)
        if score > 0:
            scores[pattern] = score

    # Special logic: constrained_optimization needs both constraint + optimization keywords
    has_constraint = scores.get("constrained_optimization", 0) > 0
    has_optimization = scores.get("optimization", 0) > 0

    if has_constraint and has_optimization:
        return "constrained_optimization"

    # If we have constrained keywords but no optimization, might still be constrained opt
    if has_constraint and any(kw in problem_lower for kw in ["maximize", "minimize", "max", "min"]):
        return "constrained_optimization"

    # Remove constrained_optimization if no explicit constraint keywords
    if "constrained_optimization" in scores and not has_constraint:
        del scores["constrained_optimization"]

    # Return highest scoring pattern
    if scores:
        return max(scores, key=scores.get)

    # Fallback heuristics
    if "d/d" in problem_lower or "'" in problem:
        return "derivatives"

    return "derivatives"  # Default


def detect_fine_pattern(problem: str) -> str:
    """
    Classify a calculus problem into a FINE-GRAINED pattern type.

    This is more specific than detect_pattern() and is used for
    diagnostic method-choice questions where we need to match
    the exact solving method.

    Args:
        problem: The problem text to classify

    Returns:
        Fine-grained pattern name (e.g., "directional_derivative", "u_substitution")
    """
    problem_lower = problem.lower()

    # ==========================================================================
    # PRIORITY CHECK: Composite patterns that override single-method patterns
    # These must be checked FIRST because they involve multiple techniques
    # ==========================================================================

    # Check for extrema on bounded region (composite: interior + boundary)
    # This pattern should NOT be classified as just "second_derivative_test"
    # or just "lagrange_multipliers" even if those words appear
    bounded_region_keywords = FINE_PATTERN_KEYWORDS.get("extrema_on_bounded_region", [])
    if any(kw in problem_lower for kw in bounded_region_keywords):
        # Verify it's asking for extrema/max/min (not just mentioning a region)
        extrema_words = ["maxim", "minim", "extrema", "largest", "smallest", "max", "min"]
        if any(w in problem_lower for w in extrema_words):
            return "extrema_on_bounded_region"

    # ==========================================================================
    # STANDARD SCORING: Single-method patterns
    # ==========================================================================

    scores = {}
    for pattern, keywords in FINE_PATTERN_KEYWORDS.items():
        # Skip composite patterns (already handled above)
        if pattern == "extrema_on_bounded_region":
            continue

        score = sum(1 for kw in keywords if kw in problem_lower)
        if score > 0:
            # Weight longer keyword matches higher (more specific)
            weighted_score = score + sum(
                len(kw) / 10 for kw in keywords if kw in problem_lower
            )
            scores[pattern] = weighted_score

    # Return highest scoring fine pattern if any
    if scores:
        best_fine = max(scores, key=scores.get)
        # Only return if we have reasonable confidence (score > 0.5)
        if scores[best_fine] > 0.5:
            return best_fine

    # Fall back to coarse pattern detection
    coarse = detect_pattern(problem)

    # Map coarse patterns to most common fine pattern
    COARSE_TO_FINE_DEFAULT = {
        "optimization": "critical_points",
        "constrained_optimization": "lagrange_multipliers",
        "related_rates": "related_rates",
        "derivatives": "chain_rule",  # Most common derivative issue
        "integration": "u_substitution",  # Most common technique
        "limits": "limits",
    }

    return COARSE_TO_FINE_DEFAULT.get(coarse, coarse)


def fine_to_coarse_pattern(fine_pattern: str) -> str:
    """
    Map a fine-grained pattern to its coarse category.

    Used for looking up heuristic files (which use coarse names).
    """
    FINE_TO_COARSE = {
        # Multivariable -> derivatives (but has own heuristics)
        "directional_derivative": "derivatives",
        "gradient": "derivatives",
        "tangent_plane": "derivatives",
        "partial_derivatives": "derivatives",
        "lagrange_multipliers": "constrained_optimization",

        # Optimization
        "critical_points": "optimization",
        "critical_points_multivariable": "optimization",
        "second_derivative_test": "optimization",
        "absolute_extrema": "optimization",
        "extrema_on_bounded_region": "optimization",

        # Integration
        "u_substitution": "integration",
        "integration_by_parts": "integration",
        "partial_fractions": "integration",
        "trig_substitution": "integration",
        "double_integrals": "integration",
        "triple_integrals": "integration",
        "improper_integrals": "integration",

        # Derivatives
        "chain_rule": "derivatives",
        "product_rule": "derivatives",
        "quotient_rule": "derivatives",
        "implicit_differentiation": "derivatives",

        # Direct mappings
        "related_rates": "related_rates",
        "limits": "limits",
        "lhopitals_rule": "limits",

        # Series
        "taylor_series": "limits",  # Often covered in limits heuristics
        "power_series": "limits",
        "convergence_tests": "limits",
    }

    return FINE_TO_COARSE.get(fine_pattern, fine_pattern)


def get_heuristic_for_fine_pattern(fine_pattern: str) -> str:
    """
    Get the heuristic file path for a fine-grained pattern.

    Some fine patterns have their own heuristic files (e.g., u_substitution.md),
    others fall back to the coarse category file.
    """
    # Check if fine pattern has its own heuristic file
    fine_heuristic_path = HEURISTICS_DIR / f"{fine_pattern}.md"
    if fine_heuristic_path.exists():
        return str(fine_heuristic_path)

    # Fall back to coarse pattern
    coarse = fine_to_coarse_pattern(fine_pattern)
    return str(HEURISTICS_DIR / f"{coarse}.md")


def detect_pattern_llm(problem: str, llm=None) -> str:
    """
    Classify a calculus problem using LLM for higher accuracy.

    Use this for batch processing or when keyword detection is uncertain.

    Args:
        problem: The problem text to classify
        llm: Optional LLM instance (will create one if not provided)

    Returns:
        Pattern name
    """
    if llm is None:
        try:
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return detect_pattern(problem)  # Fallback to keyword-based

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                temperature=0,
                max_tokens=50,
            )
        except Exception:
            return detect_pattern(problem)

    # Build classification prompt
    pattern_list = "\n".join(f"- {p}: {PATTERN_DESCRIPTIONS[p]}" for p in PATTERNS)

    prompt = f"""Classify this calculus problem into exactly ONE of these pattern types:

{pattern_list}

Problem: {problem}

Reply with ONLY the pattern name (e.g., "optimization" or "related_rates"). Nothing else."""

    try:
        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        response = result.content.strip().lower().replace(" ", "_")

        # Validate response
        if response in PATTERNS:
            return response

        # Try to match partial
        for p in PATTERNS:
            if p in response:
                return p

        return detect_pattern(problem)  # Fallback

    except Exception:
        return detect_pattern(problem)


def detect_patterns_batch(problems: list[str], use_llm: bool = False) -> list[str]:
    """
    Classify multiple problems efficiently.

    Args:
        problems: List of problem texts
        use_llm: Whether to use LLM for classification

    Returns:
        List of pattern names
    """
    if not use_llm:
        return [detect_pattern(p) for p in problems]

    # For LLM, reuse the same instance
    try:
        from langchain_anthropic import ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return [detect_pattern(p) for p in problems]

        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0,
            max_tokens=50,
        )

        return [detect_pattern_llm(p, llm) for p in problems]

    except Exception:
        return [detect_pattern(p) for p in problems]


def get_available_patterns() -> list[str]:
    """Return list of available pattern types."""
    return PATTERNS.copy()


def get_pattern_description(pattern: str) -> str:
    """Get description for a pattern."""
    return PATTERN_DESCRIPTIONS.get(pattern, "")


@tool
def get_heuristic(pattern: str) -> str:
    """
    Load the solving heuristic for a calculus pattern type.

    Use this tool to retrieve the step-by-step solving template
    for a specific type of calculus problem. The heuristic includes:
    - Pattern recognition tips
    - Decision tree for approach selection
    - Solving template with numbered steps
    - Common mistakes to avoid

    Args:
        pattern: The pattern type. Must be one of:
                 optimization, constrained_optimization, related_rates,
                 derivatives, integration, limits

    Returns:
        The heuristic content in markdown format
    """
    # Normalize pattern name
    pattern = pattern.lower().strip().replace(" ", "_").replace("-", "_")

    # Check if pattern is valid
    if pattern not in PATTERNS:
        available = ", ".join(PATTERNS)
        return f"Unknown pattern: '{pattern}'. Available patterns: {available}"

    # Load heuristic file
    heuristic_path = HEURISTICS_DIR / f"{pattern}.md"

    if not heuristic_path.exists():
        return f"Heuristic file not found for pattern: {pattern}"

    try:
        content = heuristic_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"Error loading heuristic: {e}"


# Export the tool for use in agent
PATTERN_TOOLS = [get_heuristic]
