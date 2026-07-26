"""
benchmarks.teaching_eval — Milestone A: thin teaching-trajectory evaluation.

An OFFLINE harness that drives the *real* canonical loop (`run_tutor_turn` +
`run_teaching_turn`) with a simulated student over a handful of curated
scenarios, then scores each trajectory three ways:

  1. a symbolic answer-leak check (reusing ``benchmarks.evaluator.evaluate``);
  2. structural assertions on the spine invariants (illegal action, extra tool
     call, pre-solution leak) — these are the HARD gates;
  3. an independently-authored LLM-as-judge rubric (reported, not gated, until a
     baseline distribution exists).

No production code is imported for its side effects and none is modified: the
harness only *consumes* the public `claire_core` surface + in-memory stores.

Public API::

    from benchmarks.teaching_eval import (
        TeachingScenario, GOLDEN_SCENARIOS,
        SimulatedStudent, answer_leaked,
        RUBRIC_VERSION, JudgeVerdict, StubJudge, LLMJudge, judge_trajectory,
        run_trajectory, run_suite,
    )
"""
from .judge import JudgeVerdict, LLMJudge, StubJudge, judge_trajectory
from .leak_check import TutorMessage, answer_leaked
from .rubric import RUBRIC_DIMENSIONS, RUBRIC_VERSION, DimensionScore
from .scenarios import (
    GOLDEN_SCENARIOS,
    ScenarioTurn,
    TeachingScenario,
    TurnKind,
    reply,
    submit,
)
from .simulated_student import SimulatedStudent

__all__ = [
    # scenarios
    "TeachingScenario",
    "ScenarioTurn",
    "TurnKind",
    "GOLDEN_SCENARIOS",
    "submit",
    "reply",
    # student
    "SimulatedStudent",
    # leak
    "answer_leaked",
    "TutorMessage",
    # rubric / judge
    "RUBRIC_VERSION",
    "RUBRIC_DIMENSIONS",
    "DimensionScore",
    "JudgeVerdict",
    "StubJudge",
    "LLMJudge",
    "judge_trajectory",
]
