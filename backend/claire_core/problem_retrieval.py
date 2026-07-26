"""
claire_core.problem_retrieval — worked-example lookup over the UW problem corpus.

A first-cut, dependency-light retriever: it flattens the ~760-problem corpus
(loaded via `problem_loader`) into part-level records and ranks them by simple
topic/concept keyword overlap. No embeddings — keyword matching is enough to
surface a *similar solved problem* for the agent to teach from, and the corpus
is small enough to scan in memory.

Exposed to the agent as the `retrieve_teaching_example` tool (see `tools.py`).
Swapping in real vector search later means replacing `retrieve_examples` only;
the tool signature stays the same.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Flattened, per-course corpus cache: course -> list of example records.
_CORPUS_CACHE: Dict[str, List[dict]] = {}


def _corpus(course: str) -> List[dict]:
    """Flatten the course's problems into searchable part-level records.

    Records keep only what a teaching example needs (question + answer + labels).
    `problem_loader.load_problems` already returns problems newest-exam-first, so
    ties in the ranking below naturally prefer recent exams.
    """
    if course in _CORPUS_CACHE:
        return _CORPUS_CACHE[course]

    try:
        from app.content.problem_loader import load_problems

        problems = load_problems(course)
    except Exception as exc:  # pragma: no cover - data/env dependent
        logger.warning("problem_retrieval: could not load course %s: %s", course, exc)
        problems = []

    records: List[dict] = []
    for p in problems:
        for part in p.parts:
            if not (part.question_text or "").strip():
                continue
            records.append(
                {
                    "id": f"{p.id}:{part.label or '_'}",
                    "exam": p.exam,
                    "problem_number": p.problem_number,
                    "topic": p.topic or "",
                    "concepts": p.concepts or [],
                    "label": part.label,
                    "question_text": part.question_text or "",
                    "final_answer": part.final_answer or "",
                    "source": p.get_source_label() if hasattr(p, "get_source_label") else p.exam,
                }
            )

    _CORPUS_CACHE[course] = records
    return records


def retrieve_examples(
    topic: str,
    error_type: Optional[str] = None,
    course: str = "124",
    limit: int = 2,
) -> List[dict]:
    """Rank corpus examples by topic/concept overlap (+ optional error keywords).

    Returns up to `limit` example records (dicts). Deterministic: stable sort on
    score preserves the corpus's newest-first order for ties.
    """
    records = _corpus(course)
    if not records:
        return []

    tq = (topic or "").lower().strip()
    et_words = (error_type or "").lower().replace("_", " ").split()

    scored = []
    for r in records:
        score = 0
        rtopic = r["topic"].lower()
        concepts = [c.lower() for c in r["concepts"]]

        if tq:
            if rtopic == tq:
                score += 3
            elif tq in rtopic or rtopic in tq:
                score += 2
            if any(tq in c or c in tq for c in concepts):
                score += 2

        if et_words:
            haystack = " ".join([rtopic, " ".join(concepts), r["question_text"].lower()])
            score += sum(1 for w in et_words if w and w in haystack)

        # With no topic given, keep everything (score 0) so we still return the
        # most recent examples rather than nothing.
        if score > 0 or not tq:
            scored.append((score, r))

    scored.sort(key=lambda sr: -sr[0])  # stable → recent-first within a score
    return [r for _, r in scored[: max(0, limit)]]


def _format_examples(records: List[dict]) -> str:
    if not records:
        return "No matching worked examples found in the corpus."
    blocks = []
    for r in records:
        tag = r["topic"] or "example"
        if r["concepts"]:
            tag += " / " + ", ".join(r["concepts"][:2])
        blocks.append(
            f"EXAMPLE ({tag}) — {r['source']}\n"
            f"Q: {r['question_text']}\n"
            f"A: {r['final_answer'] or '(answer not recorded)'}"
        )
    return "\n\n".join(blocks)


@tool
def retrieve_teaching_example(
    topic: str,
    error_type: str = "",
    course: str = "124",
) -> str:
    """Fetch 1-2 solved example problems similar to what the student is working on.

    Use this during teaching to ground a hint in a concrete, already-solved
    problem of the same type (e.g. show how the chain rule applies elsewhere).
    These are DIFFERENT problems from the corpus, so it is fine to show their
    answers — do not reveal the CURRENT problem's answer.

    Args:
        topic: The problem topic/concept, e.g. "derivatives", "related_rates",
            "chain_rule", "optimization".
        error_type: Optional misconception to bias toward, e.g.
            "chain_rule_omission", "algebra_error".
        course: Course code, one of "124", "125", "126". Defaults to "124".
    """
    records = retrieve_examples(topic, error_type or None, course=course or "124", limit=2)
    return _format_examples(records)
