"""
claire_core.state — domain models + the teaching state machine.

This is the deterministic heart of the tutor. It has NO LLM and NO I/O, so it
is fast and fully unit-testable. The central idea:

    The LLM proposes, the deterministic policy disposes.

The agent may *suggest* a teaching action, but two things are ground truth:

  1. the SymPy verifier's grade (correct / incorrect / unverifiable), and
  2. the per-problem `TeachingState` (attempt count, hint history, phase).

`enforce()` clamps the agent's proposed action to the set that is legal given
BOTH of those, so the tutor can never (for example) congratulate a wrong answer,
keep quizzing a correct one, dump the full solution on the first attempt, or
repeat the same shallow hint forever.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Set

from pydantic import BaseModel, Field, model_validator


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class ProblemPhase(str, Enum):
    """The lifecycle of a single problem the student is working on.

    `GRADED` is intentionally NOT here: grading is an *event* inside a turn, not
    a durable state. After a turn we always sit in one of these.
    """

    AWAITING_ATTEMPT = "awaiting_attempt"  # no answer submitted yet
    EVALUATING = "evaluating"              # an answer is being graded this turn
    TEACHING = "teaching"                  # guiding after a wrong/uncertain try
    RESOLVED = "resolved"                  # solved correctly (or full solution shown)
    ABANDONED = "abandoned"                # ended without a correct answer


class GradeStatus(str, Enum):
    """Ground-truth verdict from the symbolic verifier."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNVERIFIABLE = "unverifiable"  # could not parse / verify the answer


class TutorAction(str, Enum):
    """The mutually-exclusive things the tutor can do on a single turn."""

    ASK_CLARIFICATION = "ask_clarification"
    IDENTIFY_ERROR = "identify_error"
    GIVE_HINT = "give_hint"
    EXPLAIN_CONCEPT = "explain_concept"
    CHECK_INTERMEDIATE_STEP = "check_intermediate_step"
    SHOW_WORKED_EXAMPLE = "show_worked_example"
    SHOW_SOLUTION = "show_solution"
    CONFIRM_CORRECT = "confirm_correct"
    END_PROBLEM = "end_problem"


class HintLevel(str, Enum):
    """How much of the answer a hint gives away. Ordered least → most."""

    NONE = "none"
    NUDGE = "nudge"
    CONCEPT = "concept"
    NEXT_STEP = "next_step"
    NEAR_SOLUTION = "near_solution"
    FULL_SOLUTION = "full_solution"


# The escalation ladder — index in this list is the "depth" of a hint.
HINT_LADDER: List[HintLevel] = [
    HintLevel.NONE,
    HintLevel.NUDGE,
    HintLevel.CONCEPT,
    HintLevel.NEXT_STEP,
    HintLevel.NEAR_SOLUTION,
    HintLevel.FULL_SOLUTION,
]


def hint_index(level: HintLevel) -> int:
    return HINT_LADDER.index(level)


def next_hint_level(level: HintLevel) -> HintLevel:
    """The next rung up the ladder (saturates at FULL_SOLUTION)."""
    return HINT_LADDER[min(hint_index(level) + 1, len(HINT_LADDER) - 1)]


class MisconceptionType(str, Enum):
    """Structured error classification (from classify.py or the agent)."""

    POWER_RULE_ERROR = "power_rule_error"
    CHAIN_RULE_OMISSION = "chain_rule_omission"
    PRODUCT_RULE_ERROR = "product_rule_error"
    ALGEBRA_ERROR = "algebra_error"
    NOTATION_ERROR = "notation_error"
    CONCEPTUAL_CONFUSION = "conceptual_confusion"
    UNKNOWN = "unknown"


