"""
Exam Panic Mode - Core feature of Claire

Takes uploaded materials → generates study strategy

NO over-engineering. Simple aggregation + output.
"""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExamSummary:
    """Output of exam analysis."""
    top_topics: list[tuple[str, int]]  # (topic_id, count)
    topic_counts: dict[str, int]
    focus_advice: list[dict]  # [{topic, display_name, steps}]
    cram_plan: list[dict]  # [{day, topics}]
    total_questions: int = 0


# Display names for topics (user-friendly)
TOPIC_DISPLAY = {
    "u_substitution": "U-Substitution",
    "integration_by_parts": "Integration by Parts",
    "partial_fractions": "Partial Fractions",
    "trig_substitution": "Trig Substitution",
    "taylor_series": "Taylor Series",
    "maclaurin_series": "Maclaurin Series",
    "power_series": "Power Series",
    "lagrange_multipliers": "Lagrange Multipliers",
    "constrained_optimization": "Constrained Optimization",
    "critical_points": "Critical Points",
    "related_rates": "Related Rates",
    "chain_rule": "Chain Rule",
    "implicit_differentiation": "Implicit Differentiation",
    "double_integrals_rectangular": "Double Integrals",
    "double_integrals_polar": "Double Integrals (Polar)",
    "triple_integrals_rectangular": "Triple Integrals",
    "gradient": "Gradient",
    "directional_derivative": "Directional Derivative",
    "ratio_test": "Ratio Test",
    "comparison_test": "Comparison Test",
    "lhopitals_rule": "L'Hôpital's Rule",
    "improper_integrals": "Improper Integrals",
    "volume_disk_method": "Volume (Disk/Washer)",
    "volume_shell_method": "Volume (Shell)",
    "arc_length": "Arc Length",
    "greens_theorem": "Green's Theorem",
    "stokes_theorem": "Stokes' Theorem",
    "divergence_theorem": "Divergence Theorem",
}


def get_display_name(topic_id: str) -> str:
    """Get user-friendly name for a topic."""
    if topic_id in TOPIC_DISPLAY:
        return TOPIC_DISPLAY[topic_id]
    return topic_id.replace("_", " ").title()


# Quick solving tips (embedded, no complex loading)
QUICK_TIPS = {
    "u_substitution": [
        "Identify inner function u = g(x)",
        "Compute du = g'(x)dx",
        "Rewrite integral in terms of u",
        "Integrate and substitute back",
    ],
    "integration_by_parts": [
        "Use LIATE to choose u (Log, Inverse trig, Algebraic, Trig, Exp)",
        "Apply ∫udv = uv - ∫vdu",
        "Simplify the remaining integral",
    ],
    "partial_fractions": [
        "Factor the denominator",
        "Set up A/(x-a) + B/(x-b) form",
        "Solve for constants",
        "Integrate each term",
    ],
    "taylor_series": [
        "Recall standard series (eˣ, sin, cos, 1/(1-x))",
        "Match function to standard form",
        "Substitute and simplify",
    ],
    "lagrange_multipliers": [
        "Identify f (objective) and g (constraint)",
        "Set up ∇f = λ∇g",
        "Solve system with g = c",
        "Compare values at solutions",
    ],
    "related_rates": [
        "Draw diagram, label variables",
        "Write equation relating quantities",
        "Differentiate with respect to t",
        "Substitute known values, solve",
    ],
    "double_integrals_rectangular": [
        "Sketch the region",
        "Choose order (dydx or dxdy)",
        "Set up limits",
        "Integrate inside-out",
    ],
    "double_integrals_polar": [
        "Convert to polar: x=rcosθ, y=rsinθ",
        "Use dA = r dr dθ",
        "Set up r and θ limits",
        "Integrate",
    ],
    "critical_points": [
        "Find where f'(x) = 0 or undefined",
        "Use first/second derivative test",
        "Classify as max, min, or neither",
    ],
    "chain_rule": [
        "Identify outer and inner functions",
        "Derivative = f'(g(x)) · g'(x)",
    ],
    "ratio_test": [
        "Compute L = lim |aₙ₊₁/aₙ|",
        "L < 1: converges, L > 1: diverges",
    ],
    "lhopitals_rule": [
        "Verify 0/0 or ∞/∞ form",
        "Differentiate top and bottom separately",
        "Take limit again",
    ],
    "gradient": [
        "∇f = (∂f/∂x, ∂f/∂y)",
        "Points in direction of steepest increase",
    ],
    "greens_theorem": [
        "∮ F·dr = ∬ (∂Q/∂x - ∂P/∂y) dA",
        "Convert line integral to double integral or vice versa",
    ],
}


