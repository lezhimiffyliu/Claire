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
PATTERNS = [
    "optimization",
    "constrained_optimization",
    "related_rates",
    "derivatives",
    "integration",
    "limits",
]

HEURISTICS_DIR = Path(__file__).parent / "heuristics"

# Pattern descriptions for LLM classification
PATTERN_DESCRIPTIONS = {
    "optimization": "Finding maximum or minimum values of a function (no constraints)",
    "constrained_optimization": "Optimization with constraints (Lagrange multipliers, subject to equations)",
    "related_rates": "Rates of change with respect to time (how fast something changes)",
    "derivatives": "Finding derivatives, differentiation rules, tangent lines, slopes",
    "integration": "Finding integrals, antiderivatives, area calculations",
    "limits": "Evaluating limits, L'Hopital's rule, continuity",
}

# Keywords for fast detection
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