class ToolName(str, Enum):
    """The tools the tutor may request during a teaching turn.

    Deliberately the SAME three that back the (orphaned) conversational loop —
    the teaching path calls their pure implementations directly (see
    `tools.run_tool`), not the LangChain tool objects.
    """

    VERIFY_STEP = "verify_step"          # symbolically check an intermediate step
    LOOKUP_HEURISTIC = "lookup_heuristic"  # canonical formula/template for a pattern
    RETRIEVE_EXAMPLE = "retrieve_example"  # a similar solved problem from the corpus


# Map a fine-grained misconception to the coarse bucket the profile tracks
# (concept | algebra | logic | careless). None means "don't record a bucket".
MISCONCEPTION_TO_BUCKET = {
    MisconceptionType.POWER_RULE_ERROR: "concept",
    MisconceptionType.CHAIN_RULE_OMISSION: "concept",
    MisconceptionType.PRODUCT_RULE_ERROR: "concept",
    MisconceptionType.CONCEPTUAL_CONFUSION: "concept",
    MisconceptionType.ALGEBRA_ERROR: "algebra",
    MisconceptionType.NOTATION_ERROR: "careless",
    MisconceptionType.UNKNOWN: None,
}


# Attempts required before the tutor is allowed to reveal the whole solution.
SOLUTION_ATTEMPT_THRESHOLD = 3

# Bounded per-problem memory for multi-turn teaching. Kept small on purpose:
# enough context to stay coherent, never a full chat log.
TRANSCRIPT_CAP = 8          # last N student/tutor messages retained
EVIDENCE_CAP = 5            # last N structured tool-evidence records retained
_TRANSCRIPT_TEXT_CAP = 600  # per-message character clamp before storing


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #
class Problem(BaseModel):
    """A problem the student is working on."""

    id: str
    text: str
    official_answer: str
    topic: str
    subtopic: Optional[str] = None
    # One of: derivative | indefinite_integral | definite_integral | limit |
    # equation | algebraic. If None, the verifier auto-detects.
    problem_type: Optional[str] = None
    course: str = "124"


class StudentAttempt(BaseModel):
    """A single answer submitted by the student."""

    problem_id: str
    answer: str
    work: Optional[str] = None
    source: str = "practice"  # diagnostic | practice | handwritten_upload


class Grade(BaseModel):
    """Ground-truth judgment of an attempt (produced by verifier.py)."""

    is_correct: bool
    is_uncertain: bool
    verifier_type: str
    confidence: float
    reason: str

    @property
    def status(self) -> GradeStatus:
        if self.is_uncertain:
            return GradeStatus.UNVERIFIABLE
        return GradeStatus.CORRECT if self.is_correct else GradeStatus.INCORRECT

    @classmethod
    def from_verification(cls, result) -> "Grade":
        """Adapt a verifier.AnswerVerificationResult into a Grade."""
        return cls(
            is_correct=bool(result.is_correct),
            is_uncertain=bool(result.is_uncertain),
            verifier_type=result.verifier_type,
            confidence=float(result.confidence),
            reason=result.reason,
        )


class ToolRequest(BaseModel):
    """A single, strictly-typed tool call the agent asks the orchestrator to run.

    Only the fields for the chosen `tool` are meaningful; the validator enforces
    that the required one(s) are present so we never dispatch a malformed call.
    """

    tool: ToolName
    # verify_step
    expression: Optional[str] = None  # the student's intermediate expression
    expected: Optional[str] = None    # what it should equal (agent-derived; NOT the official final answer)
    # lookup_heuristic
    pattern: Optional[str] = None     # e.g. "chain_rule", "optimization"
    # retrieve_example
    topic: Optional[str] = None       # e.g. "derivatives"
    error_type: Optional[str] = None  # optional bias, e.g. "chain_rule_omission"

    @model_validator(mode="after")
    def _require_fields_for_tool(self) -> "ToolRequest":
        if self.tool == ToolName.VERIFY_STEP and not (self.expression or "").strip():
            raise ValueError("verify_step requires 'expression'")
        if self.tool == ToolName.LOOKUP_HEURISTIC and not (self.pattern or "").strip():
            raise ValueError("lookup_heuristic requires 'pattern'")
        if self.tool == ToolName.RETRIEVE_EXAMPLE and not (self.topic or "").strip():
            raise ValueError("retrieve_example requires 'topic'")
        return self


