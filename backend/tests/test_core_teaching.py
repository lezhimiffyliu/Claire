"""Tests for the multi-turn teaching path: state schema additions + the bounded
one-hop tool loop in claire_core.loop.run_teaching_turn.

Fully offline: StubTutorAgent replays scripted decisions; in-memory stores.
"""
import pytest

from claire_core import (
    HintLevel,
    InMemoryProfileStore,
    InMemoryTeachingStateStore,
    Problem,
    ProblemPhase,
    StubTutorAgent,
    TeachingDecision,
    TeachingState,
    ToolName,
    ToolRequest,
    TutorAction,
    enforce,
    run_teaching_turn,
)
from claire_core.state import (
    EVIDENCE_CAP,
    TRANSCRIPT_CAP,
    EvidenceRecord,
    Grade,
    GradeStatus,
)


PROB = Problem(
    id="q1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    course="124",
)


def _incorrect_grade() -> Grade:
    return Grade(
        is_correct=False, is_uncertain=False, verifier_type="carried",
        confidence=1.0, reason="wrong",
    )


def _teaching_state() -> TeachingState:
    return TeachingState(
        problem_id="q1",
        phase=ProblemPhase.TEACHING,
        last_grade_status=GradeStatus.INCORRECT,
        attempt_count=1,
    )


def _stores(state: TeachingState):
    prof = InMemoryProfileStore()
    ts = InMemoryTeachingStateStore()
    ts.save("u1", state)
    return prof, ts


# --------------------------------------------------------------------------- #
# Schema: strict ToolRequest, bounded transcript/evidence
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [
    {"tool": "verify_step"},         # missing expression
    {"tool": "lookup_heuristic"},    # missing pattern
    {"tool": "retrieve_example"},    # missing topic
])
def test_tool_request_requires_fields(bad):
    with pytest.raises(Exception):
        ToolRequest(**bad)


def test_transcript_and_evidence_are_capped():
    s = TeachingState(problem_id="q1")
    for i in range(TRANSCRIPT_CAP + 5):
        s.append_transcript("student", f"msg{i}")
    assert len(s.transcript) == TRANSCRIPT_CAP
    for i in range(EVIDENCE_CAP + 4):
        s.append_evidence(EvidenceRecord(tool=ToolName.VERIFY_STEP, input="x", result="CORRECT", turn=i))
    assert len(s.evidence) == EVIDENCE_CAP


def test_teaching_decision_defaults_allow_pure_tool_request():
    d = TeachingDecision(tool_request=ToolRequest(tool="retrieve_example", topic="derivatives"))
    assert d.action == TutorAction.ASK_CLARIFICATION  # safe default
    assert d.message == ""
    assert d.redirect_to_submit is False


def test_enforce_preserves_redirect_flag():
    # ask_clarification is legal for an incorrect carried grade → returned as-is.
    proposed = TeachingDecision(
        action=TutorAction.ASK_CLARIFICATION, message="Submit it in the box.",
        redirect_to_submit=True,
    )
    out = enforce(proposed, _incorrect_grade(), _teaching_state())
    assert out.redirect_to_submit is True


# --------------------------------------------------------------------------- #
# run_teaching_turn: the bounded one-hop tool loop
# --------------------------------------------------------------------------- #
def test_no_tool_means_single_llm_call():
    prof, ts = _stores(_teaching_state())
    hint = TeachingDecision(action=TutorAction.GIVE_HINT, message="Use the power rule.", hint_level=HintLevel.NUDGE)
    agent = StubTutorAgent(propose_returns=[hint])

    res = run_teaching_turn(
        problem=PROB, student_message="why?", user_id="u1",
        agent=agent, profile_store=prof, teaching_state_store=ts,
    )
    assert agent.propose_calls == 1
    assert res.tool_used is None
    assert res.decision.action == TutorAction.GIVE_HINT
    assert res.ended is False


def test_tool_path_is_two_calls_and_records_evidence():
    prof, ts = _stores(_teaching_state())
    tool_req = TeachingDecision(tool_request=ToolRequest(tool="verify_step", expression="2x", expected="3x^2"))
    final = TeachingDecision(action=TutorAction.GIVE_HINT, message="Check the exponent.", hint_level=HintLevel.NUDGE)
    agent = StubTutorAgent(propose_returns=[tool_req, final])

    res = run_teaching_turn(
        problem=PROB, student_message="I got 2x", user_id="u1",
        agent=agent, profile_store=prof, teaching_state_store=ts,
    )
    assert agent.propose_calls == 2
    assert agent.allow_tools_seen == [True, False]   # second call cannot request tools
    assert res.tool_used == ToolName.VERIFY_STEP

    saved = ts.load("u1", "q1")
    assert len(saved.evidence) == 1
    assert saved.evidence[0].tool == ToolName.VERIFY_STEP
    # transcript gets both the student line and the tutor reply
    assert [e.role for e in saved.transcript] == ["student", "tutor"]


