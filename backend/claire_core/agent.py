"""
claire_core.agent — the tutor's LLM layer (LangChain / LangGraph).

Two entry points, both LangChain-native, both easy to swap later:

    TutorAgent.decide(problem, attempt, grade) -> TeachingDecision
        One structured call. Given the verifier's ground-truth grade, the model
        chooses a teaching ACTION and writes the student-facing message. The
        grade is already known here, so no tools are needed.

    TutorAgent.chat(history) -> str
        A genuine LangGraph ReAct tool-calling loop (verify_answer_tool,
        lookup_heuristic_tool) for follow-up Socratic dialogue, where the agent
        may want to check an intermediate step.

`TutorAgentProtocol` is the seam loop.py depends on; `StubTutorAgent` is the
no-LLM implementation used in tests.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Protocol, runtime_checkable

from .state import (
    EvidenceRecord,
    Grade,
    GradeStatus,
    Problem,
    StudentAttempt,
    TeachingDecision,
    TeachingState,
    allowed_actions,
    default_decision_for,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are Claire, a Socratic calculus tutor.

Rules you must obey:
1. NEVER give away the final answer prematurely. Teach the formula/rule first,
   then let the student apply it.
2. The correctness of the student's answer has ALREADY been decided by a symbolic
   verifier — treat that verdict as ground truth. Do not re-judge it.
3. Be warm, concise (1-4 sentences), and end wrong-answer turns with a question
   that moves the student one concrete step forward.
4. You are given the teaching history for THIS problem and the student's mastery.
   If you have already hinted, go DEEPER than last time — do not repeat yourself.
"""


@runtime_checkable
class TutorAgentProtocol(Protocol):
    """The interface loop.py depends on. Anything with .decide() works."""

    def decide(
        self,
        problem: Problem,
        attempt: StudentAttempt,
        grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
    ) -> TeachingDecision:
        ...

    def propose(
        self,
        problem: Problem,
        student_message: str,
        carried_grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
        *,
        allow_tools: bool = True,
        evidence: Optional[EvidenceRecord] = None,
    ) -> TeachingDecision:
        ...


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
_VERDICT_LABEL = {
    GradeStatus.CORRECT: "CORRECT",
    GradeStatus.INCORRECT: "INCORRECT",
    GradeStatus.UNVERIFIABLE: "UNVERIFIABLE (could not read/verify the work)",
}


def _state_block(state: Optional[TeachingState]) -> str:
    if state is None:
        return "TEACHING HISTORY: (this is the first turn on this problem)"
    hints = ", ".join(state.hints_given) or "none yet"
    concepts = ", ".join(state.explained_concepts) or "none yet"
    return (
        f"TEACHING HISTORY (this problem):\n"
        f"  attempts so far        : {state.attempt_count}\n"
        f"  current hint level     : {state.hint_level.value}\n"
        f"  hints already given    : {hints}\n"
        f"  concepts explained     : {concepts}\n"
        f"  last action            : {state.last_action.value if state.last_action else 'none'}\n"
        f"  diagnosed misconception: {state.diagnosed_misconception.value if state.diagnosed_misconception else 'none'}"
    )


def _turn_prompt(
    problem: Problem,
    attempt: StudentAttempt,
    grade: Grade,
    state: Optional[TeachingState] = None,
    profile_summary: Optional[str] = None,
) -> str:
    verdict = _VERDICT_LABEL[grade.status]
    legal = sorted(a.value for a in allowed_actions(grade, state))
    profile = profile_summary or "STUDENT MASTERY: (no history yet)"
    return f"""PROBLEM ({problem.topic}): {problem.text}

STUDENT'S ANSWER: {attempt.answer}
STUDENT'S WORK: {attempt.work or "(none provided)"}

VERIFIER VERDICT (ground truth): {verdict}
Verifier note: {grade.reason}

{_state_block(state)}

{profile}

You may ONLY choose one of these actions: {legal}
Pick the single best action and write the student-facing `message`. Set
`hint_level` to how much you reveal (none|nudge|concept|next_step|near_solution|
full_solution) — escalate it if you have hinted before. If the verdict is
INCORRECT, also set `diagnosed_misconception` to one of: power_rule_error,
chain_rule_omission, product_rule_error, algebra_error, notation_error,
conceptual_confusion, unknown. Put a one-line justification in `reasoning_summary`.
If CORRECT, confirm briefly. Never reveal the final answer unless the action is
show_solution.
"""


