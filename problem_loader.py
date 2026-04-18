"""
Problem Loader - Load UW Math problems from JSON files.

JSON Format:
{
  "id": "uw_math_124_au24_p1",
  "course": "math_124",
  "exam": "au24_final",
  "problem_number": 1,
  "topic": "limits",
  "concepts": ["limits", "algebraic_limits"],
  "points": 12,
  "stem": "Compute each of the following limits...",
  "parts": [
    {
      "label": "a",
      "question_text": "$\\lim_{x\\to 2} ...$",
      "final_answer": "$\\frac{2}{3}$",
      "has_diagram": false,
      "diagram_image": null
    }
  ]
}
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional
import streamlit as st

# Cache control via environment variable
# Set CLAIRE_DISABLE_CACHE=1 to disable caching during development
CACHE_ENABLED = os.environ.get("CLAIRE_DISABLE_CACHE", "0") != "1"
CACHE_TTL = 3600 if CACHE_ENABLED else 0  # 0 = no cache


@dataclass
class ProblemPart:
    """A single part of a problem (e.g., part a, b, c)."""
    label: Optional[str]  # "a", "b", "c", or None for single-part problems
    question_text: str
    final_answer: str
    has_diagram: bool = False
    diagram_image: Optional[str] = None  # Local path (legacy)
    diagram_image_url: Optional[str] = None  # Supabase public URL
    depends_on: Optional[str] = None


@dataclass
class Problem:
    """A UW Math exam problem with multiple parts."""
    id: str
    course: str
    exam: str
    problem_number: int
    topic: str
    concepts: list[str]
    points: int
    stem: Optional[str]  # Shared instruction for all parts
    parts: list[ProblemPart]

    def get_display_text(self, part_index: int = 0) -> str:
        """Get formatted text for display."""
        if part_index >= len(self.parts):
            return ""

        part = self.parts[part_index]
        text = ""

        # Add stem if exists
        if self.stem:
            text += f"{self.stem}\n\n"

        # Add part label if exists
        if part.label:
            text += f"**({part.label})** "

        text += part.question_text
        return text

    def get_source_label(self) -> str:
        """Get human-readable source label."""
        # "au24_final" -> "Autumn 2024 Final"
        exam = self.exam
        season = {"au": "Autumn", "wi": "Winter", "sp": "Spring", "su": "Summer"}.get(exam[:2], "")
        year = "20" + exam[2:4] if len(exam) >= 4 else ""
        exam_type = exam.split("_")[-1].title() if "_" in exam else "Exam"
        return f"{season} {year} {exam_type} - Problem {self.problem_number}"


def load_problems_from_file(filepath: str) -> list[Problem]:
    """Load problems from a single JSON file."""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        problems = []
        for item in data:
            parts = []
            for p in item.get("parts", []):
                parts.append(ProblemPart(
                    label=p.get("label"),
                    question_text=p.get("question_text", ""),
                    final_answer=p.get("final_answer", ""),
                    has_diagram=p.get("has_diagram", False),
                    diagram_image=p.get("diagram_image"),
                    diagram_image_url=p.get("diagram_image_url"),
                    depends_on=p.get("depends_on"),
                ))

            problems.append(Problem(
                id=item.get("id", ""),
                course=item.get("course", ""),
                exam=item.get("exam", ""),
                problem_number=item.get("problem_number", 0),
                topic=item.get("topic", ""),
                concepts=item.get("concepts", []),
                points=item.get("points", 0),
                stem=item.get("stem"),
                parts=parts,
            ))

        return problems

    except Exception as e:
        print(f"[problem_loader] Error loading {filepath}: {e}")
        return []


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_problems(course: str) -> list[Problem]:
    """
    Load all problems for a course (e.g., "124").

    Looks for files matching: problems/math124_*.json

    Cached for 1 hour to avoid repeated file I/O.
    Set CLAIRE_DISABLE_CACHE=1 to disable caching during development.
    """
    problems_dir = os.path.join(os.path.dirname(__file__), "problems")

    if not os.path.exists(problems_dir):
        print(f"[problem_loader] Problems directory not found")
        return []

    all_problems = []
    prefix = f"math{course}_"

    for filename in os.listdir(problems_dir):
        if filename.startswith(prefix) and filename.endswith(".json"):
            filepath = os.path.join(problems_dir, filename)
            problems = load_problems_from_file(filepath)
            all_problems.extend(problems)
            print(f"[problem_loader] Loaded {len(problems)} problems from {filename}")

    # Sort by exam date (newest first) and problem number (ascending)
    def exam_to_timestamp(exam_str):
        """Convert exam string to timestamp for sorting.
        Examples: 'au24_final' -> 2024.83, 'wi25_final' -> 2025.08
        """
        parts = exam_str.split('_')[0]  # "au24" or "wi25"
        season = parts[:2]  # "au", "wi", "sp", "su"
        year_short = parts[2:]  # "24", "25"
        year = int('20' + year_short) if year_short else 0  # 2024, 2025

        # Approximate month for each season (for chronological ordering)
        # Autumn = Oct, Winter = Jan, Spring = Apr, Summer = Jul
        season_month = {'au': 10, 'wi': 1, 'sp': 4, 'su': 7}
        month = season_month.get(season, 1)

        # Winter crosses calendar year: Winter 2025 = Jan 2025 (already in exam string)
        return year + month / 12.0

    all_problems.sort(key=lambda p: (-exam_to_timestamp(p.exam), p.problem_number))

    print(f"[problem_loader] Total: {len(all_problems)} problems for course {course}")
    return all_problems


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_all_parts(course: str) -> list[tuple[Problem, int]]:
    """
    Get all individual parts as (Problem, part_index) tuples.
    Useful for practice mode where each part is a separate question.

    Cached for 1 hour to avoid repeated processing.
    Set CLAIRE_DISABLE_CACHE=1 to disable caching during development.
    """
    problems = load_problems(course)
    parts = []
    for problem in problems:
        for i in range(len(problem.parts)):
            parts.append((problem, i))
    return parts


def get_problem_by_id(course: str, problem_id: str) -> Optional[Problem]:
    """Get a specific problem by ID."""
    problems = load_problems(course)
    for p in problems:
        if p.id == problem_id:
            return p
    return None
