"""
benchmarks.teaching_eval.rubric — the versioned, independently-authored judge rubric.

This rubric is written FOR EVALUATION and is deliberately NOT a copy of the
tutor's `SYSTEM_PROMPT`: judging against the same text the tutor was optimized on
would measure prompt-adherence, not teaching quality. Bumping `RUBRIC_VERSION`
whenever the criteria change keeps scorecards comparable over time.

Each dimension is scored 1-5 and REQUIRES a one-line evidence quote from the
transcript, so a score can always be traced to something the tutor actually said.
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple

from pydantic import BaseModel, Field

RUBRIC_VERSION = "v1"
SCORE_MIN = 1
SCORE_MAX = 5


class RubricDimension(NamedTuple):
    key: str
    title: str
    description: str
    # What a top (5) vs bottom (1) score looks like — anchors for the judge.
    high: str
    low: str


RUBRIC_DIMENSIONS: List[RubricDimension] = [
    RubricDimension(
        key="math_correctness",
        title="Mathematical correctness",
        description="Is every mathematical statement the tutor makes true?",
        high="All formulas, rules, and intermediate claims are correct.",
        low="Contains a false statement, wrong rule, or bad intermediate result.",
    ),
    RubricDimension(
        key="pedagogical_appropriateness",
        title="Pedagogical appropriateness",
        description="Does the move fit where the student is (right depth, right next step)?",
        high="Targets the actual gap and moves exactly one concrete step forward.",
        low="Off-target, too big a leap, or busywork that ignores the student's state.",
    ),
    RubricDimension(
        key="socratic_behavior",
        title="Socratic behaviour",
        description="Does the tutor guide with questions instead of handing over results?",
        high="Teaches the rule/idea, then ends with a question the student can act on.",
        low="Lectures, or gives the result outright with no student thinking required.",
    ),
    RubricDimension(
        key="repetition",
        title="Non-repetition / progression",
        description="Across turns, does the tutor go deeper rather than repeat itself?",
        high="Each turn adds something new; repeated hints escalate in depth.",
        low="Restates the same hint/explanation without advancing.",
    ),
    RubricDimension(
        key="history_utilization",
        title="History utilization",
        description="Does the tutor use the teaching history and student's prior work?",
        high="References what the student already tried / was told and builds on it.",
        low="Acts as if every turn is the first; ignores prior context.",
    ),
    RubricDimension(
        key="answer_leakage",
        title="Answer non-leakage",
        description="Does the tutor avoid revealing the final answer prematurely?",
        high="Never states the final answer before a sanctioned full solution.",
        low="Gives away the final answer (or an equivalent) too early.",
    ),
]

DIMENSION_KEYS = [d.key for d in RUBRIC_DIMENSIONS]


class DimensionScore(BaseModel):
    """A single rubric dimension's verdict."""

    score: int = Field(ge=SCORE_MIN, le=SCORE_MAX)
    evidence: str = Field(description="One-line quote/justification from the transcript.")


class JudgeVerdict(BaseModel):
    """Structured output of the LLM-as-judge over one trajectory."""

    rubric_version: str = RUBRIC_VERSION
    math_correctness: DimensionScore
    pedagogical_appropriateness: DimensionScore
    socratic_behavior: DimensionScore
    repetition: DimensionScore
    history_utilization: DimensionScore
    answer_leakage: DimensionScore
    overall: float = Field(description="Holistic 1-5 teaching-quality score.")
    notes: str = ""

    def dimension_scores(self) -> Dict[str, int]:
        return {k: getattr(self, k).score for k in DIMENSION_KEYS}


def render_rubric() -> str:
    """Human-readable rubric block for the judge prompt."""
    lines = [f"TEACHING RUBRIC ({RUBRIC_VERSION}). Score each 1-5 (5 = best):", ""]
    for i, d in enumerate(RUBRIC_DIMENSIONS, 1):
        lines.append(f"{i}. {d.title} [{d.key}] — {d.description}")
        lines.append(f"   5: {d.high}")
        lines.append(f"   1: {d.low}")
    lines.append("")
    lines.append(
        "For EACH dimension give an integer score and a one-line `evidence` quote "
        "from the transcript. Then give a holistic `overall` (1-5) and short `notes`."
    )
    return "\n".join(lines)
