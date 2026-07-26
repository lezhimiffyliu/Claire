"""
benchmarks.teaching_eval.simulated_student — the scripted (default) student.

Deterministic by default: the student simply replays the scenario's scripted
turns, so the whole suite runs offline with no network and identical output every
time. An optional persona-driven LLM mode (``--llm-student``) rewrites only the
REPLY messages in the student's voice; SUBMIT answers stay scripted so grading
remains deterministic and the trajectory length is fixed.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .scenarios import ScenarioTurn, TeachingScenario, TurnKind

logger = logging.getLogger(__name__)

DEFAULT_STUDENT_MODEL = "claude-3-5-haiku-20241022"


class SimulatedStudent:
    """Yields the student's messages for a scenario.

    With ``model=None`` (the default, and the only mode used in CI) every message
    is exactly the scripted text. When a model is supplied, REPLY messages are
    regenerated from the persona + running transcript; if generation fails for
    any reason it degrades to the scripted text.
    """

    def __init__(self, scenario: TeachingScenario, model=None) -> None:
        self.scenario = scenario
        self._model = model

    @property
    def turns(self) -> List[ScenarioTurn]:
        return list(self.scenario.turns)

    def message_for(self, turn: ScenarioTurn, transcript: List[dict]) -> str:
        """Resolve the text the student sends for ``turn``.

        ``transcript`` is the running list of ``{"role", "text"}`` lines so far,
        used only by the LLM mode for context.
        """
        if self._model is None or turn.kind == TurnKind.SUBMIT:
            return turn.text
        return self._llm_reply(turn, transcript)

    # -- optional LLM persona mode (never exercised in CI) ------------------ #
    def _llm_reply(self, turn: ScenarioTurn, transcript: List[dict]) -> str:
        try:
            last_tutor = next(
                (t["text"] for t in reversed(transcript) if t["role"] == "tutor"),
                "(no tutor message yet)",
            )
            prompt = (
                f"You are role-playing a calculus student. Persona: "
                f"{self.scenario.persona}\n"
                f"The problem is: {self.scenario.problem.text}\n"
                f"The tutor just said: {last_tutor}\n"
                f"The scripted intent of your next message is: \"{turn.text}\".\n"
                "Reply in ONE short sentence, in the student's voice, staying true "
                "to that intent. Do NOT solve the problem or state a final answer."
            )
            resp = self._model.invoke(
                [{"role": "user", "content": prompt}]
            )
            text = getattr(resp, "content", None) or str(resp)
            text = text if isinstance(text, str) else str(text)
            return text.strip() or turn.text
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("LLM student fell back to scripted text: %s", exc)
            return turn.text