def _last_ai_text(result: dict) -> str:
    messages = result.get("messages", [])
    for msg in reversed(messages):
        content = getattr(msg, "content", None)
        if content:
            return content if isinstance(content, str) else str(content)
    return ""


# --------------------------------------------------------------------------- #
# Teaching-turn prompt (follow-up dialogue, bounded one-hop tool loop)
# --------------------------------------------------------------------------- #
_TOOL_MENU = """TOOLS you MAY request (set `tool_request` and leave action/message empty if you do):
  • verify_step     — symbolically check a student's intermediate expression.
                      args: expression (required), expected (required — what it
                      should equal, derived by YOU; never the official final answer).
  • lookup_heuristic— get the canonical formula/template for a pattern.
                      args: pattern (required), e.g. "optimization", "chain_rule".
  • retrieve_example— fetch a similar SOLVED problem to teach from.
                      args: topic (required), error_type (optional).
Request a tool ONLY when you lack the evidence to teach accurately (e.g. to check
a step you can't verify by eye, to quote an exact formula, or to ground a worked
example). Otherwise finalize with an action + message and NO tool_request. You may
request AT MOST ONE tool this turn."""


def _transcript_block(state: Optional[TeachingState]) -> str:
    if state is None or not state.transcript:
        return "DIALOGUE SO FAR: (this is the first follow-up on this problem)"
    lines = [f"  {e.role}: {e.text}" for e in state.transcript]
    return "DIALOGUE SO FAR (recent, oldest first):\n" + "\n".join(lines)


def _evidence_block(
    state: Optional[TeachingState], extra: Optional[EvidenceRecord] = None
) -> str:
    records = list(state.evidence) if state else []
    if extra is not None:
        records = records + [extra]
    if not records:
        return "TOOL EVIDENCE: (none gathered yet)"
    lines = [f"  [{r.tool.value}] {r.input} → {r.result}" for r in records]
    return "TOOL EVIDENCE (structured, ground truth):\n" + "\n".join(lines)


def _teaching_prompt(
    problem: Problem,
    student_message: str,
    carried_grade: Grade,
    state: Optional[TeachingState],
    profile_summary: Optional[str],
    allow_tools: bool,
    evidence: Optional[EvidenceRecord],
) -> str:
    verdict = _VERDICT_LABEL[carried_grade.status]
    legal = sorted(a.value for a in allowed_actions(carried_grade, state))
    profile = profile_summary or "STUDENT MASTERY: (no history yet)"

    tool_section = (
        _TOOL_MENU
        if allow_tools
        else "You have already gathered the evidence below. Do NOT request a tool now — choose the final action + message."
    )

    return f"""We are MID-TEACHING on one problem. The student is replying to your
last message; this is NOT a new graded attempt. The original answer's verdict is
BACKGROUND — do not re-judge the final answer here.

PROBLEM ({problem.topic}): {problem.text}
ORIGINAL VERDICT (background, from the verifier): {verdict} — {carried_grade.reason}

{_state_block(state)}

{_transcript_block(state)}

{_evidence_block(state, evidence)}

{profile}

STUDENT'S NEW MESSAGE: {student_message}

{tool_section}

You may ONLY choose one of these final actions: {legal}
Rules:
  • If the student's message is a COMPLETE final answer to THIS problem (not a
    step, not a question), do NOT grade it: set `redirect_to_submit`=true,
    action=ask_clarification, and a message telling them to submit it in the
    answer box so it can be checked.
  • Otherwise pick the single best next action and write the student-facing
    `message`. Advance the teaching — if you have hinted before, go DEEPER.
  • Set `hint_level` to how much you reveal. Never reveal the final answer unless
    the action is show_solution. Put a one-line note in `reasoning_summary`.
"""


