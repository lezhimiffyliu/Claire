"""
Exam Context Module - Analyzes course materials to detect exam patterns.

This provides CONTEXT for guided practice, not a separate mode.
Integrates with QuestionBank for problem extraction.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from question_bank import QuestionBank


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
    question_bank: Optional["QuestionBank"] = None  # Extracted questions

    def has_context(self) -> bool:
        """Check if any materials have been loaded."""
        return len(self.materials) > 0

    def has_questions(self) -> bool:
        """Check if question bank has questions."""
        return self.question_bank is not None and len(self.question_bank) > 0

    def get_question_count(self) -> int:
        """Get number of extracted questions."""
        if self.question_bank:
            return len(self.question_bank)
        return 0

    def get_top_patterns(self, n: int = 3) -> list[PatternInfo]:
        """Get top N patterns by score."""
        return self.detected_patterns[:n]

    def get_pattern_names(self) -> list[str]:
        """Get names of all detected patterns."""
        return [p.name for p in self.detected_patterns]

    def get_questions_for_pattern(self, pattern: str) -> list:
        """Get questions for a specific pattern."""
        if self.question_bank:
            return self.question_bank.get_by_pattern(pattern)
        return []

    def format_for_prompt(self) -> str:
        """Format context for inclusion in agent prompt."""
        if not self.has_context():
            return ""

        lines = ["[EXAM CONTEXT FROM UPLOADED MATERIALS]"]
        lines.append(f"Materials loaded: {len(self.materials)}")

        if self.question_bank:
            lines.append(f"Questions extracted: {len(self.question_bank)}")

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


def analyze_files(files: list[tuple[str, bytes]]) -> ExamContext:
    """
    Analyze uploaded files (supports PDF, TXT, MD).

    Args:
        files: List of (filename, file_bytes) tuples

    Returns:
        ExamContext with detected patterns and extracted questions
    """
    from question_bank import extract_text_from_file, build_question_bank

    texts = []
    names = []

    # Extract text from each file
    for filename, file_bytes in files:
        try:
            text = extract_text_from_file(file_bytes, filename)
            texts.append(text)
            names.append(filename)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    if not texts:
        return ExamContext()

    # Analyze patterns from text
    context = analyze_materials(texts, names)

    # Build question bank
    question_bank = build_question_bank(files)
    context.question_bank = question_bank

    return context