def test_repeated_hint_escalates_across_turns():
    prof, ts = _stores(_teaching_state())
    nudge = TeachingDecision(action=TutorAction.GIVE_HINT, message="A small nudge.", hint_level=HintLevel.NUDGE)

    # Turn 1: nudge.
    run_teaching_turn(problem=PROB, student_message="still stuck", user_id="u1",
                      agent=StubTutorAgent(propose_returns=[nudge]), profile_store=prof, teaching_state_store=ts)
    assert ts.load("u1", "q1").hint_level == HintLevel.NUDGE

    # Turn 2: agent proposes the SAME shallow level → enforce must escalate.
    again = TeachingDecision(action=TutorAction.GIVE_HINT, message="Another nudge.", hint_level=HintLevel.NUDGE)
    res = run_teaching_turn(problem=PROB, student_message="still stuck", user_id="u1",
                            agent=StubTutorAgent(propose_returns=[again]), profile_store=prof, teaching_state_store=ts)
    assert res.hint_level == HintLevel.CONCEPT   # escalated one rung


def test_final_answer_in_chat_redirects_without_grading():
    prof, ts = _stores(_teaching_state())
    redirect = TeachingDecision(
        action=TutorAction.ASK_CLARIFICATION,
        message="Looks like a final answer — submit it in the answer box.",
        redirect_to_submit=True,
    )
    agent = StubTutorAgent(propose_returns=[redirect])
    res = run_teaching_turn(problem=PROB, student_message="3x^2", user_id="u1",
                            agent=agent, profile_store=prof, teaching_state_store=ts)
    assert res.redirect_to_submit is True
    assert res.ended is False
    # phase never becomes RESOLVED here — only the verifier (submit path) can do that.
    assert res.phase != ProblemPhase.RESOLVED


def test_terminal_state_short_circuits_without_calling_agent():
    state = _teaching_state()
    state.phase = ProblemPhase.RESOLVED
    prof, ts = _stores(state)
    agent = StubTutorAgent(propose_returns=[TeachingDecision(action=TutorAction.GIVE_HINT, message="x")])

    res = run_teaching_turn(problem=PROB, student_message="more?", user_id="u1",
                            agent=agent, profile_store=prof, teaching_state_store=ts)
    assert res.ended is True
    assert res.decision.action == TutorAction.END_PROBLEM  # not a placeholder action
    assert agent.propose_calls == 0   # no LLM call on a finished problem


def test_illegal_action_is_corrected_by_enforce():
    # Carried grade is INCORRECT → CONFIRM_CORRECT is illegal; enforce must clamp.
    prof, ts = _stores(_teaching_state())
    rogue = TeachingDecision(action=TutorAction.CONFIRM_CORRECT, message="Perfect!")
    res = run_teaching_turn(problem=PROB, student_message="is this right?", user_id="u1",
                            agent=StubTutorAgent(propose_returns=[rogue]),
                            profile_store=prof, teaching_state_store=ts)
    assert res.decision.action != TutorAction.CONFIRM_CORRECT


def test_redirect_does_not_advance_a_teaching_move(monkeypatch):
    prof, ts = _stores(_teaching_state())
    # Model misbehaves: redirect AND a hint. Redirect must win, hint must NOT advance.
    bad = TeachingDecision(action=TutorAction.GIVE_HINT, message="here's a hint",
                           hint_level=HintLevel.NEXT_STEP, redirect_to_submit=True)
    res = run_teaching_turn(problem=PROB, student_message="3x^2", user_id="u1",
                            agent=StubTutorAgent(propose_returns=[bad]),
                            profile_store=prof, teaching_state_store=ts)
    assert res.redirect_to_submit is True
    assert res.decision.action == TutorAction.ASK_CLARIFICATION   # coerced, not give_hint
    assert ts.load("u1", "q1").hint_level == HintLevel.NONE       # hint NOT escalated


def test_tool_path_executes_exactly_one_tool(monkeypatch):
    import claire_core.tools as tmod
    calls = {"n": 0}
    real = tmod.run_tool

    def counting(req, problem, turn):
        calls["n"] += 1
        return real(req, problem, turn)

    monkeypatch.setattr(tmod, "run_tool", counting)

    prof, ts = _stores(_teaching_state())
    tool_req = TeachingDecision(tool_request=ToolRequest(tool="verify_step", expression="2x", expected="3x^2"))
    # NOTE: hop-2 return also carries a tool_request — it must NOT be dispatched.
    final = TeachingDecision(action=TutorAction.GIVE_HINT, message="check exponent",
                             tool_request=ToolRequest(tool="retrieve_example", topic="derivatives"))
    agent = StubTutorAgent(propose_returns=[tool_req, final])
    run_teaching_turn(problem=PROB, student_message="I got 2x", user_id="u1",
                      agent=agent, profile_store=prof, teaching_state_store=ts)
    assert agent.propose_calls == 2
    assert calls["n"] == 1   # exactly one tool executed despite hop-2's stray request


def test_state_is_isolated_per_user():
    prof = InMemoryProfileStore()
    ts = InMemoryTeachingStateStore()
    ts.save("alice", _teaching_state())
    ts.save("bob", _teaching_state())

    hint = TeachingDecision(action=TutorAction.GIVE_HINT, message="alice hint", hint_level=HintLevel.NUDGE)
    run_teaching_turn(problem=PROB, student_message="alice msg", user_id="alice",
                      agent=StubTutorAgent(propose_returns=[hint]), profile_store=prof, teaching_state_store=ts)

    assert ts.load("alice", "q1").teach_turn_count == 1
    assert ts.load("bob", "q1").teach_turn_count == 0   # untouched
    assert all("alice" in e.text or e.role == "tutor" for e in ts.load("alice", "q1").transcript)
    assert ts.load("bob", "q1").transcript == []
