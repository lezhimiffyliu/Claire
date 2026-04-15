"""
Student Profile - tracks mastery and error patterns.
Anonymous: stored in session state
Logged in: persisted to Supabase (via workspace)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import streamlit as st
import json
import os


@dataclass
class TopicEstimate:
    """
    Belief-based estimate for a topic.
    NOT a definitive mastery judgment.

    score: current estimated level (0-1), starts at 0.5 (neutral)
    attempts: number of questions attempted
    confidence: how certain we are (0-1), based on attempts
    """
    topic: str
    score: float = 0.5       # 0=weak, 1=strong, 0.5=unknown
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0

    @property
    def confidence(self) -> float:
        """Confidence grows with attempts. Need ~5 to be confident."""
        return min(1.0, self.attempts / 5)

    @property
    def priority_score(self) -> float:
        """
        Higher = more urgent to practice.
        Prioritizes: possibly weak + uncertain
        """
        return (1 - self.score) * (1 - self.confidence * 0.5)

    @property
    def status_label(self) -> str:
        """Human-readable status (NOT "weak/strong" judgments)."""
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

    def record(self, correct: bool):
        """Update estimate based on one attempt."""
        self.attempts += 1
        delta = 0.1 if correct else -0.1
        self.score = max(0.0, min(1.0, self.score + delta))

        if correct:
            self.correct += 1
        else:
            self.incorrect += 1


@dataclass
class StudentProfile:
    """
    Student profile based on belief estimation, not definitive judgment.

    Key principle: diagnostic ≠ mastery, diagnostic = initial belief.
    We track (score, confidence) not (weak/strong).
    """
    course: str  # "124", "125", "126"

    # Topic estimates: {topic_name: TopicEstimate}
    # NOT called "mastery" because we're estimating, not judging
    topic_estimates: dict = field(default_factory=dict)

    # Error pattern counts
    error_counts: dict = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })

    # Diagnostic results (initial estimate, NOT definitive)
    diagnostic_score: float = 0.0  # 0-1
    initial_focus_topics: list = field(default_factory=list)  # priority, not "weak"

    # Foundation flag (suggests, not asserts)
    suggest_foundation_review: bool = False

    # Total stats
    total_correct: int = 0
    total_incorrect: int = 0

    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "course": self.course,
            "topic_estimates": {
                k: {
                    "score": v.score,
                    "attempts": v.attempts,
                    "correct": v.correct,
                    "incorrect": v.incorrect,
                }
                for k, v in self.topic_estimates.items()
            },
            "error_counts": self.error_counts,
            "diagnostic_score": self.diagnostic_score,
            "initial_focus_topics": self.initial_focus_topics,
            "suggest_foundation_review": self.suggest_foundation_review,
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
        profile.initial_focus_topics = data.get("initial_focus_topics", [])
        profile.suggest_foundation_review = data.get("suggest_foundation_review", False)
        profile.total_correct = data.get("total_correct", 0)
        profile.total_incorrect = data.get("total_incorrect", 0)

        # Rebuild topic estimates
        for topic, stats in data.get("topic_estimates", {}).items():
            te = TopicEstimate(topic=topic)
            te.score = stats.get("score", 0.5)
            te.attempts = stats.get("attempts", 0)
            te.correct = stats.get("correct", 0)
            te.incorrect = stats.get("incorrect", 0)
            profile.topic_estimates[topic] = te

        return profile

    def record_diagnostic(self, score: float, focus_topics: list):
        """
        Record diagnostic results as INITIAL ESTIMATE, not definitive judgment.
        """
        from taxonomy import normalize_to_topic

        self.diagnostic_score = score

        # Normalize to canonical topics (not concepts)
        normalized = []
        for topic in focus_topics:
            canonical = normalize_to_topic(topic)
            if canonical not in normalized:
                normalized.append(canonical)

        self.initial_focus_topics = normalized

        # Suggest foundation review if score < 50% (not definitive)
        self.suggest_foundation_review = score < 0.5

        # Initialize estimates for focus topics
        # Start slightly below neutral (0.4) with low confidence
        for topic in normalized:
            if topic not in self.topic_estimates:
                self.topic_estimates[topic] = TopicEstimate(topic=topic)
            te = self.topic_estimates[topic]
            te.score = 0.4  # Slightly below neutral
            te.attempts = 1  # One signal from diagnostic
            te.incorrect = 1

    def record_attempt(self, topic: str, correct: bool, error_type: Optional[str] = None):
        """Record a practice attempt and update estimate."""
        from taxonomy import normalize_to_topic

        # Normalize to canonical topic
        canonical = normalize_to_topic(topic)

        # Get or create estimate
        if canonical not in self.topic_estimates:
            self.topic_estimates[canonical] = TopicEstimate(topic=canonical)

        # Update estimate
        self.topic_estimates[canonical].record(correct)

        # Update totals
        if correct:
            self.total_correct += 1
        else:
            self.total_incorrect += 1
            if error_type and error_type in self.error_counts:
                self.error_counts[error_type] += 1

    def get_priority_topics(self) -> list[str]:
        """
        Get topics sorted by priority (most urgent first).
        Priority = possibly weak + uncertain.
        NOT called "weak topics" because we don't know for sure.
        """
        priorities = []
        for topic, estimate in self.topic_estimates.items():
            priorities.append((topic, estimate.priority_score, estimate.status_label))

        # Sort by priority_score descending
        priorities.sort(key=lambda x: -x[1])
        return [t[0] for t in priorities]

    # Backward compatibility alias
    def get_weak_topics(self) -> list[str]:
        """Alias for get_priority_topics (for backward compatibility)."""
        return self.get_priority_topics()

    # Backward compatibility property
    @property
    def diagnostic_weak_topics(self) -> list:
        """Alias for initial_focus_topics (backward compatibility)."""
        return self.initial_focus_topics

    @property
    def needs_foundation(self) -> bool:
        """Alias for suggest_foundation_review (backward compatibility)."""
        return self.suggest_foundation_review

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


# ============================================================
# SESSION STORAGE (anonymous users)
# ============================================================

def get_profile() -> Optional[StudentProfile]:
    """Get profile from session state."""
    return st.session_state.get("student_profile")


def save_profile(profile: StudentProfile):
    """Save profile to session state."""
    st.session_state.student_profile = profile


def create_profile(course: str) -> StudentProfile:
    """Create a new profile for a course."""
    profile = StudentProfile(course=course)
    save_profile(profile)
    return profile


def update_profile_from_diagnostic(score: float, weak_topics: list):
    """Update profile after diagnostic completion."""
    profile = get_profile()
    if profile:
        profile.record_diagnostic(score, weak_topics)
        save_profile(profile)


def update_profile_from_grading(topic: str, correct: bool, error_type: Optional[str] = None):
    """Update profile after a grading result."""
    profile = get_profile()
    if profile:
        profile.record_attempt(topic, correct, error_type)
        save_profile(profile)


# ============================================================
# SUPABASE PERSISTENCE (logged-in users)
# ============================================================

def _get_supabase_client():
    """Get authenticated Supabase client (with user session for RLS)."""
    try:
        from auth import get_authenticated_client
        return get_authenticated_client()
    except ImportError:
        return None


def get_or_create_workspace(user_id: str, course: str) -> Optional[str]:
    """
    Get or create a workspace for the user+course.
    Returns workspace_id or None on error.
    """
    client = _get_supabase_client()
    if not client:
        return None

    try:
        # Try to find existing workspace
        result = client.table("workspaces").select("id").eq(
            "user_id", user_id
        ).eq("course", course).execute()

        if result.data:
            return result.data[0]["id"]

        # Create new workspace
        result = client.table("workspaces").insert({
            "user_id": user_id,
            "course": course,
        }).execute()

        if result.data:
            workspace_id = result.data[0]["id"]
            # Also create empty student_profiles row (with user_id for RLS)
            client.table("student_profiles").insert({
                "workspace_id": workspace_id,
                "user_id": user_id,
                "profile_data": {},
            }).execute()
            return workspace_id

        return None
    except Exception as e:
        print(f"[student_profile] get_or_create_workspace error: {e}")
        return None


def load_from_supabase(workspace_id: str) -> Optional[StudentProfile]:
    """Load profile from Supabase by workspace_id."""
    client = _get_supabase_client()
    if not client:
        return None

    try:
        # Get workspace to know the course
        ws_result = client.table("workspaces").select("course").eq(
            "id", workspace_id
        ).execute()

        if not ws_result.data:
            return None

        course = ws_result.data[0]["course"]

        # Get profile data
        result = client.table("student_profiles").select("profile_data").eq(
            "workspace_id", workspace_id
        ).execute()

        if result.data and result.data[0]["profile_data"]:
            data = result.data[0]["profile_data"]
            data["course"] = course  # Ensure course is set
            return StudentProfile.from_dict(data)

        # No profile data yet, return fresh profile
        return StudentProfile(course=course)

    except Exception as e:
        print(f"[student_profile] load_from_supabase error: {e}")
        return None


def save_to_supabase(workspace_id: str, profile: StudentProfile) -> bool:
    """
    Save profile to Supabase with merge update.
    Only updates the fields present in profile_data, preserving others.
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        profile_data = profile.to_dict()
        # Remove course from profile_data (it's in workspace)
        profile_data.pop("course", None)

        # Use the merge function for partial update
        client.rpc("merge_profile_data", {
            "p_workspace_id": workspace_id,
            "p_updates": profile_data,
        }).execute()

        return True
    except Exception as e:
        print(f"[student_profile] save_to_supabase error: {e}")
        # Fallback: try direct upsert
        try:
            client.table("student_profiles").upsert({
                "workspace_id": workspace_id,
                "profile_data": profile.to_dict(),
            }).execute()
            return True
        except Exception as e2:
            print(f"[student_profile] save_to_supabase fallback error: {e2}")
            return False


def get_current_workspace_id() -> Optional[str]:
    """Get current workspace_id from session state."""
    return st.session_state.get("workspace_id")


def set_current_workspace_id(workspace_id: str):
    """Set current workspace_id in session state."""
    st.session_state.workspace_id = workspace_id


def sync_profile_to_supabase():
    """
    Sync current session profile to Supabase.
    Call this after any profile update for logged-in users.
    """
    from auth import get_user
    user = get_user()
    if not user:
        return  # Anonymous user, skip

    workspace_id = get_current_workspace_id()
    profile = get_profile()

    if workspace_id and profile:
        save_to_supabase(workspace_id, profile)