class EvidenceRecord(BaseModel):
    """The structured, short result of one tool call — the only tool output that
    is ever persisted. No raw scratchpad, no verbose dumps."""

    tool: ToolName
    input: str    # normalized, human-readable summary of what was asked
    result: str   # short summary of the finding (already truncated by the dispatcher)
    turn: int     # the teach_turn_count when produced


class TranscriptEntry(BaseModel):
    """One line of the bounded multi-turn dialogue kept for context."""

    role: Literal["student", "tutor"]
    text: str


class TeachingDecision(BaseModel):
    """A tutor's turn: what to do + what to say + how deep to go."""

    # Defaults so a pure tool-request response (only `tool_request` set) validates
    # without the model having to invent placeholder action/message text.
    action: TutorAction = TutorAction.ASK_CLARIFICATION
    message: str = ""
    hint_level: HintLevel = HintLevel.NONE
    diagnosed_misconception: Optional[MisconceptionType] = None
    # If set on the FIRST teaching-turn call, the orchestrator runs this one tool,
    # feeds the structured result back, and calls the agent once more to finalize.
    tool_request: Optional[ToolRequest] = None
    # Set when the student pasted a complete final answer into the chat: the
    # teaching path must NOT grade it — the API tells the frontend to use the
    # formal submit-attempt path instead.
    redirect_to_submit: bool = False
    # Short, DISPLAYABLE rationale — never the model's hidden chain of thought.
    reasoning_summary: str = ""
    # Provenance filled in by enforce() when it overrides the agent. Internal.
    reasoning: str = ""


class TeachingState(BaseModel):
    """Per-problem teaching memory. This is what lets the *same* problem advance
    across attempts instead of restarting the dialogue every turn."""

    problem_id: str
    phase: ProblemPhase = ProblemPhase.AWAITING_ATTEMPT
    attempt_count: int = 0
    # The verifier's verdict on the most recent graded attempt — carried into
    # follow-up teaching turns as background (they never re-grade the answer).
    last_grade_status: Optional[GradeStatus] = None
    hint_level: HintLevel = HintLevel.NONE
    diagnosed_misconception: Optional[MisconceptionType] = None
    explained_concepts: List[str] = Field(default_factory=list)
    hints_given: List[str] = Field(default_factory=list)  # hint-level history
    actions_taken: List[TutorAction] = Field(default_factory=list)
    last_action: Optional[TutorAction] = None
    last_question: Optional[str] = None
    # True once any hint/concept/example was given before the problem resolved —
    # feeds the profile's hint-dependency signal.
    used_hint: bool = False
    # Bounded multi-turn memory for the follow-up teaching dialogue.
    teach_turn_count: int = 0
    transcript: List[TranscriptEntry] = Field(default_factory=list)
    evidence: List[EvidenceRecord] = Field(default_factory=list)

    def append_transcript(self, role: str, text: str) -> None:
        """Append a dialogue line, clamped in length and capped in count."""
        clean = (text or "").strip()[:_TRANSCRIPT_TEXT_CAP]
        if not clean:
            return
        self.transcript.append(TranscriptEntry(role=role, text=clean))
        if len(self.transcript) > TRANSCRIPT_CAP:
            self.transcript = self.transcript[-TRANSCRIPT_CAP:]

    def append_evidence(self, record: EvidenceRecord) -> None:
        """Append a structured tool-evidence record, capped in count."""
        self.evidence.append(record)
        if len(self.evidence) > EVIDENCE_CAP:
            self.evidence = self.evidence[-EVIDENCE_CAP:]

    def register_attempt(self) -> None:
        """Call at the start of a turn, when a new answer arrives.

        Terminal phases (resolved/abandoned) are preserved so the enforcement
        layer can lock further teaching on a problem that's already done.
        """
        self.attempt_count += 1
        if self.phase not in (ProblemPhase.RESOLVED, ProblemPhase.ABANDONED):
            self.phase = ProblemPhase.EVALUATING

    def advance(self, decision: "TeachingDecision", grade: "Grade") -> None:
        """Fold an enforced decision + grade into the state (pure, no I/O)."""
        self.last_grade_status = grade.status
        self.last_action = decision.action
        self.actions_taken.append(decision.action)
        if decision.diagnosed_misconception:
            self.diagnosed_misconception = decision.diagnosed_misconception

        a = decision.action
        if a == TutorAction.GIVE_HINT:
            self.hint_level = decision.hint_level
            self.hints_given.append(decision.hint_level.value)
            self.used_hint = True
        elif a in (TutorAction.EXPLAIN_CONCEPT, TutorAction.SHOW_WORKED_EXAMPLE):
            self.used_hint = True
            if a == TutorAction.EXPLAIN_CONCEPT and decision.diagnosed_misconception:
                concept = decision.diagnosed_misconception.value
                if concept not in self.explained_concepts:
                    self.explained_concepts.append(concept)

        if decision.message.strip().endswith("?"):
            self.last_question = decision.message.strip()

        # Phase transition (grade is ground truth).
        if grade.status == GradeStatus.CORRECT:
            self.phase = ProblemPhase.RESOLVED
        elif a == TutorAction.SHOW_SOLUTION:
            self.phase = ProblemPhase.RESOLVED
        elif a == TutorAction.END_PROBLEM:
            self.phase = ProblemPhase.ABANDONED
        else:
            self.phase = ProblemPhase.TEACHING


