"""
Heuristic Loader - Maps topics to solving templates

Supports one-to-many mapping with LLM selection:
    topics → candidate heuristics → LLM selects best → solving template

Usage:
    from topics.heuristic_loader import get_solving_approach

    approach = get_solving_approach(["u_substitution"], problem_text="∫x·e^(x²)dx")
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

# Load mapping at module level (now one-to-many)
_TOPIC_MAPPING: dict[str, list[str]] = {}
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


def get_candidates_for_topics(topics: list[str]) -> list[str]:
    """Get all candidate heuristics for given topics (deduplicated)."""
    candidates = []
    seen = set()

    for topic in topics:
        if topic in _TOPIC_MAPPING:
            for h in _TOPIC_MAPPING[topic]:
                if h not in seen:
                    candidates.append(h)
                    seen.add(h)

    return candidates


def get_heuristic_file(heuristic_name: str) -> Optional[Path]:
    """Get the heuristic file path for a heuristic name."""
    # Try direct match
    file_path = HEURISTICS_DIR / f"{heuristic_name}.md"
    if file_path.exists():
        return file_path

    # Try legacy names (backwards compat)
    legacy_map = {
        "lagrange_multipliers": "constrained_optimization.md",
        "limits": "limits.md",
        "derivatives": "derivatives.md",
        "integration": "integration.md",
        "optimization": "optimization.md",
        "related_rates": "related_rates.md",
    }
    if heuristic_name in legacy_map:
        file_path = HEURISTICS_DIR / legacy_map[heuristic_name]
        if file_path.exists():
            return file_path

    return None


def load_heuristic(heuristic_name: str) -> Optional[str]:
    """Load the full heuristic content by name."""
    file_path = get_heuristic_file(heuristic_name)
    if file_path:
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            pass
    return None


# ============================================================
# LLM Selection (one-to-many → best one)
# ============================================================

SELECTION_PROMPT = '''你是一个微积分老师。

现在给你一道题，以及几个可能的解题方法，请选择最合适的一个。

候选方法：
{candidates}

要求：
1. 只返回一个方法名称（必须从候选列表中选）
2. 不要解释
3. 不要输出多余内容

题目：
{problem_text}

输出（只输出方法名）：'''


def _get_selection_llm():
    """Get LLM for heuristic selection (DeepSeek, cheap)."""
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from claire_agent import get_secret

        deepseek_key = get_secret("DEEPSEEK_API_KEY")
        if deepseek_key:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                temperature=0,
                max_tokens=50,
            )

        anthropic_key = get_secret("ANTHROPIC_API_KEY")
        if anthropic_key:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=anthropic_key,
                temperature=0,
                max_tokens=50,
            )
    except Exception as e:
        print(f"[heuristic_loader] LLM error: {e}")

    return None


def select_best_heuristic(problem_text: str, candidates: list[str]) -> str:
    """
    Use LLM to select the best heuristic from candidates.

    Args:
        problem_text: The problem to solve
        candidates: List of candidate heuristic names

    Returns:
        Best heuristic name (from candidates)
    """
    if not candidates:
        return "derivatives"  # Default

    if len(candidates) == 1:
        return candidates[0]  # No selection needed

    llm = _get_selection_llm()
    if not llm:
        return candidates[0]  # Fallback to first

    # Format candidates for display
    candidates_str = "\n".join(f"- {c}" for c in candidates)

    prompt = SELECTION_PROMPT.format(
        candidates=candidates_str,
        problem_text=problem_text[:500]  # Truncate
    )

    try:
        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        response = result.content.strip().lower().replace(" ", "_")

        # Validate response is in candidates
        for c in candidates:
            if c.lower() in response or response in c.lower():
                return c

        # Partial match
        for c in candidates:
            if any(word in response for word in c.split("_")):
                return c

    except Exception as e:
        print(f"[select_best_heuristic] Error: {e}")

    return candidates[0]  # Fallback


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


def get_solving_approach(topics: list[str], problem_text: str = "") -> dict:
    """
    Get a user-friendly solving approach for given topics.

    Flow:
    1. Get candidate heuristics for all topics
    2. If multiple candidates, use LLM to select best one
    3. Load heuristic and extract steps

    Args:
        topics: List of topic IDs (e.g., ["u_substitution"])
        problem_text: Optional problem text for better selection

    Returns:
        {
            "description": "This problem is about...",
            "steps": ["Step 1...", "Step 2..."],
            "topic": "u_substitution",
            "heuristic": "u_substitution"
        }
    """
    if not topics:
        return {
            "description": "",
            "steps": [],
            "topic": None,
            "heuristic": None
        }

    # Step 1: Get all candidate heuristics
    candidates = get_candidates_for_topics(topics)

    if not candidates:
        # Fallback: use first topic as heuristic name
        candidates = [topics[0]]

    # Step 2: Select best heuristic
    if len(candidates) == 1:
        best_heuristic = candidates[0]
    elif problem_text:
        best_heuristic = select_best_heuristic(problem_text, candidates)
    else:
        best_heuristic = candidates[0]

    # Step 3: Load heuristic content
    heuristic_content = load_heuristic(best_heuristic)
    steps = extract_solving_template(heuristic_content) if heuristic_content else []

    # Fallback steps
    if not steps:
        steps = _get_fallback_steps(best_heuristic)

    # Get description from first topic
    main_topic = topics[0]
    description = f"This problem is about {get_topic_description(main_topic)}."

    return {
        "description": description,
        "steps": steps,
        "topic": main_topic,
        "heuristic": best_heuristic
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
