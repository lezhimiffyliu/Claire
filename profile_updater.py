"""
Profile Updater - updates student profile based on attempt results.

Scoring logic:
- Correct: +10 points to topic/concepts
- Correct after hint: +5 points (reduced credit)
- Incorrect: -8 points to topic/concepts
- Error type: count += 1
- Consecutive failures on same topic: trigger needs_foundation_work
"""

from dataclasses import dataclass, field
from typing import Optional
from copy import deepcopy


@dataclass
class Attempt:
    """A single practice attempt."""
    problem_id: str
    course: str
    topic: str
    concepts: list[str] = field(default_factory=list)
    correct: bool = False
    error_type: Optional[str] = None  # concept, algebra, logic, careless
    hint_used: bool = False
    solved_after_hint: bool = False


@dataclass
class TopicScore:
    """Score tracking for a topic or concept."""
    score: float = 50.0  # Start at 50 (neutral)
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    streak: int = 0  # Positive = correct streak, negative = incorrect streak

    @property
    def mastery_level(self) -> str:
        """weak / developing / solid / mastered"""
        if self.attempts < 2:
            return "untested"
        if self.score < 30:
            return "weak"
        if self.score < 50:
            return "developing"
        if self.score < 75:
            return "solid"
        return "mastered"

    @property
    def accuracy(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts


@dataclass
class StudentProfile:
    """
    Student profile with scoring system.
    """
    course: str

    # Topic scores: {topic: TopicScore}
    topic_scores: dict = field(default_factory=dict)

    # Concept scores: {concept: TopicScore}
    concept_scores: dict = field(default_factory=dict)

    # Error pattern counts
    error_counts: dict = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })

    # Diagnostic results
    diagnostic_score: float = 0.0
    diagnostic_weak_topics: list = field(default_factory=list)

    # Foundation flags
    needs_foundation_work: bool = False
    foundation_topics: list = field(default_factory=list)  # Topics needing foundation

    # Recent history for streak detection
    recent_attempts: list = field(default_factory=list)  # Last N attempts per topic

    # Totals
    total_correct: int = 0
    total_incorrect: int = 0

    def get_topic_score(self, topic: str) -> TopicScore:
        """Get or create topic score."""
        if topic not in self.topic_scores:
            self.topic_scores[topic] = TopicScore()
        return self.topic_scores[topic]

    def get_concept_score(self, concept: str) -> TopicScore:
        """Get or create concept score."""
        if concept not in self.concept_scores:
            self.concept_scores[concept] = TopicScore()
        return self.concept_scores[concept]

    def get_weak_topics(self) -> list[str]:
        """Get topics sorted by weakness (lowest score first)."""
        scored = [
            (topic, ts.score, ts.attempts)
            for topic, ts in self.topic_scores.items()
        ]
        # Sort by score ascending, then by attempts (fewer = less tested)
        scored.sort(key=lambda x: (x[1], x[2]))
        return [t[0] for t in scored if t[1] < 60]  # Only weak/developing

    def get_dominant_error_type(self) -> Optional[str]:
        """Get the most common error type."""
        if not any(self.error_counts.values()):
            return None
        return max(self.error_counts.items(), key=lambda x: x[1])[0]

    @property
    def overall_accuracy(self) -> float:
        total = self.total_correct + self.total_incorrect
        if total == 0:
            return 0.0
        return self.total_correct / total

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "course": self.course,
            "topic_scores": {
                k: {
                    "score": v.score,
                    "attempts": v.attempts,
                    "correct": v.correct,
                    "incorrect": v.incorrect,
                    "streak": v.streak,
                }
                for k, v in self.topic_scores.items()
            },
            "concept_scores": {
                k: {
                    "score": v.score,
                    "attempts": v.attempts,
                    "correct": v.correct,
                    "incorrect": v.incorrect,
                    "streak": v.streak,
                }
                for k, v in self.concept_scores.items()
            },
            "error_counts": self.error_counts,
            "diagnostic_score": self.diagnostic_score,
            "diagnostic_weak_topics": self.diagnostic_weak_topics,
            "needs_foundation_work": self.needs_foundation_work,
            "foundation_topics": self.foundation_topics,
            "total_correct": self.total_correct,
            "total_incorrect": self.total_incorrect,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudentProfile":
        """Deserialize from storage."""
        profile = cls(course=data.get("course", "124"))
        profile.error_counts = data.get("error_counts", {
            "concept": 0, "algebra": 0, "logic": 0, "careless": 0
        })
        profile.diagnostic_score = data.get("diagnostic_score", 0.0)
        profile.diagnostic_weak_topics = data.get("diagnostic_weak_topics", [])
        profile.needs_foundation_work = data.get("needs_foundation_work", False)
        profile.foundation_topics = data.get("foundation_topics", [])
        profile.total_correct = data.get("total_correct", 0)
        profile.total_incorrect = data.get("total_incorrect", 0)

        # Rebuild topic scores
        for topic, stats in data.get("topic_scores", {}).items():
            ts = TopicScore()
            ts.score = stats.get("score", 50.0)
            ts.attempts = stats.get("attempts", 0)
            ts.correct = stats.get("correct", 0)
            ts.incorrect = stats.get("incorrect", 0)
            ts.streak = stats.get("streak", 0)
            profile.topic_scores[topic] = ts

        # Rebuild concept scores
        for concept, stats in data.get("concept_scores", {}).items():
            ts = TopicScore()
            ts.score = stats.get("score", 50.0)
            ts.attempts = stats.get("attempts", 0)
            ts.correct = stats.get("correct", 0)
            ts.incorrect = stats.get("incorrect", 0)
            ts.streak = stats.get("streak", 0)
            profile.concept_scores[concept] = ts

        return profile


