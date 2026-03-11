"""
Exam Context Module - Analyzes course materials to detect exam patterns.

This provides CONTEXT for guided practice, not a separate mode.
"""

from dataclasses import dataclass, field
from typing import Optional


# Pattern keywords for detection
PATTERN_KEYWORDS = {
    "optimization": [
        "maximize", "minimum", "minimize", "maximum", "optimization",
        "critical point", "second derivative", "absolute extrema",
        "largest", "smallest", "optimal",
    ],
    "constrained_optimization": [
        "lagrange", "subject to", "constraint", "bounded by", "boundary",
        "interior", "feasible region", "closed region", "lagrange multiplier",
    ],
    "related_rates": [
        "related rates", "how fast", "rate of change", "per second",
        "per minute", "velocity", "sliding", "filling", "draining",
        "increasing", "decreasing", "dv/dt", "dr/dt",
    ],
    "derivatives": [
        "derivative", "differentiate", "product rule", "chain rule",
        "implicit differentiation", "tangent line", "linearization",
        "quotient rule", "d/dx",
    ],
    "integration": [
        "integral", "integrate", "substitution", "integration by parts",
        "partial fractions", "area under", "antiderivative", "u-sub",
    ],
    "limits": [
        "limit", "approaches", "continuity", "l'hopital", "l'hôpital",
        "indeterminate", "infinity", "squeeze theorem",
    ],
}

# Study priorities for each pattern
PATTERN_PRIORITIES = {
    "optimization": "Focus on: setup objective function → find critical points → check endpoints",
    "constrained_optimization": "Focus on: Lagrange system setup → solve 3 equations → compare values",
    "related_rates": "Focus on: draw diagram → write equation → implicit differentiate → substitute",
    "derivatives": "Focus on: identify rule (chain/product/quotient) → apply correctly",
    "integration": "Focus on: choose technique (u-sub/parts/partial) → execute → verify",
    "limits": "Focus on: classify form → choose method (direct/L'Hopital/algebra)",
}


@dataclass
class PatternInfo:
    """Information about a detected pattern."""
    name: str
    score: int  # Number of keyword matches
    evidence: list[str]  # Keywords found
    priority: str  # Study focus


@dataclass
class ExamContext:
    """
    Context derived from uploaded course materials.
    Used to guide practice sessions.
    """
    materials: list[str] = field(default_factory=list)  # Raw material texts
    material_names: list[str] = field(default_factory=list)  # File names
    detected_patterns: list[PatternInfo] = field(default_factory=list)
    total_chars: int = 0

    def has_context(self) -> bool:
        """Check if any materials have been loaded."""
        return len(self.materials) > 0

    def get_top_patterns(self, n: int = 3) -> list[PatternInfo]:
        """Get top N patterns by score."""
        return self.detected_patterns[:n]

    def get_pattern_names(self) -> list[str]:
        """Get names of all detected patterns."""
        return [p.name for p in self.detected_patterns]

    def format_for_prompt(self) -> str:
        """Format context for inclusion in agent prompt."""
        if not self.has_context():
            return ""

        lines = ["[EXAM CONTEXT FROM UPLOADED MATERIALS]"]
        lines.append(f"Materials loaded: {len(self.materials)}")

        if self.detected_patterns:
            lines.append("Likely exam patterns (by frequency):")
            for p in self.detected_patterns[:5]:
                lines.append(f"  - {p.name}: {p.priority}")

        lines.append("[END EXAM CONTEXT]")
        return "\n".join(lines)


def analyze_materials(texts: list[str], names: list[str] = None) -> ExamContext:
    """
    Analyze course materials and create exam context.

    Args:
        texts: List of material content strings
        names: Optional list of material names/filenames

    Returns:
        ExamContext with detected patterns
    """
    if names is None:
        names = [f"material_{i}" for i in range(len(texts))]

    # Combine all text
    combined = " ".join(texts).lower()
    total_chars = sum(len(t) for t in texts)

    # Detect patterns
    pattern_scores: dict[str, tuple[int, list[str]]] = {}

    for pattern, keywords in PATTERN_KEYWORDS.items():
        evidence = []
        for kw in keywords:
            if kw in combined:
                evidence.append(kw)
        if evidence:
            pattern_scores[pattern] = (len(evidence), evidence)

    # Sort by score
    sorted_patterns = sorted(
        pattern_scores.items(),
        key=lambda x: x[1][0],
        reverse=True
    )

    # Build PatternInfo list
    detected = []
    for pattern_name, (score, evidence) in sorted_patterns:
        detected.append(PatternInfo(
            name=pattern_name,
            score=score,
            evidence=evidence[:5],  # Keep top 5 evidence
            priority=PATTERN_PRIORITIES.get(pattern_name, "Review the heuristic template.")
        ))

    return ExamContext(
        materials=texts,
        material_names=names,
        detected_patterns=detected,
        total_chars=total_chars
    )


def add_material(context: ExamContext, text: str, name: str = "pasted") -> ExamContext:
    """
    Add a new material to existing context and re-analyze.

    Args:
        context: Existing ExamContext
        text: New material content
        name: Material name

    Returns:
        Updated ExamContext
    """
    new_texts = context.materials + [text]
    new_names = context.material_names + [name]
    return analyze_materials(new_texts, new_names)


def clear_context() -> ExamContext:
    """Return an empty context."""
    return ExamContext()
