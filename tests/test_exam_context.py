"""Tests for exam_context module."""

from exam_context import analyze_materials, analyze_files, ExamContext, add_material, clear_context


def test_analyze_materials_detects_patterns():
    """Test that analyze_materials detects patterns from text."""
    texts = [
        "Midterm covers: optimization, Lagrange multipliers, related rates. "
        "Practice finding maximum and minimum values subject to constraints."
    ]

    context = analyze_materials(texts, ["review.txt"])

    assert context.has_context()
    assert len(context.materials) == 1
    assert len(context.detected_patterns) >= 2

    pattern_names = context.get_pattern_names()
    assert "optimization" in pattern_names
    assert "constrained_optimization" in pattern_names


def test_analyze_materials_empty():
    """Test that empty materials return empty context."""
    context = analyze_materials([], [])

    assert not context.has_context()
    assert len(context.materials) == 0
    assert len(context.detected_patterns) == 0


def test_format_for_prompt():
    """Test that context formats correctly for prompt."""
    texts = ["Find the maximum of f(x,y) subject to constraint g(x,y) = c"]
    context = analyze_materials(texts)

    prompt_text = context.format_for_prompt()

    assert "[EXAM CONTEXT" in prompt_text
    assert "Materials loaded:" in prompt_text


def test_add_material():
    """Test adding material to existing context."""
    context = analyze_materials(["optimization problem"], ["file1.txt"])
    assert len(context.materials) == 1

    context = add_material(context, "integration by parts", "file2.txt")
    assert len(context.materials) == 2


def test_clear_context():
    """Test clearing context."""
    context = clear_context()

    assert not context.has_context()
    assert len(context.materials) == 0


def test_get_top_patterns():
    """Test getting top N patterns."""
    texts = [
        "Lagrange multiplier optimization subject to constraint. "
        "Maximum and minimum values. Integration by parts."
    ]
    context = analyze_materials(texts)

    top = context.get_top_patterns(2)
    assert len(top) <= 2


def test_pattern_priority():
    """Test that detected patterns have priority hints."""
    texts = ["Find the derivative using chain rule and product rule."]
    context = analyze_materials(texts)

    if context.detected_patterns:
        p = context.detected_patterns[0]
        assert p.priority  # Should have a priority hint
        assert len(p.evidence) > 0  # Should have evidence


def test_analyze_files():
    """Test analyzing file bytes including question extraction."""
    content = b"""
    Problem 1. Find the derivative of x^3
    Problem 2. Maximize f(x,y) subject to x + y = 10
    """

    files = [("exam.txt", content)]
    context = analyze_files(files)

    assert context.has_context()
    assert len(context.materials) == 1
    # Should have question bank
    assert context.question_bank is not None


def test_has_questions():
    """Test question bank integration."""
    content = b"""
    Problem 1. Find the derivative of sin(x)
    Problem 2. Evaluate the integral of cos(x) dx
    """

    files = [("test.txt", content)]
    context = analyze_files(files)

    # Check question-related methods
    if context.has_questions():
        assert context.get_question_count() > 0
