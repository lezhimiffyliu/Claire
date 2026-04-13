"""
Problem Loader - Load problems from JSON files for each course.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Problem:
    """A practice problem with solution."""
    id: str
    question: str  # LaTeX formatted
    solution_steps: list[str]
    final_answer: str
    topic: str
    difficulty: str  # easy, medium, hard

    def get_display_text(self) -> str:
        """Return question text for display."""
        return self.question


def load_problems(course: str) -> list[Problem]:
    """
    Load problems for a specific course.

    Args:
        course: "124", "125", or "126"

    Returns:
        List of Problem objects
    """
    problems_dir = os.path.join(os.path.dirname(__file__), "problems")
    filepath = os.path.join(problems_dir, f"{course}.json")

    if not os.path.exists(filepath):
        print(f"[problem_loader] No problems file for course {course}")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        problems = []
        for item in data:
            problems.append(Problem(
                id=item.get("id", ""),
                question=item.get("question", ""),
                solution_steps=item.get("solution_steps", []),
                final_answer=item.get("final_answer", ""),
                topic=item.get("topic", ""),
                difficulty=item.get("difficulty", "medium"),
            ))

        print(f"[problem_loader] Loaded {len(problems)} problems for course {course}")
        return problems

    except Exception as e:
        print(f"[problem_loader] Error loading {filepath}: {e}")
        return []


def get_problem_by_id(course: str, problem_id: str) -> Optional[Problem]:
    """Get a specific problem by ID."""
    problems = load_problems(course)
    for p in problems:
        if p.id == problem_id:
            return p
    return None


def get_random_problem(course: str, topic: Optional[str] = None) -> Optional[Problem]:
    """Get a random problem, optionally filtered by topic."""
    import random
    problems = load_problems(course)

    if not problems:
        return None

    if topic:
        problems = [p for p in problems if p.topic == topic]

    if not problems:
        return None

    return random.choice(problems)
