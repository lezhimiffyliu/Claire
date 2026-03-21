"""
Exam Scope Analyzer - Generates a structured "exam map" from uploaded materials.

After upload, produces:
  - Topic distribution (what % of material covers each topic)
  - High-frequency topics (likely exam content)
  - Risk areas (low coverage — study carefully)
  - Minimum passing path (master these first)
"""

from dataclasses import dataclass, field
from typing import List, Tuple

TOPIC_DISPLAY = {
    "optimization": "Optimization (max/min)",
    "constrained_optimization": "Constrained Optimization",
    "related_rates": "Related Rates",
    "derivatives": "Derivatives & Rules",
    "integration": "Integration",
    "limits": "Limits & Continuity",
}

TOPIC_EMOJI = {
    "optimization": "📈",
    "constrained_optimization": "🔒",
    "related_rates": "⏱️",
    "derivatives": "📐",
    "integration": "∫",
    "limits": "→",
}

ALL_TOPICS = list(TOPIC_DISPLAY.keys())


@dataclass
class ExamScopeReport:
    topic_distribution: List[Tuple[str, int, int]]  # (name, pct, raw_score)
    high_freq_topics: List[str]                      # top topics
    risk_areas: List[str]                            # missing or low-score topics
    min_passing_path: List[str]                      # minimum set to focus on
    total_questions: int
    material_names: List[str]


def generate_exam_scope(exam_context) -> ExamScopeReport:
    """
    Generate an ExamScopeReport from an ExamContext.
    Uses detected patterns as primary signal; question bank categories as
    a secondary refinement when available.
    """
    patterns = exam_context.detected_patterns  # List[PatternInfo]
    total_score = sum(p.score for p in patterns) or 1
    q_count = exam_context.get_question_count()

    # Build topic distribution from pattern scores
    topic_dist: List[Tuple[str, int, int]] = []
    for p in patterns:
        pct = max(1, round(p.score / total_score * 100))
        topic_dist.append((p.name, pct, p.score))

    # Refine with question-bank category counts if available
    if exam_context.question_bank and q_count > 0:
        from collections import Counter
        cat_counts: Counter = Counter()
        for q in exam_context.question_bank.questions:
            for cat in (q.categories or []):
                cat_lower = cat.lower()
                for pat_name in ALL_TOPICS:
                    if pat_name in cat_lower or cat_lower in pat_name:
                        cat_counts[pat_name] += 1
                        break

        if cat_counts:
            total_q = sum(cat_counts.values()) or 1
            topic_dist = []
            for pat_name in sorted(cat_counts, key=lambda x: -cat_counts[x]):
                pct = max(1, round(cat_counts[pat_name] / total_q * 100))
                topic_dist.append((pat_name, pct, cat_counts[pat_name]))

    # High-frequency: top 3
    high_freq = [name for name, _, _ in topic_dist[:3]]

    # Risk areas: not detected, or very low score
    detected_names = {name for name, _, _ in topic_dist}
    risk: List[str] = []
    for topic in ALL_TOPICS:
        if topic not in detected_names:
            risk.append(topic)
        else:
            score = next((s for n, _, s in topic_dist if n == topic), 0)
            if score <= 1:
                risk.append(topic)

    # Minimum passing path: cover ≥70% of content with fewest topics
    min_path: List[str] = []
    cumulative_pct = 0
    for name, pct, _ in topic_dist:
        min_path.append(name)
        cumulative_pct += pct
        if cumulative_pct >= 70 or len(min_path) >= 3:
            break

    return ExamScopeReport(
        topic_distribution=topic_dist,
        high_freq_topics=high_freq,
        risk_areas=risk[:4],
        min_passing_path=min_path,
        total_questions=q_count,
        material_names=exam_context.material_names,
    )
