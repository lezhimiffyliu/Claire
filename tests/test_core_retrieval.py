"""Tests for claire_core.problem_retrieval — corpus-backed worked-example lookup.

These run against the real `problems/*.json` corpus (no network, no LLM). They
assert ranking behavior rather than exact problem ids, so they stay stable as
the corpus grows.
"""
from claire_core import problem_retrieval as pr
from claire_core.tools import TUTOR_TOOLS, retrieve_teaching_example


def test_corpus_loads_and_flattens():
    records = pr._corpus("124")
    assert records, "expected a non-empty Math 124 corpus"
    r = records[0]
    # Every record carries what a teaching example needs.
    for key in ("topic", "concepts", "question_text", "final_answer", "source"):
        assert key in r
    # Only parts with actual question text are indexed.
    assert all(rec["question_text"].strip() for rec in records)


def test_retrieve_respects_limit():
    out = pr.retrieve_examples("derivatives", course="124", limit=2)
    assert len(out) <= 2


def test_retrieve_ranks_topic_matches_first():
    # Pick a topic that exists in the corpus, then confirm the top hit matches it.
    topics = [r["topic"] for r in pr._corpus("124") if r["topic"]]
    assert topics, "corpus should have labelled topics"
    target = topics[0]
    out = pr.retrieve_examples(target, course="124", limit=3)
    assert out, "expected at least one match for an in-corpus topic"
    top = out[0]
    assert target.lower() in top["topic"].lower() or any(
        target.lower() in c.lower() for c in top["concepts"]
    )


def test_unknown_topic_returns_empty_when_no_overlap():
    out = pr.retrieve_examples("nonexistent_topic_xyz", course="124", limit=2)
    assert out == []


def test_tool_is_registered_and_returns_string():
    assert retrieve_teaching_example in TUTOR_TOOLS
    # LangChain @tool: invoke via .invoke with the arg dict.
    text = retrieve_teaching_example.invoke(
        {"topic": "derivatives", "error_type": "chain_rule_omission", "course": "124"}
    )
    assert isinstance(text, str) and text.strip()
