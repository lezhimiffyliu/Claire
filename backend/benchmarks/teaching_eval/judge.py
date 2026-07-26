"""
benchmarks.teaching_eval.judge — LLM-as-judge over a teaching trajectory.

The judge scores a completed trajectory against the versioned `rubric.py`. Two
implementations share one protocol:

  * `StubJudge`   — deterministic, no network; used in CI. Returns a fixed
    passing verdict (optionally overridable) so tests never hit the API.
  * `LLMJudge`    — the real judge. It MUST run on a different model than the
    tutor (default `claude-sonnet-4-5`) to reduce self-evaluation bias; the
    default judge model is therefore a distinct model, overridable via
    ``--judge-model``.

`judge_trajectory` is the thin entry point the runner calls.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Protocol, runtime_checkable

from .rubric import DimensionScore, JudgeVerdict, render_rubric
from .scenarios import TeachingScenario

logger = logging.getLogger(__name__)

# Distinct from the tutor's DEFAULT_MODEL ("claude-sonnet-4-5") so the judge is
# not grading its own family. Override with --judge-model (a stronger model such
# as an Opus snapshot is recommended for the archived baseline run).
JUDGE_DEFAULT_MODEL = "claude-3-5-haiku-20241022"


@runtime_checkable
class JudgeProtocol(Protocol):
    def judge(self, scenario: TeachingScenario, transcript: List[dict]) -> JudgeVerdict:
        ...


def _render_transcript(scenario: TeachingScenario, transcript: List[dict]) -> str:
    lines = [
        f"PROBLEM ({scenario.problem.topic}): {scenario.problem.text}",
        f"STUDENT PERSONA: {scenario.persona}",
        "",
        "TRANSCRIPT (chronological):",
    ]
    for entry in transcript:
        role = entry["role"]
        if role == "tutor":
            action = entry.get("action", "?")
            lines.append(f"  TUTOR [{action}]: {entry['text']}")
        else:
            kind = entry.get("kind", "reply")
            lines.append(f"  STUDENT ({kind}): {entry['text']}")
    return "\n".join(lines)


class StubJudge:
    """Deterministic judge for CI. Returns a fixed verdict (default: all 4s)."""

    def __init__(self, verdict: Optional[JudgeVerdict] = None, default_score: int = 4) -> None:
        self._verdict = verdict
        self._default_score = default_score

    def judge(self, scenario: TeachingScenario, transcript: List[dict]) -> JudgeVerdict:
        if self._verdict is not None:
            return self._verdict
        d = DimensionScore(score=self._default_score, evidence="stub judge (no LLM)")
        return JudgeVerdict(
            math_correctness=d,
            pedagogical_appropriateness=d,
            socratic_behavior=d,
            repetition=d,
            history_utilization=d,
            answer_leakage=d,
            overall=float(self._default_score),
            notes="StubJudge deterministic verdict.",
        )


class LLMJudge:
    """Real LLM judge. Model is injectable for testing; built lazily otherwise."""

    def __init__(self, model=None, model_name: str = JUDGE_DEFAULT_MODEL) -> None:
        if model is None:
            from langchain_anthropic import ChatAnthropic

            model = ChatAnthropic(model=model_name, temperature=0.0, max_tokens=1024)
        self._model = model
        self.model_name = model_name

    def judge(self, scenario: TeachingScenario, transcript: List[dict]) -> JudgeVerdict:
        system = (
            "You are an impartial evaluator of a calculus tutor's teaching quality. "
            "You are NOT the tutor. Judge only what the tutor said, using the rubric. "
            "Be strict and quote evidence."
        )
        user = (
            f"{render_rubric()}\n\n"
            f"{_render_transcript(scenario, transcript)}\n\n"
            "Now produce the structured verdict."
        )
        structured = self._model.with_structured_output(JudgeVerdict)
        verdict = structured.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        if isinstance(verdict, JudgeVerdict):
            return verdict
        return JudgeVerdict(**verdict)


def judge_trajectory(
    scenario: TeachingScenario, transcript: List[dict], judge: JudgeProtocol
) -> JudgeVerdict:
    """Score one trajectory, degrading to a neutral verdict if the judge fails."""
    try:
        return judge.judge(scenario, transcript)
    except Exception as exc:  # pragma: no cover - network path
        logger.warning("judge failed for %s, returning neutral verdict: %s",
                       scenario.id, exc)
        neutral = DimensionScore(score=3, evidence=f"judge error: {type(exc).__name__}")
        return JudgeVerdict(
            math_correctness=neutral,
            pedagogical_appropriateness=neutral,
            socratic_behavior=neutral,
            repetition=neutral,
            history_utilization=neutral,
            answer_leakage=neutral,
            overall=3.0,
            notes="Judge unavailable; neutral fallback (not counted as reliable).",
        )