def get_tips(topic_id: str) -> list[str]:
    """Get solving tips for a topic."""
    if topic_id in QUICK_TIPS:
        return QUICK_TIPS[topic_id]
    # Generic fallback
    return [
        "Identify the problem type",
        "Set up relevant equations",
        "Solve step by step",
    ]


def aggregate_topics(questions: list) -> dict[str, int]:
    """
    Aggregate topic counts from questions.

    Args:
        questions: List of Question objects with .topics attribute

    Returns:
        {topic_id: count}
    """
    all_topics = []

    for q in questions:
        topics = getattr(q, "topics", [])
        if not topics:
            # Fallback to pattern if no fine-grained topics
            pattern = getattr(q, "pattern", None)
            if pattern:
                topics = [pattern]
        all_topics.extend(topics)

    return dict(Counter(all_topics))


def get_top_topics(topic_counts: dict[str, int], n: int = 5) -> list[tuple[str, int]]:
    """Get top N topics by frequency."""
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_topics[:n]


def generate_focus_advice(top_topics: list[tuple[str, int]]) -> list[dict]:
    """
    Generate focus advice for top topics.

    Returns list of:
    {
        "topic": "integration_by_parts",
        "display_name": "Integration by Parts",
        "count": 6,
        "steps": ["Step 1...", ...]
    }
    """
    advice = []

    for topic_id, count in top_topics:
        advice.append({
            "topic": topic_id,
            "display_name": get_display_name(topic_id),
            "count": count,
            "steps": get_tips(topic_id),
        })

    return advice


def generate_cram_plan(top_topics: list[tuple[str, int]], days: int = 3) -> list[dict]:
    """
    Generate a simple cram plan.

    Distributes topics across days, 2-3 per day.
    """
    if not top_topics:
        return []

    plan = []
    topics_per_day = max(2, (len(top_topics) + days - 1) // days)

    topic_list = [t[0] for t in top_topics]

    for day in range(1, days + 1):
        start = (day - 1) * topics_per_day
        end = start + topics_per_day
        day_topics = topic_list[start:end]

        if not day_topics:
            break

        plan.append({
            "day": day,
            "topics": day_topics,
            "display_names": [get_display_name(t) for t in day_topics],
        })

    return plan


def generate_exam_summary(questions: list, days: int = 3) -> ExamSummary:
    """
    Main function: Generate complete exam analysis.

    Args:
        questions: List of Question objects from uploaded materials
        days: Number of days for cram plan

    Returns:
        ExamSummary with all analysis
    """
    # Step 1: Aggregate topics
    topic_counts = aggregate_topics(questions)

    # Step 2: Get top topics
    top_topics = get_top_topics(topic_counts, n=6)

    # Step 3: Generate focus advice
    focus_advice = generate_focus_advice(top_topics)

    # Step 4: Generate cram plan
    cram_plan = generate_cram_plan(top_topics, days=days)

    return ExamSummary(
        top_topics=top_topics,
        topic_counts=topic_counts,
        focus_advice=focus_advice,
        cram_plan=cram_plan,
        total_questions=len(questions),
    )


# ============================================================
# Formatted Output (for UI)
# ============================================================

def format_summary_markdown(summary: ExamSummary) -> str:
    """
    Format ExamSummary as markdown for display.

    User-friendly language, no technical jargon.
    """
    lines = []

    # Header
    lines.append("## 📊 Exam Analysis")
    lines.append(f"*Based on {summary.total_questions} problems from your materials*")
    lines.append("")

    # Top topics
    lines.append("### 🎯 This course heavily focuses on:")
    lines.append("")
    for i, (topic, count) in enumerate(summary.top_topics, 1):
        name = get_display_name(topic)
        lines.append(f"**{i}. {name}** — appears in {count} problems")
    lines.append("")

    # Focus advice
    lines.append("---")
    lines.append("### 📝 What you should know:")
    lines.append("")

    for advice in summary.focus_advice[:4]:  # Top 4
        lines.append(f"**{advice['display_name']}**")
        for step in advice["steps"]:
            lines.append(f"- {step}")
        lines.append("")

    # Cram plan
    lines.append("---")
    lines.append("### 📅 Cram Plan")
    lines.append("")

    for day in summary.cram_plan:
        topics_str = ", ".join(day["display_names"])
        lines.append(f"**Day {day['day']}:** {topics_str}")

    return "\n".join(lines)


def format_summary_dict(summary: ExamSummary) -> dict:
    """
    Format ExamSummary as dict for API/JSON output.
    """
    return {
        "total_questions": summary.total_questions,
        "top_topics": [
            {"topic": t, "display_name": get_display_name(t), "count": c}
            for t, c in summary.top_topics
        ],
        "focus_advice": summary.focus_advice,
        "cram_plan": summary.cram_plan,
    }
