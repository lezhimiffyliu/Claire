"""
Session persistence for Claire.

Stores parsed question banks, user level, and placement results as JSON
files on disk, keyed by a short session ID that lives in the URL (?s=<id>).

This means page refreshes or closing/reopening the tab don't lose context —
as long as the user keeps the URL (or bookmarks it).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Optional

SESSION_DIR = Path(__file__).parent / ".sessions"
SESSION_DIR.mkdir(exist_ok=True)


# ────────────────────────────────────────────────────────────
# ID helpers
# ────────────────────────────────────────────────────────────

def new_session_id() -> str:
    """Generate a short, URL-safe session ID (12 hex chars)."""
    return uuid.uuid4().hex[:12]


def session_path(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.json"


# ────────────────────────────────────────────────────────────
# Serialization helpers for domain objects
# ────────────────────────────────────────────────────────────

def _serialize_question(q) -> dict:
    """Convert a Question dataclass to a plain dict."""
    return {
        "id": q.id,
        "text": q.text,
        "source": q.source,
        "pattern": q.pattern,
        "problem_id": q.problem_id,
        "difficulty": q.difficulty,
        "categories": q.categories,
        "heuristic_file": q.heuristic_file,
        "solution": q.solution,
        "metadata": q.metadata,
    }


def _deserialize_question(d: dict):
    """Rebuild a Question dataclass from a plain dict."""
    from question_bank import Question
    return Question(
        id=d.get("id", ""),
        text=d.get("text", ""),
        source=d.get("source", ""),
        pattern=d.get("pattern", ""),
        problem_id=d.get("problem_id", ""),
        difficulty=d.get("difficulty", "medium"),
        categories=d.get("categories", []),
        heuristic_file=d.get("heuristic_file", ""),
        solution=d.get("solution"),
        metadata=d.get("metadata", {}),
    )


def _serialize_placement_result(r) -> Optional[dict]:
    if r is None:
        return None
    return {
        "level": r.level,
        "title": r.title,
        "summary": r.summary,
        "score": r.score,
        "total": r.total,
        "weak_topics": getattr(r, "weak_topics", []),
        "strong_topics": getattr(r, "strong_topics", []),
    }


def _deserialize_placement_result(d: Optional[dict]):
    if d is None:
        return None
    from placement_test import PlacementResult
    return PlacementResult(
        level=d["level"],
        title=d["title"],
        summary=d["summary"],
        score=d["score"],
        total=d["total"],
        weak_topics=d.get("weak_topics", []),
        strong_topics=d.get("strong_topics", []),
    )


def _serialize_placement_questions(qs: list) -> list[dict]:
    return [
        {
            "prompt": q.prompt,
            "choices": q.choices,
            "correct_index": q.correct_index,
            "explanation": q.explanation,
            "source": q.source,
            "difficulty": q.difficulty,
        }
        for q in qs
    ]


def _deserialize_placement_questions(lst: list[dict]) -> list:
    from placement_test import PlacementQuestion
    return [PlacementQuestion(**d) for d in lst]


# ────────────────────────────────────────────────────────────
# Save / load
# ────────────────────────────────────────────────────────────

def save_session(
    session_id: str,
    *,
    # exam context
    material_names: list[str],
    questions: list,          # list[Question]
    detected_patterns: list,  # list[PatternInfo] — just store name + priority
    # user state
    user_level: str,
    calc_track: Optional[str],
    placement_stage: str,
    placement_result,
    placement_questions: list,
    placement_answers: list,
) -> None:
    data = {
        "material_names": material_names,
        "questions": [_serialize_question(q) for q in questions],
        "detected_patterns": [
            {"name": p.name, "priority": p.priority, "score": p.score}
            for p in detected_patterns
        ],
        "user_level": user_level,
        "calc_track": calc_track,
        "placement_stage": placement_stage,
        "placement_result": _serialize_placement_result(placement_result),
        "placement_questions": _serialize_placement_questions(placement_questions),
        "placement_answers": placement_answers,
    }
    session_path(session_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2)
    )


def load_session(session_id: str) -> Optional[dict]:
    """
    Load a saved session.  Returns None if not found.
    Returns a plain dict; the caller reconstructs Streamlit state.
    """
    path = session_path(session_id)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
        return {
            "material_names": raw.get("material_names", []),
            "questions": [_deserialize_question(q) for q in raw.get("questions", [])],
            "detected_patterns": raw.get("detected_patterns", []),
            "user_level": raw.get("user_level", "intermediate"),
            "calc_track": raw.get("calc_track"),
            "placement_stage": raw.get("placement_stage", "not_started"),
            "placement_result": _deserialize_placement_result(raw.get("placement_result")),
            "placement_questions": _deserialize_placement_questions(
                raw.get("placement_questions", [])
            ),
            "placement_answers": raw.get("placement_answers", []),
        }
    except Exception as e:
        print(f"[session_store] Failed to load session {session_id}: {e}")
        return None


def delete_session(session_id: str) -> None:
    path = session_path(session_id)
    if path.exists():
        path.unlink()