# --------------------------------------------------------------------------- #
# The enforcement rules — verifier grade + teaching state are ground truth
# --------------------------------------------------------------------------- #
def _solution_unlocked(state: Optional[TeachingState]) -> bool:
    """The full solution is only allowed after real effort."""
    if state is None:
        return True  # no state to gate on (e.g. a one-shot unit test)
    return (
        state.attempt_count >= SOLUTION_ATTEMPT_THRESHOLD
        or state.hint_level in (HintLevel.NEAR_SOLUTION, HintLevel.FULL_SOLUTION)
    )


def allowed_actions(
    grade: Grade, state: Optional[TeachingState] = None
) -> Set[TutorAction]:
    """The set of teaching actions that are legal for a grade + teaching state."""
    if grade.status == GradeStatus.CORRECT:
        return {TutorAction.CONFIRM_CORRECT, TutorAction.END_PROBLEM}

    if grade.status == GradeStatus.UNVERIFIABLE:
        # Can't confirm, can't end, can't reveal the solution on a non-verdict.
        return {TutorAction.ASK_CLARIFICATION, TutorAction.GIVE_HINT}

    # INCORRECT: everything pedagogical except claiming it was correct.
    legal = {
        TutorAction.ASK_CLARIFICATION,
        TutorAction.IDENTIFY_ERROR,
        TutorAction.GIVE_HINT,
        TutorAction.EXPLAIN_CONCEPT,
        TutorAction.CHECK_INTERMEDIATE_STEP,
        TutorAction.SHOW_WORKED_EXAMPLE,
        TutorAction.END_PROBLEM,
    }
    if _solution_unlocked(state):
        legal.add(TutorAction.SHOW_SOLUTION)
    return legal


def _default_action(grade: Grade) -> TutorAction:
    if grade.status == GradeStatus.CORRECT:
        return TutorAction.CONFIRM_CORRECT
    if grade.status == GradeStatus.UNVERIFIABLE:
        return TutorAction.ASK_CLARIFICATION
    return TutorAction.IDENTIFY_ERROR


