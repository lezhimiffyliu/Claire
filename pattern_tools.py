"""
Pattern detection and heuristic retrieval for Claire 2.0.
"""

import os
from pathlib import Path
from langchain_core.tools import tool

# Available patterns (must match filenames in heuristics/)
PATTERNS = [
    "optimization",
    "constrained_optimization",
    "related_rates",
    "derivatives",
    "integration",
    "limits",
]

HEURISTICS_DIR = Path(__file__).parent / "heuristics"


def detect_pattern(problem: str) -> str:
    """
    Classify a calculus problem into a pattern type.

    This is a rule-based classifier using keyword matching.
    Returns one of the known pattern types.

    Args:
        problem: The problem text to classify

    Returns:
        Pattern name (e.g., "optimization", "related_rates")
    """
    problem_lower = problem.lower()

    # Constrained optimization (check before general optimization)
    constrained_keywords = [
        "subject to", "constraint", "given that", "such that",
        "lagrange", "restricted to", "bounded by"
    ]
    optimization_keywords = [
        "maximize", "minimize", "maximum", "minimum",
        "largest", "smallest", "optimize", "optimal",
        "greatest", "least"
    ]

    has_constraint = any(kw in problem_lower for kw in constrained_keywords)
    has_optimization = any(kw in problem_lower for kw in optimization_keywords)

    if has_constraint and has_optimization:
        return "constrained_optimization"

    # Related rates
    related_rates_keywords = [
        "rate of change", "how fast", "changing",
        "increasing at", "decreasing at", "per second",
        "per minute", "per hour", "velocity", "speed",
        "dv/dt", "dr/dt", "dh/dt", "da/dt",
        "at what rate", "find the rate"
    ]
    if any(kw in problem_lower for kw in related_rates_keywords):
        return "related_rates"

    # Unconstrained optimization
    if has_optimization:
        return "optimization"

    # Limits
    limit_keywords = [
        "limit", "lim", "approaches", "tends to",
        "as x →", "as x->", "l'hopital", "l'hôpital",
        "indeterminate", "continuous at"
    ]
    if any(kw in problem_lower for kw in limit_keywords):
        return "limits"

    # Integration
    integration_keywords = [
        "integrate", "integral", "∫", "antiderivative",
        "area under", "accumulation", "find the integral",
        "indefinite", "definite integral", "evaluate the integral"
    ]
    if any(kw in problem_lower for kw in integration_keywords):
        return "integration"

    # Derivatives (default for differentiation-related problems)
    derivative_keywords = [
        "derivative", "differentiate", "d/dx", "dy/dx",
        "f'(x)", "f'", "slope of tangent", "rate of change",
        "implicit differentiation", "chain rule", "product rule"
    ]
    if any(kw in problem_lower for kw in derivative_keywords):
        return "derivatives"

    # Default: try to infer from mathematical expressions
    if "d/d" in problem_lower or "'" in problem:
        return "derivatives"

    # Fallback
    return "derivatives"


def get_available_patterns() -> list[str]:
    """Return list of available pattern types."""
    return PATTERNS.copy()


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
