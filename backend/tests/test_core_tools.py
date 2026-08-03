"""Tests for the deterministic teaching-turn tool dispatcher (claire_core.tools.run_tool).

Each tool call must return a short, structured EvidenceRecord — never raw output
or free text summarized by another model. No network, no LLM.
"""
from claire_core.state import Problem, ToolName, ToolRequest
from claire_core.tools import run_tool


PROB = Problem(
    id="q1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    course="124",
)


def test_verify_step_correct():
    rec = run_tool(ToolRequest(tool="verify_step", expression="6*x", expected="6*x"), PROB, 1)
    assert rec.tool == ToolName.VERIFY_STEP
    assert rec.result.startswith("CORRECT")
    assert rec.turn == 1
    assert "6*x" in rec.input


def test_verify_step_incorrect():
    rec = run_tool(ToolRequest(tool="verify_step", expression="2*x", expected="3*x**2"), PROB, 2)
    assert rec.result.startswith("INCORRECT")


def test_lookup_heuristic_returns_text():
    rec = run_tool(ToolRequest(tool="lookup_heuristic", pattern="optimization"), PROB, 1)
    assert rec.tool == ToolName.LOOKUP_HEURISTIC
    assert rec.result.strip()          # some template or a clear "unknown pattern" message
    assert len(rec.result) <= 301      # clamped


def test_retrieve_example_returns_structured_record():
    rec = run_tool(ToolRequest(tool="retrieve_example", topic="derivatives"), PROB, 3)
    assert rec.tool == ToolName.RETRIEVE_EXAMPLE
    assert rec.result.strip()
    assert rec.turn == 3


def test_retrieve_example_miss_is_graceful():
    rec = run_tool(ToolRequest(tool="retrieve_example", topic="nonexistent_topic_xyz"), PROB, 1)
    assert "No worked example" in rec.result


def test_retrieve_example_excludes_current_problem(monkeypatch):
    # If the corpus returns the student's OWN problem, it must be filtered out
    # (returning it would leak the current answer as a "similar example").
    import claire_core.problem_retrieval as pr

    fake = [
        {"id": "q1:_", "source": "self", "question_text": "x^3", "final_answer": "3x^2"},
        {"id": "other:_", "source": "SP24 Q2", "question_text": "x^4", "final_answer": "4x^3"},
    ]
    monkeypatch.setattr(pr, "retrieve_examples", lambda *a, **k: fake)
    rec = run_tool(ToolRequest(tool="retrieve_example", topic="derivatives"), PROB, 1)
    assert "self" not in rec.result and "3x^2" not in rec.result
    assert "SP24 Q2" in rec.result


def test_tool_exception_degrades_to_error_evidence(monkeypatch):
    import claire_core.tools as tmod

    def boom(*a, **k):
        raise RuntimeError("verifier exploded")

    monkeypatch.setattr(tmod, "verify_answer", boom)
    rec = run_tool(ToolRequest(tool="verify_step", expression="2x", expected="3x^2"), PROB, 1)
    assert rec.tool == ToolName.VERIFY_STEP
    assert "unavailable" in rec.result.lower()   # safe degrade, no raise