_DEFAULT_MESSAGE = {
    TutorAction.CONFIRM_CORRECT: "That's correct — nice work. Let's move on.",
    TutorAction.GIVE_HINT: "Not quite. Here's a hint to get you unstuck.",
    TutorAction.IDENTIFY_ERROR: "That isn't right yet. Let's find where it went off track.",
    TutorAction.EXPLAIN_CONCEPT: "Let's revisit the idea behind this step.",
    TutorAction.CHECK_INTERMEDIATE_STEP: "Let's check one of your steps together.",
    TutorAction.SHOW_WORKED_EXAMPLE: "Here's a similar worked example to learn from.",
    TutorAction.ASK_CLARIFICATION: "I couldn't fully read your work — can you walk me through your steps?",
    TutorAction.SHOW_SOLUTION: "Let's work through the full solution together.",
    TutorAction.END_PROBLEM: "Let's set this one aside for now.",
}


def default_decision_for(
    grade: Grade, state: Optional[TeachingState] = None
) -> TeachingDecision:
    """A safe decision derived purely from the grade (used as LLM fallback)."""
    action = _default_action(grade)
    hint = HintLevel.NUDGE if action == TutorAction.GIVE_HINT else HintLevel.NONE
    return TeachingDecision(
        action=action,
        message=_DEFAULT_MESSAGE[action],
        hint_level=hint,
        reasoning="Derived from verifier grade (no LLM).",
    )


def enforce(
    proposed: TeachingDecision,
    grade: Grade,
    state: Optional[TeachingState] = None,
) -> TeachingDecision:
    """
    Clamp the agent's proposed decision to what the grade + teaching state allow.

    Rules:
      * Correct answer  → only confirm/end (never keep quizzing).
      * Incorrect       → anything pedagogical except "confirm correct".
      * Unverifiable    → only clarify/hint (never confirm, end, or reveal).
      * Full solution   → gated behind effort (SOLUTION_ATTEMPT_THRESHOLD or a
                          near-solution hint already given).
      * Resolved/abandoned problem → no further teaching.
      * Repeated hint   → force the hint level to escalate up the ladder.
    """
    # A problem that's already done can't be taught further.
    if state is not None and state.phase in (
        ProblemPhase.RESOLVED,
        ProblemPhase.ABANDONED,
    ):
        return TeachingDecision(
            action=TutorAction.END_PROBLEM,
            message=_DEFAULT_MESSAGE[TutorAction.END_PROBLEM],
            reasoning=f"ENFORCED: problem already {state.phase.value}; no more teaching.",
            diagnosed_misconception=proposed.diagnosed_misconception,
        )

    legal = allowed_actions(grade, state)

    # 1. Illegal action → override to a safe default (and replace the message,
    #    since a message written for the wrong action can't be trusted).
    if proposed.action not in legal:
        safe = _default_action(grade)
        return TeachingDecision(
            action=safe,
            message=_DEFAULT_MESSAGE[safe],
            hint_level=HintLevel.NUDGE if safe == TutorAction.GIVE_HINT else HintLevel.NONE,
            diagnosed_misconception=proposed.diagnosed_misconception,
            reasoning_summary=proposed.reasoning_summary,
            reasoning=(
                f"ENFORCED: agent proposed '{proposed.action.value}' but grade "
                f"({grade.status.value}) with state "
                f"(attempts={getattr(state, 'attempt_count', 0)}, "
                f"hint={getattr(state, 'hint_level', HintLevel.NONE).value}) only allows "
                f"{sorted(a.value for a in legal)}."
            ),
        )

    # 2. Legal action, but a repeated hint must dig deeper than last time.
    if (
        proposed.action == TutorAction.GIVE_HINT
        and state is not None
        and state.last_action == TutorAction.GIVE_HINT
        and hint_index(proposed.hint_level) <= hint_index(state.hint_level)
    ):
        escalated = next_hint_level(state.hint_level)
        return proposed.model_copy(
            update={
                "hint_level": escalated,
                "reasoning": (
                    f"ENFORCED: repeated hint escalated "
                    f"{state.hint_level.value} → {escalated.value}."
                ),
            }
        )

    return proposed
