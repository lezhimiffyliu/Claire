"""
Student Profile V2 - Hierarchical topic and subtopic tracking.

Key improvements over V1:
- Tracks mastery at both TOPIC and SUBTOPIC level
- Uses taxonomy to structure knowledge hierarchy
- Prioritizes weak subtopics within topics for targeted practice
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from taxonomy import get_subtopics, get_topic_for_subtopic, normalize_to_topic


@dataclass
class SubtopicEstimate:
    """
    Fine-grained estimate for a specific subtopic.

    Example: "polar_integral_setup" under "polar_coordinates"
    """
    subtopic: str
    score: float = 0.5       # 0=weak, 1=strong, 0.5=unknown
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0

    # Error type tracking
    error_counts: Dict[str, int] = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })
    last_error_type: Optional[str] = None

    # Recent performance tracking (NEW) ⭐
    recent_attempts: list = field(default_factory=list)  # Last K attempts [True, False, False, ...]
    recent_k: int = 5  # Track last 5 attempts

    # Hint-dependency tracking ⭐
    # correct_after_hint: correct attempts that only came AFTER a hint was given.
    # hint_used_count: attempts on this subtopic where the tutor gave a hint.
    correct_after_hint: int = 0
    hint_used_count: int = 0

    @property
    def confidence(self) -> float:
        """Confidence grows with attempts. Need ~3 to be confident."""
        return min(1.0, self.attempts / 3)

    @property
    def priority_score(self) -> float:
        """
        Higher = more urgent to practice.
        Same formula as V1, but at subtopic level.
        """
        return (1 - self.score) * (1 - self.confidence * 0.5)

    @property
    def status_label(self) -> str:
        """Human-readable status."""
        if self.attempts == 0:
            return "not yet tested"
        if self.confidence < 0.4:
            return "needs more signal"
        if self.score < 0.4:
            return "likely needs review"
        if self.score < 0.6:
            return "mixed results"
        if self.score < 0.8:
            return "showing progress"
        return "looking solid"

    @property
    def hint_dependency(self) -> float:
        """Fraction of correct answers on this subtopic that needed a hint.

        High (→1.0) means the student can only get it right with scaffolding;
        low (→0.0) means they can do it unaided. 0.0 if never correct.
        """
        if self.correct == 0:
            return 0.0
        return min(1.0, self.correct_after_hint / self.correct)

    def get_dominant_error_type(self) -> Optional[str]:
        """Get the most common error type for this subtopic."""
        if not any(self.error_counts.values()):
            return None
        return max(self.error_counts.items(), key=lambda x: x[1])[0]

    def get_recent_wrong_streak(self) -> int:
        """
        Get the current streak of consecutive wrong attempts (from most recent).

        Returns:
            Number of consecutive wrong attempts from the end of recent_attempts.
            E.g., [True, False, False] → 2
                  [False, False, True] → 0
                  [False, False, False] → 3
        """
        if not self.recent_attempts:
            return 0

        streak = 0
        # Count from the end backwards
        for attempt in reversed(self.recent_attempts):
            if attempt:  # Correct
                break
            streak += 1

        return streak

    def is_struggling_recently(self) -> bool:
        """
        Check if student is struggling with this subtopic recently.

        Criteria:
        - Has at least 2 recent attempts
        - Recent wrong streak >= 2 (2+ consecutive wrong)

        Returns:
            True if currently struggling, False otherwise
        """
        if len(self.recent_attempts) < 2:
            return False

        return self.get_recent_wrong_streak() >= 2

    def get_error_urgency_boost(self) -> float:
        """
        Get recommendation boost based on error type pattern.

        Error type urgency:
        - concept: 30 points (needs understanding, high priority)
        - logic: 25 points (needs reasoning practice)
        - algebra: 10 points (computational practice)
        - careless: 0 points (understands it, just needs care)

        Returns 0-30 based on dominant error type and error count.
        """
        dominant_error = self.get_dominant_error_type()
        if not dominant_error:
            return 0.0

        # Base boost by error type
        error_boosts = {
            "concept": 30,
            "logic": 25,
            "algebra": 10,
            "careless": 0,
        }

        base_boost = error_boosts.get(dominant_error, 0)

        # Scale by error frequency (more errors = more urgent)
        error_count = self.error_counts[dominant_error]
        if error_count == 0:
            return 0.0

        # Diminishing returns: 1 error = 100%, 2 = 100%, 3+ = 100%
        # (concept errors are always urgent)
        frequency_multiplier = min(1.0, error_count / 2) if dominant_error != "concept" else 1.0

        return base_boost * frequency_multiplier

    def get_recent_performance_boost(self) -> float:
        """
        Get recommendation boost based on RECENT performance.

        Recent struggle detection:
        - If recent wrong streak >= 2: +40 points (HIGH PRIORITY!)
        - If recent wrong streak == 1: +10 points (watch closely)
        - Otherwise: 0 points

        This makes the system highly responsive to current struggles.

        Returns:
            0-40 points based on recent wrong streak
        """
        wrong_streak = self.get_recent_wrong_streak()

        if wrong_streak >= 2:
            # Student is struggling RIGHT NOW → immediate high priority
            return 40.0
        elif wrong_streak == 1:
            # Just failed once, monitor
            return 10.0
        else:
            # Recent success or no recent attempts
            return 0.0

    def record(self, correct: bool, error_type: Optional[str] = None,
               used_hint: bool = False):
        """Update estimate based on one attempt.

        `used_hint` records whether the tutor scaffolded this attempt, feeding
        the hint-dependency signal.
        """
        self.attempts += 1
        delta = 0.1 if correct else -0.1
        self.score = max(0.0, min(1.0, self.score + delta))

        if used_hint:
            self.hint_used_count += 1

        if correct:
            self.correct += 1
            if used_hint:
                self.correct_after_hint += 1
        else:
            self.incorrect += 1

            # Track error type
            if error_type and error_type in self.error_counts:
                self.error_counts[error_type] += 1
                self.last_error_type = error_type

        # Track recent performance (NEW) ⭐
        self.recent_attempts.append(correct)
        # Keep only last K attempts
        if len(self.recent_attempts) > self.recent_k:
            self.recent_attempts.pop(0)


@dataclass
class TopicEstimateV2:
    """
    Topic-level estimate with subtopic breakdown.

    Structure:
    - Overall topic score (aggregated from subtopics)
    - Individual subtopic estimates
    """
    topic: str

    # Subtopic breakdown: {subtopic_name: SubtopicEstimate}
    subtopics: Dict[str, SubtopicEstimate] = field(default_factory=dict)

    # Topic-level aggregates (computed from subtopics)
    total_attempts: int = 0
    total_correct: int = 0
    total_incorrect: int = 0

    @property
    def score(self) -> float:
        """
        Overall topic score = average of subtopic scores.
        Weighted by attempts (more attempts = more weight).
        """
        if not self.subtopics:
            return 0.5  # Neutral if no subtopics

        total_weighted = 0.0
        total_weight = 0

        for sub in self.subtopics.values():
            if sub.attempts > 0:
                # Weight by attempts (more attempts = more reliable)
                weight = sub.attempts
                total_weighted += sub.score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.5

        return total_weighted / total_weight

    @property
    def confidence(self) -> float:
        """Topic confidence = based on total attempts across subtopics."""
        return min(1.0, self.total_attempts / 8)

    @property
    def priority_score(self) -> float:
        """
        Topic priority = highest priority among subtopics.
        We want to surface the weakest subtopic.
        """
        if not self.subtopics:
            return (1 - self.score) * (1 - self.confidence * 0.5)

        # Return max priority among subtopics
        max_priority = max(
            (sub.priority_score for sub in self.subtopics.values()),
            default=0.5
        )
        return max_priority

    @property
    def status_label(self) -> str:
        """Topic status based on aggregated score."""
        if self.total_attempts == 0:
            return "not yet tested"
        if self.confidence < 0.4:
            return "needs more signal"
        if self.score < 0.4:
            return "likely needs review"
        if self.score < 0.6:
            return "mixed results"
        if self.score < 0.8:
            return "showing progress"
        return "looking solid"

    def get_or_create_subtopic(self, subtopic: str) -> SubtopicEstimate:
        """Get existing or create new subtopic estimate."""
        if subtopic not in self.subtopics:
            self.subtopics[subtopic] = SubtopicEstimate(subtopic=subtopic)
        return self.subtopics[subtopic]

    def record_subtopic(self, subtopic: str, correct: bool,
                        error_type: Optional[str] = None, used_hint: bool = False):
        """Record an attempt at a specific subtopic."""
        sub_est = self.get_or_create_subtopic(subtopic)
        sub_est.record(correct, error_type, used_hint=used_hint)

        # Update topic-level aggregates
        self.total_attempts += 1
        if correct:
            self.total_correct += 1
        else:
            self.total_incorrect += 1

    def get_weakest_subtopics(self, limit: int = 3) -> list[str]:
        """
        Get the weakest subtopics within this topic.
        Returns subtopic names sorted by priority (highest first).
        """
        if not self.subtopics:
            return []

        # Sort by priority_score descending
        sorted_subs = sorted(
            self.subtopics.values(),
            key=lambda s: -s.priority_score
        )

        return [s.subtopic for s in sorted_subs[:limit]]

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "topic": self.topic,
            "subtopics": {
                k: {
                    "score": v.score,
                    "attempts": v.attempts,
                    "correct": v.correct,
                    "incorrect": v.incorrect,
                    "error_counts": v.error_counts,
                    "last_error_type": v.last_error_type,
                    "recent_attempts": v.recent_attempts,
                    "correct_after_hint": v.correct_after_hint,
                    "hint_used_count": v.hint_used_count,
                }
                for k, v in self.subtopics.items()
            },
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "total_incorrect": self.total_incorrect,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopicEstimateV2":
        """Deserialize from storage."""
        topic = data.get("topic", "")
        te = cls(topic=topic)
        te.total_attempts = data.get("total_attempts", 0)
        te.total_correct = data.get("total_correct", 0)
        te.total_incorrect = data.get("total_incorrect", 0)

        # Rebuild subtopics
        for subtopic, stats in data.get("subtopics", {}).items():
            sub = SubtopicEstimate(subtopic=subtopic)
            sub.score = stats.get("score", 0.5)
            sub.attempts = stats.get("attempts", 0)
            sub.correct = stats.get("correct", 0)
            sub.incorrect = stats.get("incorrect", 0)
            sub.error_counts = stats.get("error_counts", {
                "concept": 0, "algebra": 0, "logic": 0, "careless": 0
            })
            sub.last_error_type = stats.get("last_error_type")
            sub.recent_attempts = stats.get("recent_attempts", [])
            sub.correct_after_hint = stats.get("correct_after_hint", 0)
            sub.hint_used_count = stats.get("hint_used_count", 0)
            te.subtopics[subtopic] = sub

        return te


@dataclass
class StudentProfileV2:
    """
    Enhanced student profile with hierarchical topic/subtopic tracking.

    Key changes from V1:
    - topic_estimates is now {topic: TopicEstimateV2} with nested subtopics
    - Can track mastery at fine-grained level
    - Priority system surfaces weakest subtopics within weak topics
    """
    course: str  # "124", "125", "126"

    # Hierarchical topic estimates: {topic_name: TopicEstimateV2}
    topic_estimates: Dict[str, TopicEstimateV2] = field(default_factory=dict)

    # Error pattern counts (unchanged from V1)
    error_counts: dict = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })

    # Diagnostic results (unchanged from V1)
    diagnostic_score: float = 0.0
    initial_focus_topics: list = field(default_factory=list)
    suggest_foundation_review: bool = False

    # Total stats (unchanged from V1)
    total_correct: int = 0
    total_incorrect: int = 0

    # Question-level history (NEW) ⭐
    # {question_id: {attempts, correct, last_result, last_seen}}
    question_history: Dict[str, dict] = field(default_factory=dict)

    def get_or_create_topic(self, topic: str) -> TopicEstimateV2:
        """Get existing or create new topic estimate."""
        if topic not in self.topic_estimates:
            self.topic_estimates[topic] = TopicEstimateV2(topic=topic)
        return self.topic_estimates[topic]

    def record_attempt(
        self,
        topic: str,
        subtopic: Optional[str],
        correct: bool,
        error_type: Optional[str] = None,
        question_id: Optional[str] = None,
        used_hint: bool = False
    ):
        """
        Record a practice attempt at topic and/or subtopic level.

        Args:
            topic: Canonical topic name (e.g., "double_integrals")
            subtopic: Optional subtopic name (e.g., "integration_bounds_setup")
            correct: Whether the attempt was correct
            error_type: Optional error classification
            question_id: Optional question ID for question-level tracking
            used_hint: Whether the tutor scaffolded this attempt (hint dependency)
        """
        # Normalize topic
        canonical = normalize_to_topic(topic, self.course)

        # Get or create topic estimate
        topic_est = self.get_or_create_topic(canonical)

        if subtopic:
            # Record at subtopic level
            topic_est.record_subtopic(subtopic, correct, error_type, used_hint=used_hint)
        else:
            # Record at topic level (no specific subtopic)
            # Still update topic aggregates
            topic_est.total_attempts += 1
            if correct:
                topic_est.total_correct += 1
            else:
                topic_est.total_incorrect += 1

        # Update profile totals
        if correct:
            self.total_correct += 1
        else:
            self.total_incorrect += 1
            if error_type and error_type in self.error_counts:
                self.error_counts[error_type] += 1

        # Record question-level history (NEW) ⭐
        if question_id:
            self.record_question_attempt(question_id, correct)

    def record_question_attempt(self, question_id: str, correct: bool):
        """
        Record an attempt on a specific question.

        Updates question_history with:
        - attempts count
        - correct count
        - last_result (bool)
        - last_seen (timestamp)
        """
        from datetime import datetime

        if question_id not in self.question_history:
            self.question_history[question_id] = {
                "attempts": 0,
                "correct": 0,
                "last_result": None,
                "last_seen": None,
            }

        qh = self.question_history[question_id]
        qh["attempts"] += 1
        if correct:
            qh["correct"] += 1
        qh["last_result"] = correct
        qh["last_seen"] = datetime.now().isoformat()

    def get_question_boost(
        self,
        question_id: str,
        current_session_questions: Optional[list] = None
    ) -> float:
        """
        Calculate recommendation boost/penalty for a specific question.

        Strategy:
        - Never seen (attempts=0): 0 points (neutral)
        - Last wrong: +20~30 points (reinforce error correction)
        - Last correct: -10~-20 points (reduce short-term repetition)
        - Time decay: If last_seen is old (>1 day), gradually restore weight
        - Short-term suppression: If in recent K questions, heavy penalty (-40)

        Args:
            question_id: Question identifier
            current_session_questions: List of recently attempted question_ids

        Returns:
            Boost score (-40 to +30)
        """
        from datetime import datetime, timedelta

        # Not seen before → neutral
        if question_id not in self.question_history:
            return 0.0

        qh = self.question_history[question_id]
        boost = 0.0

        # Short-term suppression: Recently attempted in this session
        if current_session_questions and question_id in current_session_questions[-10:]:
            # Within last 10 questions → strong suppression
            return -40.0

        # Base boost from last result
        if qh["last_result"] is not None:
            if qh["last_result"]:
                # Last correct → reduce repetition
                boost = -15.0
            else:
                # Last wrong → reinforce practice
                boost = +25.0

        # Time decay: If seen long ago, reduce penalty/boost
        if qh["last_seen"]:
            last_seen = datetime.fromisoformat(qh["last_seen"])
            hours_since = (datetime.now() - last_seen).total_seconds() / 3600

            if hours_since > 24:  # More than 1 day
                # Gradually restore weight (reduce magnitude)
                decay_factor = min(1.0, hours_since / (24 * 7))  # Full decay after 1 week
                boost *= (1 - decay_factor * 0.7)  # Reduce boost/penalty by up to 70%

        return boost

    def get_priority_topics(self) -> list[str]:
        """
        Get topics sorted by priority (most urgent first).
        Uses the new priority_score which considers weakest subtopics.
        """
        priorities = []
        for topic, estimate in self.topic_estimates.items():
            priorities.append((topic, estimate.priority_score, estimate.status_label))

        # Sort by priority_score descending
        priorities.sort(key=lambda x: -x[1])
        return [t[0] for t in priorities]

    def get_priority_subtopics(self, topic: str, limit: int = 3) -> list[str]:
        """
        Get weakest subtopics within a specific topic.

        Returns:
            List of subtopic names sorted by priority (highest first)
        """
        if topic not in self.topic_estimates:
            # Return all subtopics for this topic from taxonomy
            return get_subtopics(self.course, topic)[:limit]

        return self.topic_estimates[topic].get_weakest_subtopics(limit)

    def get_all_priority_subtopics(self, limit: int = 10) -> list[tuple[str, str]]:
        """
        Get weakest subtopics across ALL topics.

        Returns:
            List of (topic, subtopic) tuples sorted by priority
        """
        all_subtopics = []

        for topic, topic_est in self.topic_estimates.items():
            for subtopic, sub_est in topic_est.subtopics.items():
                all_subtopics.append((
                    topic,
                    subtopic,
                    sub_est.priority_score,
                    sub_est.status_label
                ))

        # Sort by priority descending
        all_subtopics.sort(key=lambda x: -x[2])

        return [(t[0], t[1]) for t in all_subtopics[:limit]]

    def record_diagnostic(self, score: float, focus_topics: list):
        """
        Record diagnostic results as INITIAL ESTIMATE.
        Initialize subtopics from taxonomy for focus topics.
        """
        self.diagnostic_score = score

        # Normalize to canonical topics
        normalized = []
        for topic in focus_topics:
            canonical = normalize_to_topic(topic, self.course)
            if canonical not in normalized:
                normalized.append(canonical)

        self.initial_focus_topics = normalized
        self.suggest_foundation_review = score < 0.5

        # Initialize topic estimates with all subtopics from taxonomy
        for topic in normalized:
            if topic not in self.topic_estimates:
                topic_est = TopicEstimateV2(topic=topic)

                # Initialize all subtopics for this topic
                subtopics = get_subtopics(self.course, topic)
                for subtopic in subtopics:
                    sub_est = SubtopicEstimate(subtopic=subtopic)
                    sub_est.score = 0.4  # Slightly below neutral
                    sub_est.attempts = 0  # No attempts yet, will update when practiced
                    topic_est.subtopics[subtopic] = sub_est

                self.topic_estimates[topic] = topic_est

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "course": self.course,
            "topic_estimates": {
                k: v.to_dict() for k, v in self.topic_estimates.items()
            },
            "error_counts": self.error_counts,
            "diagnostic_score": self.diagnostic_score,
            "initial_focus_topics": self.initial_focus_topics,
            "suggest_foundation_review": self.suggest_foundation_review,
            "total_correct": self.total_correct,
            "total_incorrect": self.total_incorrect,
            "question_history": self.question_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudentProfileV2":
        """Deserialize from storage."""
        profile = cls(course=data.get("course", "124"))
        profile.error_counts = data.get("error_counts", {
            "concept": 0, "algebra": 0, "logic": 0, "careless": 0
        })
        profile.diagnostic_score = data.get("diagnostic_score", 0.0)
        profile.initial_focus_topics = data.get("initial_focus_topics", [])
        profile.suggest_foundation_review = data.get("suggest_foundation_review", False)
        profile.total_correct = data.get("total_correct", 0)
        profile.total_incorrect = data.get("total_incorrect", 0)
        profile.question_history = data.get("question_history", {})

        # Rebuild topic estimates
        for topic, topic_data in data.get("topic_estimates", {}).items():
            profile.topic_estimates[topic] = TopicEstimateV2.from_dict(topic_data)

        return profile

    # Backward compatibility properties
    @property
    def diagnostic_weak_topics(self) -> list:
        """Alias for initial_focus_topics (backward compatibility)."""
        return self.initial_focus_topics

    @property
    def needs_foundation(self) -> bool:
        """Alias for suggest_foundation_review (backward compatibility)."""
        return self.suggest_foundation_review

    @property
    def overall_accuracy(self) -> float:
        total = self.total_correct + self.total_incorrect
        if total == 0:
            return 0.0
        return self.total_correct / total

    def get_dominant_error_type(self) -> Optional[str]:
        """Get the most common error type."""
        if not any(self.error_counts.values()):
            return None
        return max(self.error_counts.items(), key=lambda x: x[1])[0]


# ============================================================
# MIGRATION from V1 to V2
# ============================================================

def migrate_from_v1(old_profile: "StudentProfile") -> StudentProfileV2:
    """
    Migrate old V1 profile to V2 format.

    Converts flat TopicEstimate to hierarchical TopicEstimateV2.
    Initializes subtopics from taxonomy.
    """
    new_profile = StudentProfileV2(course=old_profile.course)

    # Copy simple fields
    new_profile.error_counts = old_profile.error_counts.copy()
    new_profile.diagnostic_score = old_profile.diagnostic_score
    new_profile.initial_focus_topics = old_profile.initial_focus_topics.copy()
    new_profile.suggest_foundation_review = old_profile.suggest_foundation_review
    new_profile.total_correct = old_profile.total_correct
    new_profile.total_incorrect = old_profile.total_incorrect

    # Migrate topic estimates
    for topic, old_est in old_profile.topic_estimates.items():
        # Create new topic estimate
        new_topic_est = TopicEstimateV2(topic=topic)
        new_topic_est.total_attempts = old_est.attempts
        new_topic_est.total_correct = old_est.correct
        new_topic_est.total_incorrect = old_est.incorrect

        # Initialize subtopics from taxonomy
        subtopics = get_subtopics(new_profile.course, topic)
        for subtopic in subtopics:
            # Create subtopic with inherited topic score
            # (we don't have subtopic-level data from V1)
            sub_est = SubtopicEstimate(subtopic=subtopic)
            sub_est.score = old_est.score  # Inherit from parent topic
            sub_est.attempts = 0  # No subtopic-level data yet
            new_topic_est.subtopics[subtopic] = sub_est

        new_profile.topic_estimates[topic] = new_topic_est

    return new_profile


# ============================================================
# SESSION STORAGE (anonymous users)
# ============================================================

def get_profile_v2() -> Optional[StudentProfileV2]:
    """Deprecated Streamlit session storage — no-op in the API (returns None)."""
    return None


def save_profile_v2(profile: StudentProfileV2):
    """Deprecated Streamlit session storage — no-op in the API."""
    return None


def create_profile_v2(course: str) -> StudentProfileV2:
    """Create a new V2 profile for a course."""
    profile = StudentProfileV2(course=course)
    save_profile_v2(profile)
    return profile