# --------------------------------------------------------------------------- #
# The real LangChain agent
# --------------------------------------------------------------------------- #
class TutorAgent:
    """LangChain/LangGraph-backed tutor. Model is injectable for testing."""

    def __init__(self, model=None, model_name: str = DEFAULT_MODEL) -> None:
        if model is None:
            from langchain_anthropic import ChatAnthropic

            model = ChatAnthropic(model=model_name, temperature=0.3, max_tokens=800)
        self._model = model
        self._react_agent = None  # built lazily for chat()

    # -- grading-turn decision (single structured call) -------------------- #
    def decide(
        self,
        problem: Problem,
        attempt: StudentAttempt,
        grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
    ) -> TeachingDecision:
        try:
            structured = self._model.with_structured_output(TeachingDecision)
            decision = structured.invoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": _turn_prompt(
                            problem, attempt, grade, state, profile_summary
                        ),
                    },
                ]
            )
            if isinstance(decision, TeachingDecision):
                return decision
            return TeachingDecision(**decision)  # dict fallback
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("TutorAgent.decide fell back to default: %s", exc)
            return default_decision_for(grade, state)

    # -- teaching-turn decision (structured, optional one-hop tool) -------- #
    def propose(
        self,
        problem: Problem,
        student_message: str,
        carried_grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
        *,
        allow_tools: bool = True,
        evidence: Optional[EvidenceRecord] = None,
    ) -> TeachingDecision:
        """One structured decision for a follow-up teaching turn.

        With ``allow_tools=True`` the model may EITHER finalize a decision OR set
        ``tool_request`` to ask for one tool. The orchestrator runs the tool and
        calls this again with ``allow_tools=False`` and the ``evidence`` in hand,
        so the second call must finalize. This is the whole tool loop — no ReAct,
        no free-text intermediate agent.
        """
        try:
            structured = self._model.with_structured_output(TeachingDecision)
            decision = structured.invoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": _teaching_prompt(
                            problem,
                            student_message,
                            carried_grade,
                            state,
                            profile_summary,
                            allow_tools,
                            evidence,
                        ),
                    },
                ]
            )
            if not isinstance(decision, TeachingDecision):
                decision = TeachingDecision(**decision)  # dict fallback
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("TutorAgent.propose fell back to default: %s", exc)
            return default_decision_for(carried_grade, state)

        # A finalizing call can never carry a tool request (guards the ≤1-hop
        # invariant even if the model ignores the instruction).
        if not allow_tools:
            decision.tool_request = None
        return decision

    # -- interactive Socratic loop (ReAct tool-calling) -------------------- #
    def _get_react_agent(self):
        if self._react_agent is None:
            from langgraph.prebuilt import create_react_agent

            from .tools import TUTOR_TOOLS

            self._react_agent = create_react_agent(
                self._model, TUTOR_TOOLS, prompt=SYSTEM_PROMPT
            )
        return self._react_agent

    def chat(self, history: List[dict]) -> str:
        """Run one turn of the ReAct tool-calling loop over a message history.

        `history` is a list of {"role": "user"|"assistant", "content": str}.
        Returns the tutor's reply text.
        """
        agent = self._get_react_agent()
        result = agent.invoke({"messages": history})
        return _last_ai_text(result)


# --------------------------------------------------------------------------- #
# Test double
# --------------------------------------------------------------------------- #
class StubTutorAgent:
    """A no-LLM TutorAgent for tests.

    `decide` returns the preset (or grade-derived) decision. `propose` replays a
    scripted list of decisions across calls (to exercise the tool-then-finalize
    path) and records call metadata so tests can assert the ≤1-call/≤1-tool
    invariants.
    """

    def __init__(
        self,
        decision: Optional[TeachingDecision] = None,
        propose_returns: Optional[List[TeachingDecision]] = None,
    ) -> None:
        self._decision = decision
        self._propose_returns = list(propose_returns) if propose_returns else None
        self.propose_calls = 0
        self.allow_tools_seen: List[bool] = []

    def decide(
        self,
        problem: Problem,
        attempt: StudentAttempt,
        grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
    ) -> TeachingDecision:
        return self._decision or default_decision_for(grade, state)

    def propose(
        self,
        problem: Problem,
        student_message: str,
        carried_grade: Grade,
        state: Optional[TeachingState] = None,
        profile_summary: Optional[str] = None,
        *,
        allow_tools: bool = True,
        evidence: Optional[EvidenceRecord] = None,
    ) -> TeachingDecision:
        self.propose_calls += 1
        self.allow_tools_seen.append(allow_tools)
        if self._propose_returns:
            decision = self._propose_returns.pop(0)
        else:
            decision = default_decision_for(carried_grade, state)
        if not allow_tools:
            decision.tool_request = None
        return decision
