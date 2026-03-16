"""
Practice Planner — turns diagnostic results into a prioritized problem list.

Priority formula for each question in the bank:
  score = weak_topic_bonus + frequency_score + points_score + difficulty_fit

- weak_topic_bonus : +3 if the question's pattern matches a weak topic from diagnostic
- frequency_score  : how many distinct source files contain this topic (0–2 pts)
- points_score     : extracted point value from question text, normalized (0–2 pts)
- difficulty_fit   : beginners get easy questions first; advanced get hard first (0–1 pt)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Map diagnostic topic names → question_bank pattern names
TOPIC_TO_PATTERN: dict[str, list[str]] = {
    # Calc I
    "derivatives":              ["derivatives"],
    "optimization":             ["optimization"],
    "limits":                   ["limits"],
    "integration":              ["integration"],
    # Calc II extras
    "series":                   ["series", "limits"],
    "improper_integrals":       ["integration", "limits"],
    "volume":                   ["integration"],
    # Calc III extras
    "partial_derivatives":      ["derivatives"],
    "constrained_optimization": ["constrained_optimization"],
    "multivariable_integration": ["integration"],
    "gradient":                 ["derivatives"],
    "multivariable_optimization": ["optimization", "constrained_optimization"],
    # related rates always high-value
    "related_rates":            ["related_rates"],
}

# Human-readable topic labels
TOPIC_LABELS: dict[str, str] = {
    "derivatives":              "Derivatives",
    "optimization":             "Optimization (max/min)",
    "limits":                   "Limits",
    "integration":              "Integration",
    "series":                   "Series & Convergence",
    "improper_integrals":       "Improper Integrals",
    "volume":                   "Volume of Revolution",
    "partial_derivatives":      "Partial Derivatives",
    "constrained_optimization": "Lagrange Multipliers",
    "multivariable_integration":"Multivariable Integration",
    "gradient":                 "Gradient & Directional Derivatives",
    "multivariable_optimization":"Multivariable Optimization",
    "related_rates":            "Related Rates",
}

_POINTS_RE = re.compile(
    r"\(?\s*(\d{1,3})\s*(?:pts?|points?|marks?)\s*\)?",
    re.IGNORECASE,
)


def _extract_points(text: str) -> int:
    """Pull the first point value mentioned in the problem text (e.g. '(10 pts)')."""
    m = _POINTS_RE.search(text)
    return int(m.group(1)) if m else 0


def _topic_patterns(weak_topics: list[str]) -> set[str]:
    """Flatten weak topic names → set of question_bank pattern strings."""
    out: set[str] = set()
    for t in weak_topics:
        out.update(TOPIC_TO_PATTERN.get(t, [t]))
    return out


@dataclass
class ScoredQuestion:
    question: object          # question_bank.Question
    score: float
    reasons: list[str] = field(default_factory=list)


def prioritize_questions(
    result,           # PlacementResult
    question_bank,    # question_bank.QuestionBank
    *,
    limit: int = 20,
) -> list:
    """
    Return up to `limit` Question objects sorted by practice priority.
    """
    if question_bank is None:
        return []

    questions = getattr(question_bank, "questions", [])
    if not questions:
        return []

    weak_patterns = _topic_patterns(result.weak_topics)
    level = result.level  # beginner / intermediate / advanced

    # Count how many distinct sources mention each pattern (frequency proxy)
    pattern_source_count: dict[str, set[str]] = {}
    for q in questions:
        pat = getattr(q, "pattern", "")
        src = getattr(q, "source", "")
        pattern_source_count.setdefault(pat, set()).add(src)

    # Max points across all questions (for normalization)
    all_points = [_extract_points(getattr(q, "text", "")) for q in questions]
    max_points = max(all_points) if any(p > 0 for p in all_points) else 1

    scored: list[ScoredQuestion] = []
    for q, pts in zip(questions, all_points):
        s = 0.0
        reasons: list[str] = []
        pat = getattr(q, "pattern", "")
        diff = getattr(q, "difficulty", "medium")

        # 1. Weak topic bonus
        if pat in weak_patterns:
            s += 3.0
            reasons.append("weak area")

        # 2. Frequency (how many exams/files feature this topic)
        freq = len(pattern_source_count.get(pat, set()))
        freq_score = min(freq / 2, 1.0) * 2  # cap at 2 pts
        s += freq_score
        if freq > 1:
            reasons.append(f"appears in {freq} sources")

        # 3. Point value
        if pts > 0:
            pts_score = (pts / max_points) * 2
            s += pts_score
            reasons.append(f"{pts} pts")

        # 4. Difficulty fit
        diff_rank = {"easy": 0, "medium": 1, "hard": 2}.get(diff, 1)
        if level == "beginner":
            fit = 1.0 - diff_rank * 0.4   # easy=1.0, medium=0.6, hard=0.2
        elif level == "advanced":
            fit = diff_rank * 0.4          # hard=0.8, medium=0.4, easy=0.0
        else:
            fit = 0.5 - abs(diff_rank - 1) * 0.2  # medium=0.5, easy/hard=0.3
        s += fit

        scored.append(ScoredQuestion(question=q, score=s, reasons=reasons))

    scored.sort(key=lambda x: x.score, reverse=True)
    return [s.question for s in scored[:limit]]


def format_study_plan(result, prioritized_questions: list, *, max_preview: int = 5) -> str:
    """
    Return a markdown string summarising the diagnostic outcome and
    the top practice problems, suitable for injecting into the chat.
    """
    level_emoji = {"beginner": "🌱", "intermediate": "📚", "advanced": "🚀"}.get(
        result.level, "📚"
    )

    lines: list[str] = []
    lines.append(f"### {level_emoji} Diagnostic complete — {result.score}/{result.total}")
    lines.append("")

    if result.weak_topics:
        weak_labels = [TOPIC_LABELS.get(t, t.replace("_", " ").title()) for t in result.weak_topics]
        lines.append(f"**Areas to focus on:** {', '.join(weak_labels)}")
    if result.strong_topics:
        strong_labels = [TOPIC_LABELS.get(t, t.replace("_", " ").title()) for t in result.strong_topics]
        lines.append(f"**Already solid:** {', '.join(strong_labels)}")

    lines.append("")
    lines.append(result.summary)

    if prioritized_questions:
        lines.append("")
        lines.append(f"**Recommended practice order** (top {min(max_preview, len(prioritized_questions))}):")
        for i, q in enumerate(prioritized_questions[:max_preview], 1):
            src = getattr(q, "source", "")
            pid = getattr(q, "problem_id", "")
            diff = getattr(q, "difficulty", "medium")
            diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(diff, "")
            label = f"{src} — {pid}" if pid else src
            pts = _extract_points(getattr(q, "text", ""))
            pts_str = f" · {pts} pts" if pts else ""
            lines.append(f"{i}. {diff_icon} **{label}**{pts_str}")

    lines.append("")
    lines.append("Just paste or click any problem to start. I'll teach based on your weak areas first.")
    return "\n".join(lines)
