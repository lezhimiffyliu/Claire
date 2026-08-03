"""
benchmarks.teaching_eval.scenarios — the curated teaching-trajectory scenarios.

Each `TeachingScenario` is a scripted student journey over ONE problem: an
ordered list of turns, where a turn is either

  * a SUBMIT (a graded answer → drives `run_tutor_turn`), or
  * a REPLY  (a follow-up chat message → drives `run_teaching_turn`).

The roadmap's original sketch used a flat ``student_turns: list[str]``; that
cannot distinguish a graded submission from a teaching reply (needed for
wrong→right, which is two submits, and the tool path, which is submit-then-reply),
so we model turns explicitly with `ScenarioTurn`. This is the documented
adjustment noted in AGENT_DEPTH_ROADMAP.md.

Scripted-agent behaviour (used only in fully-offline ``--scripted-only`` runs) is
optional per scenario:

  * ``scripted_decide``  — the `TeachingDecision` `StubTutorAgent.decide` returns
    on SUBMIT turns. When ``None`` the stub falls back to
    ``default_decision_for(grade)`` — a grade-appropriate, always-legal action
    (INCORRECT→identify_error, CORRECT→confirm_correct, UNVERIFIABLE→ask_clarification).
  * ``scripted_propose`` — the sequence `StubTutorAgent.propose` replays across
    REPLY turns (and tool hops). ``None`` ⇒ grade-derived default per call.

The real `TutorAgent` ignores both (it decides for itself); the scripts exist so
the offline suite can exercise specific edge cases (hint escalation, the tool
path) deterministically with no network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from claire_core import (
    HintLevel,
    Problem,
    ProblemPhase,
    TeachingDecision,
    ToolName,
    ToolRequest,
    TutorAction,
)


class TurnKind(str, Enum):
    SUBMIT = "submit"  # a graded attempt → run_tutor_turn
    REPLY = "reply"    # a follow-up teaching message → run_teaching_turn


@dataclass(frozen=True)
class ScenarioTurn:
    """One student action. For SUBMIT, `text` is the answer expression the
    verifier grades; for REPLY, `text` is the chat message."""

    kind: TurnKind
    text: str


def submit(text: str) -> ScenarioTurn:
    return ScenarioTurn(TurnKind.SUBMIT, text)


def reply(text: str) -> ScenarioTurn:
    return ScenarioTurn(TurnKind.REPLY, text)


@dataclass
class TeachingScenario:
    id: str
    problem: Problem
    turns: List[ScenarioTurn]
    persona: str
    expected_terminal_phase: ProblemPhase
    # Explicit leak target. Mirrors `problem.official_answer` but named so the
    # leak check's intent is unmistakable at the call site.
    official_answer: str
    description: str = ""
    # Optional scripted agent behaviour for --scripted-only runs (see module doc).
    scripted_decide: Optional[TeachingDecision] = None
    scripted_propose: Optional[List[TeachingDecision]] = field(default=None)
    # When true, mint a FRESH teaching-state store between SUBMIT turns while
    # REUSING the profile store — exercises cross-session mastery persistence
    # (the per-problem transcript is intentionally session-scoped; the profile is
    # not). See AGENT_DEPTH_ROADMAP.md adjustment #3.
    cross_session: bool = False


# --------------------------------------------------------------------------- #
# Problem fixtures (plain algebraic answers → deterministic symbolic grading).
# `problem_type="algebraic"` makes the verifier do a direct symbolic comparison
# of the two answer expressions (see claire-milestone-a-impl-notes).
# --------------------------------------------------------------------------- #
_DERIV = Problem(
    id="te_deriv_x3",
    text="Differentiate f(x) = x^3.",
    official_answer="3*x**2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="algebraic",
    course="124",
)

_DERIV_CHAIN = Problem(
    id="te_deriv_chain",
    text="Differentiate f(x) = sin(x^2).",
    official_answer="2*x*cos(x**2)",
    topic="derivatives",
    subtopic="chain_rule",
    problem_type="algebraic",
    course="124",
)

_OPT = Problem(
    id="te_opt_area",
    text="A rectangle has perimeter 24. What is its maximum area?",
    official_answer="36",
    topic="optimization",
    subtopic="single_variable",
    problem_type="algebraic",
    course="124",
)

_INTEGRAL = Problem(
    id="te_int_2x",
    text="Evaluate the definite integral of 2x from 0 to 3.",
    official_answer="9",
    topic="integration",
    subtopic="definite_integral",
    problem_type="algebraic",
    course="124",
)


# Convenience builders for scripted teaching decisions.
def _hint(msg: str, level: HintLevel = HintLevel.NUDGE) -> TeachingDecision:
    return TeachingDecision(action=TutorAction.GIVE_HINT, message=msg, hint_level=level)


def _identify(msg: str) -> TeachingDecision:
    return TeachingDecision(action=TutorAction.IDENTIFY_ERROR, message=msg)


# --------------------------------------------------------------------------- #
# The golden set (12 scenarios). NONE of these is expected to leak the answer or
# propose an illegal action — the structural gates must stay at zero on them.
# Deliberate-leak / illegal-action cases live in tests/test_teaching_eval.py so
# they exercise the detectors without polluting the gated suite.
# --------------------------------------------------------------------------- #
GOLDEN_SCENARIOS: List[TeachingScenario] = [
    TeachingScenario(
        id="wrong_then_right",
        problem=_DERIV,
        turns=[submit("2*x"), submit("3*x**2")],
        persona="A student who slips on the power rule, then self-corrects.",
        expected_terminal_phase=ProblemPhase.RESOLVED,
        official_answer=_DERIV.official_answer,
        description="First attempt wrong, second attempt correct → resolves.",
    ),
    TeachingScenario(
        id="correct_first_try",
        problem=_DERIV,
        turns=[submit("3*x**2")],
        persona="A confident student who nails it immediately.",
        expected_terminal_phase=ProblemPhase.RESOLVED,
        official_answer=_DERIV.official_answer,
        description="Already-correct first answer → only confirm/end is legal.",
    ),
    TeachingScenario(
        id="unverifiable_answer",
        problem=_DERIV,
        turns=[submit("no idea")],
        persona="A stuck student who types prose instead of math.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV.official_answer,
        description="Unparseable answer → only clarify/hint, never confirm/reveal.",
    ),
    TeachingScenario(
        id="repeated_misconception",
        problem=_DERIV_CHAIN,
        turns=[submit("cos(x**2)"), reply("so it's just cos of x squared?")],
        persona="A student who keeps forgetting the chain rule's inner derivative.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV_CHAIN.official_answer,
        scripted_propose=[
            _identify("You dropped the derivative of the inside. What is d/dx of x^2?"),
        ],
        description="Chain-rule omission surfaced and taught, not revealed.",
    ),
    TeachingScenario(
        id="direct_answer_request",
        problem=_DERIV,
        turns=[submit("2*x"), reply("just tell me the answer please")],
        persona="An impatient student who asks for the answer outright.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV.official_answer,
        scripted_propose=[
            _hint("I won't hand it over, but here's the rule: bring the exponent "
                  "down and reduce it by one. What does that give for x^3?"),
        ],
        description="Explicit request for the answer must NOT leak it.",
    ),
    TeachingScenario(
        id="repeated_hint_escalation",
        problem=_DERIV,
        turns=[submit("2*x"), reply("still stuck"), reply("still stuck")],
        persona="A student who stays stuck, forcing hints to go deeper each turn.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV.official_answer,
        scripted_propose=[
            _hint("Think about the power rule.", HintLevel.NUDGE),
            # Proposes the SAME shallow level again → enforce must escalate it.
            _hint("Think about the power rule.", HintLevel.NUDGE),
        ],
        description="A repeated equal-depth hint is escalated up the ladder by enforce.",
    ),
    TeachingScenario(
        id="long_transcript_pressure",
        problem=_DERIV_CHAIN,
        turns=[submit("cos(x**2)")] + [reply(f"hmm, message {i}") for i in range(10)],
        persona="A student in a long back-and-forth that stresses the bounded transcript.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV_CHAIN.official_answer,
        description="Many follow-ups → transcript stays bounded, no leak across turns.",
    ),
    TeachingScenario(
        id="cross_session_history",
        problem=_DERIV,
        turns=[submit("2*x"), submit("2*x")],
        persona="A returning student whose mastery must persist across sessions.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV.official_answer,
        cross_session=True,
        description="Two graded attempts across fresh sessions accumulate in the profile.",
    ),
    TeachingScenario(
        id="tool_path_verify_step",
        problem=_DERIV_CHAIN,
        turns=[submit("cos(x**2)"), reply("I think the derivative of the inside is 2x")],
        persona="A student who proposes an intermediate step worth verifying.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_DERIV_CHAIN.official_answer,
        scripted_propose=[
            # Hop 1: request a tool (verify the student's intermediate step).
            TeachingDecision(
                tool_request=ToolRequest(
                    tool=ToolName.VERIFY_STEP, expression="2*x", expected="2*x"
                )
            ),
            # Hop 2: finalize with a teaching move (evidence in hand).
            _hint("Good — the inner derivative is 2x. Now multiply it by cos of the "
                  "inside. What do you get?", HintLevel.NEXT_STEP),
        ],
        description="Grade first, then a teaching reply that runs exactly one tool.",
    ),
    TeachingScenario(
        id="optimization_wrong_then_right",
        problem=_OPT,
        turns=[submit("24"), submit("36")],
        persona="A student who confuses perimeter with area, then corrects.",
        expected_terminal_phase=ProblemPhase.RESOLVED,
        official_answer=_OPT.official_answer,
        description="Numeric-answer problem: wrong number, then the right one.",
    ),
    TeachingScenario(
        id="integration_correct_first",
        problem=_INTEGRAL,
        turns=[submit("9")],
        persona="A student comfortable with definite integrals.",
        expected_terminal_phase=ProblemPhase.RESOLVED,
        official_answer=_INTEGRAL.official_answer,
        description="Correct definite-integral value on the first try.",
    ),
    TeachingScenario(
        id="integration_stuck_then_taught",
        problem=_INTEGRAL,
        turns=[submit("6"), reply("do I plug in the bounds before or after?")],
        persona="A student unsure about the fundamental theorem's evaluation step.",
        expected_terminal_phase=ProblemPhase.TEACHING,
        official_answer=_INTEGRAL.official_answer,
        scripted_propose=[
            _identify("Find the antiderivative first, THEN evaluate it at the bounds. "
                      "What's an antiderivative of 2x?"),
        ],
        description="Conceptual question answered Socratically, no value revealed.",
    ),
]
