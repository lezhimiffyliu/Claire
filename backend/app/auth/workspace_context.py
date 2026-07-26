# workspace_context.py
"""
Workspace context for API backend.
All queries use authenticated client (RLS enforced via auth.uid()).
Provides EXAMPLE-LEVEL memory (specific past attempts, not just summaries).

Security:
- All queries go through RLS (user_id = auth.uid())
- No service_role key used
"""
from dataclasses import dataclass
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class PastAttempt:
    """A past attempt with full context for agent memory."""
    question_id: str
    topic: str
    is_correct: bool
    error_type: Optional[str]
    user_answer: Optional[str]
    problem_summary: str  # Brief description of the problem
    submitted_at: str


@dataclass
class WorkspaceContextAPI:
    """
    Workspace context loaded via authenticated Supabase client.
    RLS ensures user can only access their own data.
    """
    workspace_id: str
    user_id: str
    course: str
    profile_data: dict
    recent_attempts: List[dict]
    auth_client: any  # Keep client for additional queries

    @classmethod
    def load(cls, user_id: str, auth_client) -> Optional['WorkspaceContextAPI']:
        """
        Load active workspace with FULL attempt data.

        Args:
            user_id: Verified user ID from JWT
            auth_client: Supabase client with auth set (RLS enforced)

        Returns:
            WorkspaceContextAPI if workspace found, None otherwise
        """
        if not auth_client:
            return None

        try:
            # Query active workspace (RLS: user_id = auth.uid())
            result = auth_client.table("workspaces").select(
                "id, course, student_profiles(profile_data)"
            ).eq("is_active", True).limit(1).execute()

            if not result.data:
                logger.debug(f"No active workspace found for user {user_id}")
                return None

            ws = result.data[0]
            profiles = ws.get("student_profiles", [])
            profile_data = profiles[0].get("profile_data", {}) if profiles else {}

            # Query recent attempts WITH full details (RLS enforced)
            attempts = auth_client.table("attempt_history").select(
                "question_id, topic, is_correct, error_type, final_answer, "
                "analysis_summary, submitted_at"
            ).eq("workspace_id", ws["id"]).order(
                "submitted_at", desc=True
            ).limit(50).execute()

            return cls(
                workspace_id=ws["id"],
                user_id=user_id,
                course=ws["course"],
                profile_data=profile_data,
                recent_attempts=attempts.data or [],
                auth_client=auth_client
            )

        except Exception as e:
            logger.warning(f"Failed to load workspace context: {e}")
            return None

    def get_similar_attempts(
        self,
        current_problem_id: str,
        topic: str,
        limit: int = 2
    ) -> List[PastAttempt]:
        """
        Get 1-2 most similar past attempts for example-level memory.

        Similarity criteria:
        1. Same topic (required)
        2. Prefer attempts with errors (more instructive)
        3. Prefer recent attempts

        Args:
            current_problem_id: ID of current problem (to exclude)
            topic: Topic to match
            limit: Max attempts to return

        Returns:
            List of PastAttempt objects
        """
        # Filter by topic
        topic_attempts = [
            a for a in self.recent_attempts
            if a.get("topic") == topic and a.get("question_id") != current_problem_id
        ]

        if not topic_attempts:
            return []

        # Sort: errors first (more instructive), then by recency
        topic_attempts.sort(
            key=lambda a: (a.get("is_correct", True), a.get("submitted_at", "")),
            reverse=False  # False first = errors first
        )

        # Get problem summaries for top attempts
        results = []
        for attempt in topic_attempts[:limit]:
            # Load problem text for context
            problem_summary = self._get_problem_summary(attempt.get("question_id"))

            results.append(PastAttempt(
                question_id=attempt.get("question_id", ""),
                topic=attempt.get("topic", ""),
                is_correct=attempt.get("is_correct", False),
                error_type=attempt.get("error_type"),
                user_answer=attempt.get("final_answer"),
                problem_summary=problem_summary,
                submitted_at=attempt.get("submitted_at", "")
            ))

        return results

    def _get_problem_summary(self, question_id: str) -> str:
        """Get brief problem description from problems JSON."""
        try:
            from app.content.problem_loader import get_problem_by_id
            problem = get_problem_by_id(self.course, question_id)
            if not problem:
                return f"Problem {question_id}"

            # Create brief summary
            stem = problem.stem or ""
            if len(stem) > 150:
                stem = stem[:150] + "..."

            topic_display = problem.topic.replace("_", " ").title()
            return f"{topic_display}: {stem}"

        except Exception as e:
            logger.debug(f"Failed to get problem summary: {e}")
            return f"Problem {question_id}"

    def build_example_memory(
        self,
        current_problem_id: str,
        current_topic: str,
        current_problem_summary: str
    ) -> str:
        """
        Build EXAMPLE-LEVEL memory context for agent.
        Includes specific past attempts, not just summaries.

        PROTECTION: If no similar attempts found, return empty string.
        Agent will respond normally without memory injection.

        Args:
            current_problem_id: ID of problem being worked on
            current_topic: Topic of current problem
            current_problem_summary: Brief description of current problem

        Returns:
            Memory context string to inject into agent prompt,
            or empty string if no relevant history
        """
        similar_attempts = self.get_similar_attempts(current_problem_id, current_topic)

        # No similar attempts -> no memory injection
        if not similar_attempts:
            return ""

        # Build detailed context
        lines = ["[STUDENT MEMORY - EXAMPLE LEVEL]", ""]
        lines.append("PREVIOUS ATTEMPTS (same topic):")

        for i, attempt in enumerate(similar_attempts, 1):
            lines.append(f"")
            lines.append(f"Attempt {i}:")
            lines.append(f"  - Problem: {attempt.problem_summary}")
            lines.append(f"  - Result: {'Correct' if attempt.is_correct else 'Incorrect'}")

            if not attempt.is_correct and attempt.error_type:
                error_desc = {
                    "concept": "conceptual misunderstanding",
                    "algebra": "algebraic/computational error",
                    "logic": "logical reasoning error",
                    "careless": "careless mistake"
                }.get(attempt.error_type, attempt.error_type)
                lines.append(f"  - Error type: {error_desc}")

            if attempt.user_answer:
                # Truncate long answers
                answer = attempt.user_answer
                if len(answer) > 100:
                    answer = answer[:100] + "..."
                lines.append(f"  - Student's answer: {answer}")

        lines.append("")
        lines.append("CURRENT PROBLEM:")
        lines.append(f"  - Topic: {current_topic.replace('_', ' ').title()}")
        lines.append(f"  - Problem: {current_problem_summary}")
        lines.append("")
        lines.append("INSTRUCTION: When teaching, you MUST:")
        lines.append("  1. Reference the previous attempt(s) explicitly")
        lines.append("  2. Say 'This is similar to...' and describe the similarity")
        lines.append("  3. Say 'The key difference is...' to highlight what's new")
        lines.append("  4. If the student made an error before, address it:")
        lines.append("     'Last time you struggled with X, so pay attention to...'")

        return "\n".join(lines)

    def get_student_profile_v2(self):
        """
        Convert profile_data JSONB to StudentProfileV2.

        Returns:
            StudentProfileV2 instance
        """
        from app.teaching.student_profile_v2 import StudentProfileV2

        if not self.profile_data:
            return StudentProfileV2(course=self.course)

        return StudentProfileV2.from_dict(self.profile_data)

    def get_topic_stats(self) -> dict:
        """
        Get aggregated stats by topic from recent attempts.

        Returns:
            Dict mapping topic to {attempts, correct, accuracy}
        """
        topic_stats = {}

        for attempt in self.recent_attempts:
            topic = attempt.get("topic")
            if not topic:
                continue

            if topic not in topic_stats:
                topic_stats[topic] = {"attempts": 0, "correct": 0}

            topic_stats[topic]["attempts"] += 1
            if attempt.get("is_correct"):
                topic_stats[topic]["correct"] += 1

        # Calculate accuracy
        for topic, stats in topic_stats.items():
            stats["accuracy"] = (
                stats["correct"] / stats["attempts"]
                if stats["attempts"] > 0 else 0
            )

        return topic_stats
