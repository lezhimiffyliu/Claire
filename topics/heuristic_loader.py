"""
Heuristic Loader - Maps topics to solving templates

This module provides the bridge between:
- Fine-grained topic detection
- Solving heuristics/templates

Usage:
    from topics.heuristic_loader import get_solving_approach

    approach = get_solving_approach(["lagrange_multipliers"])
    # Returns user-friendly solving steps
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional

# Paths
MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = MODULE_DIR.parent
MAPPING_FILE = MODULE_DIR / "topic_to_heuristic.json"
HEURISTICS_DIR = PROJECT_ROOT / "heuristics"

# Load mapping at module level
_TOPIC_MAPPING = {}
try:
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        _TOPIC_MAPPING = json.load(f)
        # Remove comment key
        _TOPIC_MAPPING.pop("_comment", None)
except Exception as e:
    print(f"[heuristic_loader] Warning: Could not load mapping: {e}")


# User-friendly topic descriptions (for UI)
TOPIC_DESCRIPTIONS = {
    "lagrange_multipliers": "optimizing a function under a constraint",
    "constrained_optimization": "optimizing with constraints",
    "u_substitution": "integration using substitution",
    "integration_by_parts": "integration using the parts formula",
    "partial_fractions": "integration by decomposing fractions",
    "related_rates": "finding how quantities change together over time",
    "chain_rule": "differentiating composite functions",
    "implicit_differentiation": "differentiating implicitly defined functions",
    "critical_points": "finding where a function has local extrema",
    "lhopitals_rule": "evaluating indeterminate limits",
    "taylor_series": "approximating functions with polynomials",
    "double_integrals_rectangular": "integrating over a 2D region",
    "double_integrals_polar": "integrating in polar coordinates",
    "gradient": "finding the direction of steepest increase",
    "directional_derivative": "finding the rate of change in a direction",
}


def get_heuristic_file(topic: str) -> Optional[Path]:
    """Get the heuristic file path for a topic."""
    if topic in _TOPIC_MAPPING:
        rel_path = _TOPIC_MAPPING[topic]
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            return full_path
    return None


def load_heuristic(topic: str) -> Optional[str]:
    """Load the full heuristic content for a topic."""
    file_path = get_heuristic_file(topic)
    if file_path:
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            pass
    return None


def extract_solving_template(heuristic_content: str) -> list[str]:
    """
    Extract the solving steps from heuristic content.

    Looks for:
    - ## Solving Template
    - ## Steps
    - Numbered lists (1. 2. 3.)
    """
    if not heuristic_content:
        return []

    lines = heuristic_content.split('\n')
    steps = []
    in_template = False

    for line in lines:
        # Start of template section
        if re.match(r'^##\s*(Solving Template|Steps|How to Solve)', line, re.IGNORECASE):
            in_template = True
            continue

        # End of template section (new ## header)
        if in_template and line.startswith('## '):
            break

        if in_template:
            # Extract numbered steps
            step_match = re.match(r'^\s*(\d+)[.)\s]+(.+)', line)
            if step_match:
                step_text = step_match.group(2).strip()
                # Clean up markdown formatting
                step_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', step_text)  # Remove bold
                step_text = re.sub(r'\$([^$]+)\$', r'\1', step_text)  # Keep math but remove $
                if step_text:
                    steps.append(step_text)

    return steps[:6]  # Max 6 steps


def get_topic_description(topic: str) -> str:
    """Get a user-friendly description of what the topic is about."""
    if topic in TOPIC_DESCRIPTIONS:
        return TOPIC_DESCRIPTIONS[topic]

    # Generate from topic name
    return topic.replace("_", " ")


def get_solving_approach(topics: list[str]) -> dict:
    """
    Get a user-friendly solving approach for given topics.

    Args:
        topics: List of topic IDs (e.g., ["lagrange_multipliers"])

    Returns:
        {
            "description": "This problem is about...",
            "steps": ["Step 1...", "Step 2..."],
            "topic": "lagrange_multipliers"
        }
    """
    if not topics:
        return {
            "description": "",
            "steps": [],
            "topic": None
        }

    # Use first topic
    main_topic = topics[0]

    # Get description
    description = f"This problem is about {get_topic_description(main_topic)}."

    # Load heuristic and extract steps
    heuristic = load_heuristic(main_topic)
    steps = extract_solving_template(heuristic) if heuristic else []

    # Fallback steps if none found
    if not steps:
        steps = _get_fallback_steps(main_topic)

    return {
        "description": description,
        "steps": steps,
        "topic": main_topic
    }


def _get_fallback_steps(topic: str) -> list[str]:
    """Provide fallback steps for common topics."""
    FALLBACK_STEPS = {
        "lagrange_multipliers": [
            "Identify the objective function f(x,y) to optimize",
            "Identify the constraint g(x,y) = c",
            "Set up: ∇f = λ∇g and g = c",
            "Solve the system of equations",
            "Compare values to find max/min"
        ],
        "u_substitution": [
            "Identify the inner function u = g(x)",
            "Compute du = g'(x)dx",
            "Rewrite integral in terms of u",
            "Integrate with respect to u",
            "Substitute back to get answer in terms of x"
        ],
        "integration_by_parts": [
            "Choose u and dv (LIATE rule)",
            "Compute du and v",
            "Apply formula: ∫udv = uv - ∫vdu",
            "Evaluate the remaining integral",
            "Add +C for indefinite integrals"
        ],
        "related_rates": [
            "Draw a diagram and label variables",
            "Write an equation relating the quantities",
            "Differentiate both sides with respect to time t",
            "Substitute known values",
            "Solve for the unknown rate"
        ],
        "critical_points": [
            "Find f'(x) or ∇f",
            "Set derivative(s) equal to zero",
            "Solve for critical points",
            "Use first or second derivative test",
            "Classify as max, min, or saddle"
        ],
        "double_integrals_polar": [
            "Convert to polar: x = rcosθ, y = rsinθ",
            "Convert dA to r dr dθ",
            "Determine limits for r and θ",
            "Set up the integral",
            "Evaluate inner then outer integral"
        ],
    }

    return FALLBACK_STEPS.get(topic, [
        "Identify the type of problem",
        "Set up the relevant equations",
        "Apply the appropriate technique",
        "Solve step by step",
        "Check your answer"
    ])


def format_approach_for_display(approach: dict) -> str:
    """
    Format the approach as a markdown string for display.

    This is what gets shown to the user (NOT the raw heuristic).
    """
    lines = []

    if approach.get("description"):
        lines.append(f"**{approach['description']}**")
        lines.append("")

    if approach.get("steps"):
        lines.append("**Approach:**")
        for i, step in enumerate(approach["steps"], 1):
            lines.append(f"{i}. {step}")

    return "\n".join(lines)


# ============================================================
# Batch Operations
# ============================================================

def get_approaches_for_questions(questions: list) -> list[dict]:
    """
    Get solving approaches for multiple questions.

    Args:
        questions: List of Question objects with .topics attribute

    Returns:
        List of approach dicts
    """
    approaches = []
    for q in questions:
        topics = getattr(q, "topics", [])
        approach = get_solving_approach(topics)
        approaches.append(approach)
    return approaches
