"""Tests for question_bank module."""

from question_bank import (
    Question,
    QuestionBank,
    extract_questions_from_text,
    build_question_bank,
    is_calculus_question,
)


def test_question_creation():
    """Test Question dataclass."""
    q = Question(
        id="",
        text="Find the derivative of x^2",
        source="test.txt",
        pattern="derivatives"
    )

    assert q.id  # Auto-generated
    assert q.text == "Find the derivative of x^2"
    assert q.pattern == "derivatives"
    assert q.heuristic_file == "heuristics/derivatives.md"


def test_question_bank_operations():
    """Test QuestionBank add and query operations."""
    bank = QuestionBank()

    q1 = Question(id="1", text="Derivative problem", source="a.txt", pattern="derivatives")
    q2 = Question(id="2", text="Integral problem", source="a.txt", pattern="integration")
    q3 = Question(id="3", text="Another derivative", source="b.txt", pattern="derivatives")

    bank.add(q1)
    bank.add(q2)
    bank.add(q3)

    assert len(bank) == 3
    assert len(bank.get_by_pattern("derivatives")) == 2
    assert len(bank.get_by_pattern("integration")) == 1
    assert len(bank.get_by_source("a.txt")) == 2
    assert "derivatives" in bank.get_patterns()
    assert bank.get_pattern_counts()["derivatives"] == 2


def test_is_calculus_question():
    """Test calculus question detection."""
    assert is_calculus_question("Find the derivative of x^2")
    assert is_calculus_question("Evaluate the integral of sin(x)")
    assert is_calculus_question("What is the limit as x approaches 0")
    assert not is_calculus_question("What is your name?")
    assert not is_calculus_question("Hello world")


def test_extract_questions_from_text():
    """Test question extraction from text."""
    text = """
    Problem 1. Find the derivative of f(x) = x^3
    Problem 2. Evaluate the integral of cos(x) dx
    Problem 3. Find the limit of (1-cos(x))/x as x approaches 0
    """

    questions = extract_questions_from_text(text, "test.txt")

    assert len(questions) >= 2  # Should extract at least 2
    patterns = [q.pattern for q in questions]
    # Should have detected some patterns
    assert any(p in patterns for p in ["derivatives", "integration", "limits"])


def test_extract_questions_numbered_list():
    """Test extraction from numbered list format."""
    text = """
    1. Find the maximum of f(x) = x^2 - 4x + 3
    2. Calculate the integral of e^x dx
    3. Determine the limit of sin(x)/x as x→0
    """

    questions = extract_questions_from_text(text, "exam.txt")

    assert len(questions) >= 1


def test_build_question_bank():
    """Test building question bank from file bytes."""
    content = b"""
    Problem 1. Find the derivative of ln(x)
    Problem 2. Maximize f(x,y) = xy subject to x + y = 10
    """

    files = [("test.txt", content)]
    bank = build_question_bank(files)

    assert len(bank) >= 1


def test_sample_by_pattern():
    """Test random sampling by pattern."""
    bank = QuestionBank()

    for i in range(5):
        bank.add(Question(
            id=str(i),
            text=f"Derivative problem {i}",
            source="test.txt",
            pattern="derivatives"
        ))

    samples = bank.sample_by_pattern("derivatives", 3)
    assert len(samples) == 3

    # Should return empty list for non-existent pattern
    assert bank.sample_by_pattern("nonexistent", 3) == []