# ============================================================
# SCORING CONSTANTS
# ============================================================

SCORE_CORRECT = 10          # Points for correct answer
SCORE_CORRECT_WITH_HINT = 5  # Points for correct after hint (reduced)
SCORE_INCORRECT = -8        # Points for incorrect answer
SCORE_MIN = 0               # Minimum score
SCORE_MAX = 100             # Maximum score

CONSECUTIVE_FAILURES_THRESHOLD = 3  # Failures to trigger foundation flag


# ============================================================
# UPDATE FUNCTION
# ============================================================

def update_profile(profile: StudentProfile, attempt: Attempt) -> StudentProfile:
    """
    Update profile based on attempt result.
    Returns a new profile (does not mutate input).

    Scoring:
    - Correct: +10 to topic and each concept
    - Correct after hint: +5 (reduced credit)
    - Incorrect: -8 to topic and each concept
    - Error type count += 1
    - 3+ consecutive failures on topic → needs_foundation_work
    """
    # Create a deep copy to avoid mutation
    new_profile = deepcopy(profile)

    # Determine score delta
    if attempt.correct:
        if attempt.hint_used and attempt.solved_after_hint:
            delta = SCORE_CORRECT_WITH_HINT
        else:
            delta = SCORE_CORRECT
        new_profile.total_correct += 1
    else:
        delta = SCORE_INCORRECT
        new_profile.total_incorrect += 1

        # Track error type
        if attempt.error_type and attempt.error_type in new_profile.error_counts:
            new_profile.error_counts[attempt.error_type] += 1

    # Update topic score
    topic_score = new_profile.get_topic_score(attempt.topic)
    topic_score.score = max(SCORE_MIN, min(SCORE_MAX, topic_score.score + delta))
    topic_score.attempts += 1

    if attempt.correct:
        topic_score.correct += 1
        # Update streak
        if topic_score.streak >= 0:
            topic_score.streak += 1
        else:
            topic_score.streak = 1  # Reset negative streak
    else:
        topic_score.incorrect += 1
        # Update streak
        if topic_score.streak <= 0:
            topic_score.streak -= 1
        else:
            topic_score.streak = -1  # Reset positive streak

    # Update concept scores
    for concept in attempt.concepts:
        concept_score = new_profile.get_concept_score(concept)
        concept_score.score = max(SCORE_MIN, min(SCORE_MAX, concept_score.score + delta))
        concept_score.attempts += 1

        if attempt.correct:
            concept_score.correct += 1
        else:
            concept_score.incorrect += 1

    # Check for foundation work trigger
    # If 3+ consecutive failures on a topic
    if topic_score.streak <= -CONSECUTIVE_FAILURES_THRESHOLD:
        new_profile.needs_foundation_work = True
        if attempt.topic not in new_profile.foundation_topics:
            new_profile.foundation_topics.append(attempt.topic)

    # Also check concept-level failures
    for concept in attempt.concepts:
        cs = new_profile.get_concept_score(concept)
        if cs.streak <= -CONSECUTIVE_FAILURES_THRESHOLD:
            new_profile.needs_foundation_work = True

    return new_profile


def record_diagnostic_result(
    profile: StudentProfile,
    score: float,
    weak_topics: list[str]
) -> StudentProfile:
    """
    Record diagnostic results into profile.
    """
    new_profile = deepcopy(profile)
    new_profile.diagnostic_score = score
    new_profile.diagnostic_weak_topics = weak_topics

    # Initialize weak topics with low scores
    for topic in weak_topics:
        ts = new_profile.get_topic_score(topic)
        ts.score = 30  # Start weak topics at 30
        ts.incorrect += 1
        ts.attempts += 1
        ts.streak = -1

    # If diagnostic score < 50%, flag for foundation
    if score < 0.5:
        new_profile.needs_foundation_work = True

    return new_profile
