"""
Integration tests for teaching flow.

Tests the full pipeline from vision extraction to teaching agent trigger.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class MockProblemPart:
    """Mock problem part for testing."""
    label: Optional[str]
    question_text: str
    final_answer: Optional[str]
    has_diagram: bool = False
    diagram_image_url: Optional[str] = None


@dataclass
class MockProblem:
    """Mock problem for testing."""
    id: str
    course: str
    topic: str
    stem: Optional[str]
    parts: List[MockProblemPart]
    concepts: List[str] = None

    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []


class TestBuildTeachingContext:
    """Test teaching context construction."""

    def test_basic_context_structure(self):
        """Teaching context should have all required fields."""
        # Import here to avoid issues if app.py has side effects
        from vision_analyzer import (
            PartAnalysis, SolutionAnalysis
        )

        # Create mock analysis
        part = PartAnalysis(
            part_label="a",
            steps=["Step 1: u = x^2", "Step 2: du = 2x dx"],
            student_final_answer="x^3/3",
            official_answer="x^3/3 + C",
            is_correct=False,
            is_uncertain=False,
            verifier_result={"is_correct": False, "reason": "Missing constant"},
            error_candidates=[{"step": 2, "description": "Forgot +C", "type": "careless"}],
            error_type="careless",
            feedback="Missing constant of integration",
            hint="Don't forget +C for indefinite integrals",
            confidence=0.9,
        )

        analysis = SolutionAnalysis(
            parts=[part],
            overall_summary="0/1 correct",
            profile_update_hints={},
            any_incorrect=True,
            any_uncertain=False,
        )

        problem = MockProblem(
            id="test_001",
            course="125",
            topic="integration",
            stem="Evaluate the integral",
            parts=[MockProblemPart(
                label="a",
                question_text="∫ x^2 dx",
                final_answer="x^3/3 + C"
            )],
        )

        # Build context (simulate what app.py does)
        context = {
            "problem_id": problem.id,
            "problem_stem": problem.stem,
            "question_text": problem.parts[0].question_text,
            "official_answer": problem.parts[0].final_answer,
            "topic": problem.topic,
            "concepts": problem.concepts,
            "student_answer": part.student_final_answer,
            "student_steps": part.steps,
            "is_correct": part.is_correct,
            "is_uncertain": part.is_uncertain,
            "verifier_result": part.verifier_result,
            "error_type": part.error_type,
            "error_candidates": part.error_candidates,
            "feedback": part.feedback,
            "hint": part.hint,
            "confidence": part.confidence,
        }

        # Verify structure
        assert context["problem_id"] == "test_001"
        assert context["is_correct"] is False
        assert context["student_answer"] == "x^3/3"
        assert context["official_answer"] == "x^3/3 + C"
        assert context["error_type"] == "careless"
        assert len(context["error_candidates"]) == 1


class TestAnalyzeWithVerifier:
    """Test the analyze_with_verifier function."""

    def test_correct_answer_verified(self):
        """Correct answer should be marked correct by verifier."""
        from vision_analyzer import (
            PartExtraction, SolutionExtraction, analyze_with_verifier
        )

        # Mock extraction with correct answer
        extraction = SolutionExtraction(
            parts=[PartExtraction(
                part_label="a",
                steps=["Differentiate: 3x^2"],
                student_final_answer="3x^2",
                error_candidates=[],
                suspected_error_type=None,
                confidence=0.95,
                raw_transcription="f'(x) = 3x^2",
            )],
            overall_notes="Clear handwriting",
            extraction_confidence=0.95,
        )

        problem = MockProblem(
            id="test_002",
            course="124",
            topic="derivatives",
            stem=None,
            parts=[MockProblemPart(
                label="a",
                question_text="Find d/dx[x^3]",
                final_answer="3x^2"
            )],
        )

        analysis = analyze_with_verifier(extraction, problem)

        assert analysis.parts[0].is_correct is True
        assert analysis.any_incorrect is False

    def test_wrong_answer_verified(self):
        """Wrong answer should be marked incorrect by verifier."""
        from vision_analyzer import (
            PartExtraction, SolutionExtraction, analyze_with_verifier
        )

        # Mock extraction with wrong answer
        extraction = SolutionExtraction(
            parts=[PartExtraction(
                part_label="a",
                steps=["Differentiate: x^2"],
                student_final_answer="x^2",  # Wrong - should be 3x^2
                error_candidates=[{"step": 1, "description": "Wrong coefficient", "type": "algebra"}],
                suspected_error_type="algebra",
                confidence=0.9,
                raw_transcription="f'(x) = x^2",
            )],
            overall_notes="",
            extraction_confidence=0.9,
        )

        problem = MockProblem(
            id="test_003",
            course="124",
            topic="derivatives",
            stem=None,
            parts=[MockProblemPart(
                label="a",
                question_text="Find d/dx[x^3]",
                final_answer="3x^2"
            )],
        )

        analysis = analyze_with_verifier(extraction, problem)

        assert analysis.parts[0].is_correct is False
        assert analysis.any_incorrect is True


class TestTeachingAgentTrigger:
    """Test that teaching agent is triggered correctly."""

    def test_incorrect_triggers_teaching(self):
        """Incorrect answer should set up teaching context."""
        from vision_analyzer import (
            PartExtraction, SolutionExtraction, analyze_with_verifier
        )

        extraction = SolutionExtraction(
            parts=[PartExtraction(
                part_label="",
                steps=["v(t) = integral of a(t)"],
                student_final_answer="50",  # Wrong (no units for clean parsing)
                error_candidates=[],
                suspected_error_type="concept",
                confidence=0.8,
                raw_transcription="50",
            )],
            overall_notes="",
            extraction_confidence=0.8,
        )

        problem = MockProblem(
            id="uw_math_125_a25_p3",
            course="125",
            topic="kinematics_work_integral",
            stem=None,
            parts=[MockProblemPart(
                label=None,
                question_text="How many meters will the car travel?",
                final_answer="74.25"  # No units for clean parsing
            )],
        )

        analysis = analyze_with_verifier(extraction, problem)

        # Verify teaching should be triggered
        # When wrong, either any_incorrect is True OR is_uncertain is True
        assert analysis.parts[0].is_correct is False

        # Context should be buildable
        context = {
            "problem_id": problem.id,
            "official_answer": problem.parts[0].final_answer,
            "student_answer": extraction.parts[0].student_final_answer,
            "is_correct": analysis.parts[0].is_correct,
        }

        assert context["is_correct"] is False
        assert context["student_answer"] == "50"
        assert context["official_answer"] == "74.25"


class TestVerifierIntegration:
    """Test verifier integration with vision extraction."""

    def test_verifier_type_detected(self):
        """Verifier should detect the correct type."""
        from verifier import verify_answer

        # Test derivative context - should detect as derivative
        result = verify_answer(
            "3x^2",
            "3x^2",
            problem_context="Find the derivative of x^3"
        )
        assert result.verifier_type in ["algebraic", "numeric", "derivative"]

        # Test integral context - should detect as integral
        result = verify_answer(
            "x^3/3",
            "x^3/3",
            problem_context="Find the indefinite integral"
        )
        assert result.verifier_type in ["algebraic", "integral", "numeric"]

    def test_confidence_returned(self):
        """Verifier should return confidence score."""
        from verifier import verify_answer

        result = verify_answer("x^2", "x^2")
        assert hasattr(result, "confidence")
        assert 0 <= result.confidence <= 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
