"""
Student State Model - the core of Claire's "memory".

Three layers:
1. Structured mastery memory (drives recommendations)
2. Attempt history (event stream, updates profile)
3. User preferences (minimal, stable)

NOT a "chat memory" system. This is a state model.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
from copy import deepcopy
import json


# ============================================================
# SCORING CONSTANTS
# ============================================================

SCORE_CORRECT = 0.08           # Score increase for correct
SCORE_CORRECT_WITH_HINT = 0.04 # Reduced credit with hint
SCORE_INCORRECT = -0.06        # Score decrease for incorrect
SCORE_MIN = 0.0
SCORE_MAX = 1.0

RECENT_WINDOW = 5              # Recent attempts for trend
FOUNDATION_THRESHOLD = 3       # Consecutive failures to trigger foundation


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class MasteryScore:
    """Score for a topic or concept."""
    score: float = 0.5          # 0-1, starts neutral
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    streak: int = 0             # +ve = correct streak, -ve = incorrect
    recent_results: list = field(default_factory=list)  # Last N results (True/False)
    last_seen_at: Optional[str] = None

    @property
    def mastery_level(self) -> str:
        """weak / developing / solid / mastered"""
        if self.attempts < 2:
            return "untested"
        if self.score < 0.3:
            return "weak"
        if self.score < 0.5:
            return "developing"
        if self.score < 0.75:
            return "solid"
        return "mastered"

    @property
    def recent_trend(self) -> str:
        """up / down / flat based on recent results."""
        if len(self.recent_results) < 3:
            return "flat"
        recent = self.recent_results[-3:]
        correct_count = sum(recent)
        if correct_count >= 2:
            return "up"
        if correct_count <= 1:
            return "down"
        return "flat"

    def record(self, correct: bool):
        """Record an attempt result."""
        self.attempts += 1
        self.last_seen_at = datetime.now().isoformat()

        if correct:
            self.correct += 1
            self.streak = self.streak + 1 if self.streak >= 0 else 1
        else:
            self.incorrect += 1
            self.streak = self.streak - 1 if self.streak <= 0 else -1

        # Update recent results
        self.recent_results.append(correct)
        if len(self.recent_results) > RECENT_WINDOW:
            self.recent_results.pop(0)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "attempts": self.attempts,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "streak": self.streak,
            "recent_results": self.recent_results,
            "last_seen_at": self.last_seen_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MasteryScore":
        ms = cls()
        ms.score = data.get("score", 0.5)
        ms.attempts = data.get("attempts", 0)
        ms.correct = data.get("correct", 0)
        ms.incorrect = data.get("incorrect", 0)
        ms.streak = data.get("streak", 0)
        ms.recent_results = data.get("recent_results", [])
        ms.last_seen_at = data.get("last_seen_at")
        return ms


@dataclass
class OrthogonalProfile:
    """
    Orthogonal skill dimensions - independent of topic.
    These reveal HOW a student struggles, not just WHERE.
    """
    # Skill type mastery
    skill_type: dict = field(default_factory=lambda: {
        "computational": 0.5,
        "conceptual": 0.5,
        "application": 0.5,
        "proof": 0.5,
        "multi_step": 0.5,
    })

    # Representation mastery
    representation: dict = field(default_factory=lambda: {
        "symbolic": 0.5,
        "word_problem": 0.5,
        "graphical": 0.5,
        "tabular": 0.5,
    })

    # Difficulty performance
    difficulty: dict = field(default_factory=lambda: {
        "routine": 0.5,
        "standard": 0.5,
        "challenging": 0.5,
    })

    def update(self, tags: dict, correct: bool, hint_used: bool = False):
        """Update orthogonal scores based on attempt."""
        if hint_used and correct:
            delta = SCORE_CORRECT_WITH_HINT
        elif correct:
            delta = SCORE_CORRECT
        else:
            delta = SCORE_INCORRECT

        # Update skill_type
        for skill in tags.get("skill_type", []):
            if skill in self.skill_type:
                self.skill_type[skill] = max(SCORE_MIN, min(SCORE_MAX,
                    self.skill_type[skill] + delta))

        # Update representation
        rep = tags.get("representation")
        if rep and rep in self.representation:
            self.representation[rep] = max(SCORE_MIN, min(SCORE_MAX,
                self.representation[rep] + delta))

        # Update difficulty
        diff = tags.get("difficulty")
        if diff and diff in self.difficulty:
            self.difficulty[diff] = max(SCORE_MIN, min(SCORE_MAX,
                self.difficulty[diff] + delta))

    def get_weaknesses(self) -> dict:
        """Get weak areas across all dimensions."""
        weak = {}

        weak_skills = [k for k, v in self.skill_type.items() if v < 0.4]
        if weak_skills:
            weak["skill_type"] = weak_skills

        weak_reps = [k for k, v in self.representation.items() if v < 0.4]
        if weak_reps:
            weak["representation"] = weak_reps

        weak_diff = [k for k, v in self.difficulty.items() if v < 0.4]
        if weak_diff:
            weak["difficulty"] = weak_diff

        return weak

    def to_dict(self) -> dict:
        return {
            "skill_type": self.skill_type,
            "representation": self.representation,
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OrthogonalProfile":
        op = cls()
        op.skill_type = data.get("skill_type", op.skill_type)
        op.representation = data.get("representation", op.representation)
        op.difficulty = data.get("difficulty", op.difficulty)
        return op


@dataclass
class StudentState:
    """
    Complete student state model.
    This is the "long-term memory" - but structured, not conversational.
    """
    # Identity
    user_id: str = "anonymous"
    course: str = "124"  # "124", "125", "126"

    # Meta
    profile_version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Diagnostic state
    diagnostic_completed: bool = False
    diagnostic_score: float = 0.0
    diagnostic_weak_topics: list = field(default_factory=list)

    # Foundation flag
    needs_foundation_work: bool = False
    foundation_topics: list = field(default_factory=list)

    # Topic mastery: {topic: MasteryScore}
    topic_mastery: dict = field(default_factory=dict)

    # Concept mastery: {concept: MasteryScore}
    concept_mastery: dict = field(default_factory=dict)

    # Orthogonal dimensions
    orthogonal: OrthogonalProfile = field(default_factory=OrthogonalProfile)

    # Error patterns
    error_counts: dict = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })

    # User preferences (minimal, stable)
    preferences: dict = field(default_factory=lambda: {
        "feedback_style": "hint_first",  # hint_first, direct, socratic
        "current_mode": "exam_prep",     # exam_prep, learn, review
    })

    # Totals
    total_correct: int = 0
    total_incorrect: int = 0

    # --------------------------------------------------------
    # GETTERS
    # --------------------------------------------------------

    def get_topic_mastery(self, topic: str) -> MasteryScore:
        if topic not in self.topic_mastery:
            self.topic_mastery[topic] = MasteryScore()
        return self.topic_mastery[topic]

    def get_concept_mastery(self, concept: str) -> MasteryScore:
        if concept not in self.concept_mastery:
            self.concept_mastery[concept] = MasteryScore()
        return self.concept_mastery[concept]

    def get_weak_topics(self, limit: int = 5) -> list[str]:
        """Topics sorted by weakness."""
        scored = [
            (topic, ms.score, ms.attempts)
            for topic, ms in self.topic_mastery.items()
        ]
        scored.sort(key=lambda x: (x[1], x[2]))
        return [t[0] for t in scored[:limit] if t[1] < 0.6]

    def get_strong_topics(self, limit: int = 5) -> list[str]:
        """Topics sorted by strength."""
        scored = [
            (topic, ms.score, ms.attempts)
            for topic, ms in self.topic_mastery.items()
            if ms.attempts >= 2
        ]
        scored.sort(key=lambda x: -x[1])
        return [t[0] for t in scored[:limit] if t[1] >= 0.6]

    def get_weak_concepts(self, limit: int = 5) -> list[str]:
        """Concepts sorted by weakness."""
        scored = [
            (concept, ms.score, ms.attempts)
            for concept, ms in self.concept_mastery.items()
        ]
        scored.sort(key=lambda x: (x[1], x[2]))
        return [c[0] for c in scored[:limit] if c[1] < 0.5]

    def get_dominant_error_type(self) -> Optional[str]:
        if not any(self.error_counts.values()):
            return None
        return max(self.error_counts.items(), key=lambda x: x[1])[0]

    @property
    def overall_accuracy(self) -> float:
        total = self.total_correct + self.total_incorrect
        return self.total_correct / total if total > 0 else 0.0

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "course": self.course,
            "profile_version": self.profile_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "diagnostic_completed": self.diagnostic_completed,
            "diagnostic_score": self.diagnostic_score,
            "diagnostic_weak_topics": self.diagnostic_weak_topics,
            "needs_foundation_work": self.needs_foundation_work,
            "foundation_topics": self.foundation_topics,
            "topic_mastery": {k: v.to_dict() for k, v in self.topic_mastery.items()},
            "concept_mastery": {k: v.to_dict() for k, v in self.concept_mastery.items()},
            "orthogonal": self.orthogonal.to_dict(),
            "error_counts": self.error_counts,
            "preferences": self.preferences,
            "total_correct": self.total_correct,
            "total_incorrect": self.total_incorrect,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudentState":
        state = cls()
        state.user_id = data.get("user_id", "anonymous")
        state.course = data.get("course", "124")
        state.profile_version = data.get("profile_version", 1)
        state.created_at = data.get("created_at", state.created_at)
        state.updated_at = data.get("updated_at", state.updated_at)
        state.diagnostic_completed = data.get("diagnostic_completed", False)
        state.diagnostic_score = data.get("diagnostic_score", 0.0)
        state.diagnostic_weak_topics = data.get("diagnostic_weak_topics", [])
        state.needs_foundation_work = data.get("needs_foundation_work", False)
        state.foundation_topics = data.get("foundation_topics", [])
        state.error_counts = data.get("error_counts", state.error_counts)
        state.preferences = data.get("preferences", state.preferences)
        state.total_correct = data.get("total_correct", 0)
        state.total_incorrect = data.get("total_incorrect", 0)

        # Rebuild topic mastery
        for topic, ms_data in data.get("topic_mastery", {}).items():
            state.topic_mastery[topic] = MasteryScore.from_dict(ms_data)

        # Rebuild concept mastery
        for concept, ms_data in data.get("concept_mastery", {}).items():
            state.concept_mastery[concept] = MasteryScore.from_dict(ms_data)

        # Rebuild orthogonal
        if "orthogonal" in data:
            state.orthogonal = OrthogonalProfile.from_dict(data["orthogonal"])

        return state

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "StudentState":
        return cls.from_dict(json.loads(json_str))


# ============================================================
# ATTEMPT EVENT
# ============================================================

@dataclass
class AttemptEvent:
    """
    A single practice attempt - the atomic unit of history.
    This is an event, not stored in the state directly.
    """
    attempt_id: str
    user_id: str
    problem_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Problem metadata
    course: str = "124"
    topic: str = ""
    concepts: list = field(default_factory=list)

    # Orthogonal tags
    skill_type: list = field(default_factory=list)      # computational, conceptual, etc.
    difficulty: str = "standard"                         # routine, standard, challenging
    representation: str = "symbolic"                     # symbolic, word_problem, graphical

    # Attempt result
    correct: bool = False
    error_type: Optional[str] = None  # concept, algebra, logic, careless
    hint_used: bool = False
    solved_after_hint: bool = False
    used_photo: bool = False

    def to_dict(self) -> dict:
        return {
            "attempt_id": self.attempt_id,
            "user_id": self.user_id,
            "problem_id": self.problem_id,
            "timestamp": self.timestamp,
            "course": self.course,
            "topic": self.topic,
            "concepts": self.concepts,
            "skill_type": self.skill_type,
            "difficulty": self.difficulty,
            "representation": self.representation,
            "correct": self.correct,
            "error_type": self.error_type,
            "hint_used": self.hint_used,
            "solved_after_hint": self.solved_after_hint,
            "used_photo": self.used_photo,
        }


# ============================================================
# STATE UPDATER
# ============================================================

def update_state(state: StudentState, attempt: AttemptEvent) -> StudentState:
    """
    Update student state based on an attempt event.
    Returns a new state (immutable update).

    This is the core "learning" function of the system.
    """
    new_state = deepcopy(state)
    new_state.updated_at = datetime.now().isoformat()

    # Determine score delta
    if attempt.correct:
        if attempt.hint_used and attempt.solved_after_hint:
            delta = SCORE_CORRECT_WITH_HINT
        else:
            delta = SCORE_CORRECT
        new_state.total_correct += 1
    else:
        delta = SCORE_INCORRECT
        new_state.total_incorrect += 1

        # Track error type
        if attempt.error_type and attempt.error_type in new_state.error_counts:
            new_state.error_counts[attempt.error_type] += 1

    # Update topic mastery
    topic_ms = new_state.get_topic_mastery(attempt.topic)
    topic_ms.score = max(SCORE_MIN, min(SCORE_MAX, topic_ms.score + delta))
    topic_ms.record(attempt.correct)

    # Update concept mastery
    for concept in attempt.concepts:
        concept_ms = new_state.get_concept_mastery(concept)
        concept_ms.score = max(SCORE_MIN, min(SCORE_MAX, concept_ms.score + delta))
        concept_ms.record(attempt.correct)

    # Update orthogonal profile
    ortho_tags = {
        "skill_type": attempt.skill_type,
        "representation": attempt.representation,
        "difficulty": attempt.difficulty,
    }
    new_state.orthogonal.update(ortho_tags, attempt.correct, attempt.hint_used)

    # Check for foundation trigger (3+ consecutive failures)
    if topic_ms.streak <= -FOUNDATION_THRESHOLD:
        new_state.needs_foundation_work = True
        if attempt.topic not in new_state.foundation_topics:
            new_state.foundation_topics.append(attempt.topic)

    return new_state


def record_diagnostic(
    state: StudentState,
    score: float,
    weak_topics: list[str]
) -> StudentState:
    """Record diagnostic results into state."""
    new_state = deepcopy(state)
    new_state.diagnostic_completed = True
    new_state.diagnostic_score = score
    new_state.diagnostic_weak_topics = weak_topics
    new_state.updated_at = datetime.now().isoformat()

    # Initialize weak topics with low scores
    for topic in weak_topics:
        ms = new_state.get_topic_mastery(topic)
        ms.score = 0.3  # Start weak
        ms.incorrect += 1
        ms.attempts += 1
        ms.streak = -1

    # Flag for foundation if score < 50%
    if score < 0.5:
        new_state.needs_foundation_work = True

    return new_state
