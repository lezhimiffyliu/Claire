"""
Exam Simulation Mode for Claire.

Core differentiator from GPT:
- Not single-question Q&A
- Full exam experience with timer, no hints, score prediction

Flow:
1. Select exam (from uploaded materials or preset)
2. Take exam (one question at a time, timed, no hints)
3. Get results (score, weak areas, predicted exam score)
4. Paywall for detailed analysis
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class ExamQuestion:
    """A question in an exam simulation."""
    id: str
    text: str
    topic: str  # e.g., "lagrange", "optimization", "partial_derivatives"
    points: int = 20
    difficulty: str = "medium"  # easy, medium, hard
    source: str = ""  # e.g., "SP18 Midterm 2"
    correct_answer: str = ""  # For scoring (can be partial match)
    rubric: list[str] = field(default_factory=list)  # Key steps for partial credit


@dataclass
class ExamResult:
    """Result of an exam simulation."""
    total_score: int
    max_score: int
    question_scores: list[int]  # Score per question
    weak_topics: list[str]
    strong_topics: list[str]
    predicted_low: int  # Predicted exam score range
    predicted_high: int
    time_taken_seconds: int


@dataclass
class ExamSession:
    """Active exam session state."""
    exam_id: str
    questions: list[ExamQuestion]
    current_index: int = 0
    answers: list[str] = field(default_factory=list)
    start_time: float = 0  # Unix timestamp
    time_limit_minutes: int = 45
    is_complete: bool = False
    result: Optional[ExamResult] = None


# ────────────────────────────────────────────────────────────
# Exam Generation
# ────────────────────────────────────────────────────────────

def generate_exam_from_bank(question_bank, num_questions: int = 5) -> list[ExamQuestion]:
    """
    Generate an exam from uploaded question bank.
    Tries to cover different topics.
    """
    if not question_bank or not question_bank.questions:
        return get_fallback_exam()

    # Group questions by topic/category
    by_topic: dict[str, list] = {}
    for q in question_bank.questions:
        # Use first category as topic, or pattern
        topic = q.categories[0] if q.categories else q.pattern or "general"
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(q)

    # Select questions to cover multiple topics
    selected = []
    topics = list(by_topic.keys())
    random.shuffle(topics)

    # First pass: one from each topic
    for topic in topics:
        if len(selected) >= num_questions:
            break
        qs = by_topic[topic]
        q = random.choice(qs)
        selected.append(ExamQuestion(
            id=q.id,
            text=q.text,
            topic=topic,
            points=20,
            difficulty=q.difficulty or "medium",
            source=q.format_source() if hasattr(q, 'format_source') else q.source,
            correct_answer=q.solution or "",
        ))

    # Fill remaining slots
    all_qs = [q for qs in by_topic.values() for q in qs]
    while len(selected) < num_questions and all_qs:
        q = random.choice(all_qs)
        all_qs.remove(q)
        if not any(s.id == q.id for s in selected):
            topic = q.categories[0] if q.categories else q.pattern or "general"
            selected.append(ExamQuestion(
                id=q.id,
                text=q.text,
                topic=topic,
                points=20,
                difficulty=q.difficulty or "medium",
                source=q.format_source() if hasattr(q, 'format_source') else q.source,
                correct_answer=q.solution or "",
            ))

    return selected


def get_fallback_exam() -> list[ExamQuestion]:
    """Default exam when no materials uploaded."""
    return [
        ExamQuestion(
            id="fallback_1",
            text="Find the critical points of f(x,y) = x² + y² - 4x - 6y + 13 and classify each as a local max, local min, or saddle point.",
            topic="optimization",
            points=20,
            difficulty="medium",
            source="Practice Exam",
            correct_answer="(2, 3) is a local minimum",
        ),
        ExamQuestion(
            id="fallback_2",
            text="Use Lagrange multipliers to find the maximum value of f(x,y) = xy subject to the constraint x + 2y = 10.",
            topic="lagrange",
            points=20,
            difficulty="medium",
            source="Practice Exam",
            correct_answer="Maximum is 12.5 at (5, 2.5)",
        ),
        ExamQuestion(
            id="fallback_3",
            text="Evaluate the integral ∫∫_R xy dA where R is the region bounded by y = x² and y = 4.",
            topic="double_integral",
            points=20,
            difficulty="medium",
            source="Practice Exam",
            correct_answer="64/3",
        ),
        ExamQuestion(
            id="fallback_4",
            text="Find ∂z/∂x and ∂z/∂y if z = e^(xy) + ln(x² + y²).",
            topic="partial_derivatives",
            points=20,
            difficulty="easy",
            source="Practice Exam",
            correct_answer="∂z/∂x = ye^(xy) + 2x/(x²+y²)",
        ),
        ExamQuestion(
            id="fallback_5",
            text="A box with no top is to be made from a square piece of cardboard by cutting equal squares from each corner. If the cardboard is 12 inches on each side, what size squares should be cut to maximize the volume?",
            topic="optimization",
            points=20,
            difficulty="hard",
            source="Practice Exam",
            correct_answer="Cut 2-inch squares",
        ),
    ]


# ────────────────────────────────────────────────────────────
# Scoring
# ────────────────────────────────────────────────────────────

TOPIC_LABELS = {
    "optimization": "Optimization",
    "lagrange": "Lagrange Multipliers",
    "constrained_optimization": "Constrained Optimization",
    "double_integral": "Double Integrals",
    "partial_derivatives": "Partial Derivatives",
    "chain_rule": "Chain Rule",
    "gradient": "Gradient",
    "limits": "Limits",
    "integration": "Integration",
    "related_rates": "Related Rates",
}


def score_exam(session: ExamSession) -> ExamResult:
    """
    Score an exam session.

    Scoring (MVP - simple heuristic):
    - Each question: 0, 10, or 20 points
    - 20 = answer looks complete
    - 10 = partial attempt
    - 0 = blank or very short

    Later: Use LLM for actual grading
    """
    question_scores = []
    topic_results: dict[str, list[int]] = {}  # topic -> list of scores

    for i, q in enumerate(session.questions):
        answer = session.answers[i] if i < len(session.answers) else ""
        answer = answer.strip()

        # Simple heuristic scoring
        if not answer or len(answer) < 10:
            score = 0
        elif len(answer) < 50:
            score = 10  # Partial
        else:
            score = 20  # Full credit (assume good faith)

        question_scores.append(score)

        # Track by topic
        topic = q.topic
        if topic not in topic_results:
            topic_results[topic] = []
        topic_results[topic].append(score)

    total_score = sum(question_scores)
    max_score = sum(q.points for q in session.questions)

    # Determine weak/strong topics
    weak_topics = []
    strong_topics = []
    for topic, scores in topic_results.items():
        avg = sum(scores) / len(scores) if scores else 0
        if avg < 10:
            weak_topics.append(topic)
        elif avg >= 15:
            strong_topics.append(topic)

    # Predict exam score (simple heuristic)
    # Your simulation score ± some variance
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    variance = 8
    predicted_low = max(0, int(percentage - variance))
    predicted_high = min(100, int(percentage + variance))

    return ExamResult(
        total_score=total_score,
        max_score=max_score,
        question_scores=question_scores,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        predicted_low=predicted_low,
        predicted_high=predicted_high,
        time_taken_seconds=int(session.start_time),  # Will be calculated properly
    )


def get_topic_label(topic: str) -> str:
    """Get display label for a topic."""
    return TOPIC_LABELS.get(topic, topic.replace("_", " ").title())


# ────────────────────────────────────────────────────────────
# Exam Info for Display
# ────────────────────────────────────────────────────────────

def get_exam_topics(questions: list[ExamQuestion]) -> list[str]:
    """Get unique topics covered in exam."""
    topics = []
    seen = set()
    for q in questions:
        if q.topic not in seen:
            topics.append(get_topic_label(q.topic))
            seen.add(q.topic)
    return topics


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"
