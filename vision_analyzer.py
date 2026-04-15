"""
Vision Analyzer - Multi-image analysis of handwritten solutions.

Uses Gemini Flash vision to analyze uploaded photos and provide
structured feedback per problem part.
"""

import json
import os
import httpx
from dataclasses import dataclass, field
from typing import Optional

from problem_loader import Problem
from grader import GradingResult


def _get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from env or secrets."""
    # Try env first
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Try streamlit secrets
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    return None


@dataclass
class PartExtraction:
    """Extracted data from a single problem part (vision model output)."""
    part_label: str  # "a", "b", "c", or "" for single-part
    steps: list[str]  # Steps the student wrote for this part
    student_final_answer: Optional[str]  # Student's final answer (extracted)
    error_candidates: list[dict]  # [{step: int, description: str, type: str}] - suspected errors
    suspected_error_type: Optional[str]  # concept|algebra|logic|careless|uncertain (LLM guess, not authoritative)
    confidence: float  # Model's confidence in extraction (0-1)
    raw_transcription: Optional[str]  # Full transcription of handwritten work


@dataclass
class PartAnalysis:
    """Full analysis of a single problem part (after verifier)."""
    part_label: str
    steps: list[str]
    student_final_answer: Optional[str]
    official_answer: Optional[str]
    is_correct: bool  # From verifier, not LLM
    is_uncertain: bool  # True if verifier couldn't determine
    verifier_result: Optional[dict]  # Full verifier output
    error_candidates: list[dict]
    error_type: Optional[str]
    feedback: str
    hint: str
    confidence: float


@dataclass
class SolutionExtraction:
    """Raw extraction from vision model (before verifier)."""
    parts: list[PartExtraction]
    overall_notes: str  # Any notes from vision model
    extraction_confidence: float  # Overall confidence in extraction


@dataclass
class SolutionAnalysis:
    """Full analysis of student's solution across all parts (after verifier)."""
    parts: list[PartAnalysis]
    overall_summary: str  # Brief summary of performance
    profile_update_hints: dict  # Hints for updating student profile
    any_incorrect: bool  # True if any part is incorrect
    any_uncertain: bool  # True if any part couldn't be verified


def _build_problem_context(problem: Problem) -> str:
    """Build problem context string for the prompt."""
    parts_text = []

    if problem.stem:
        parts_text.append(f"Problem stem: {problem.stem}")

    for i, part in enumerate(problem.parts):
        label = part.label or str(i + 1)
        answer = part.final_answer or "(no answer provided)"
        parts_text.append(f"Part ({label}): {part.question_text}")
        parts_text.append(f"  Correct answer: {answer}")

    return "\n".join(parts_text)


import logging

logger = logging.getLogger(__name__)


def _download_image(url: str) -> Optional[bytes]:
    """Download image from URL and return bytes."""
    try:
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning(f"[vision_analyzer] Failed to download {url}: {e}")
        return None


def extract_handwritten_solution(
    problem: Problem,
    image_urls: list[str],
) -> Optional[SolutionExtraction]:
    """
    Extract structured data from handwritten solution images using Gemini Flash vision.

    IMPORTANT: This function only EXTRACTS data, it does NOT judge correctness.
    Use analyze_with_verifier() to get final is_correct judgments.

    Args:
        problem: The Problem object with parts and answers
        image_urls: List of signed URLs for uploaded images

    Returns:
        SolutionExtraction with per-part extracted data, or None on error
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        logger.error("[vision_analyzer] No GEMINI_API_KEY")
        return None

    if not image_urls:
        logger.error("[vision_analyzer] No images provided")
        return None

    try:
        import google.generativeai as genai
        from PIL import Image
        import io

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

        # Build problem context (without revealing we will verify separately)
        problem_context = _build_problem_context(problem)

        # Build part labels list
        part_labels = [p.label or str(i + 1) for i, p in enumerate(problem.parts)]

        # EXTRACTION-ONLY prompt - no is_correct judgment
        prompt = f"""Extract structured data from these handwritten math solution images.

PROBLEM:
{problem_context}

YOUR TASK: Extract what the student wrote. DO NOT judge if it's correct - just transcribe accurately.

For EACH problem part ({', '.join(part_labels)}), extract:
1. The steps the student wrote (transcribe their work)
2. Their final answer (exactly as written)
3. Any suspected errors you notice (these are CANDIDATES, not final judgment)
4. Your confidence in reading their handwriting

Output ONLY valid JSON in this format:
{{
  "parts": [
    {{
      "part_label": "a",
      "steps": ["step 1 transcription", "step 2 transcription"],
      "student_final_answer": "exactly what student wrote as final answer, or null if not found",
      "raw_transcription": "full transcription of student's work for this part",
      "error_candidates": [
        {{"step": 1, "description": "possible issue observed", "type": "algebra"}}
      ],
      "suspected_error_type": "algebra" or "concept" or "logic" or "careless" or "uncertain" or null,
      "confidence": 0.95
    }}
  ],
  "overall_notes": "Any notes about legibility or structure",
  "extraction_confidence": 0.9
}}

Error types (for error_candidates):
- concept: Possibly wrong formula or approach
- algebra: Possible arithmetic mistake
- logic: Possible reasoning issue
- careless: Possible minor slip
- uncertain: Cannot determine

Rules:
- Include ALL parts, even if not attempted (student_final_answer = null)
- Convert handwritten math to LaTeX where appropriate
- Be specific about what you observe
- Confidence reflects how clearly you could read the handwriting
- DO NOT make final correctness judgments - just extract and note observations

Output ONLY the JSON, no other text."""

        # Download and prepare images
        content_parts = []
        for url in image_urls:
            image_bytes = _download_image(url)
            if image_bytes:
                img = Image.open(io.BytesIO(image_bytes))
                content_parts.append(img)

        if not content_parts:
            print("[vision_analyzer] No images could be downloaded")
            return None

        # Add prompt
        content_parts.append(prompt)

        # Call Gemini
        response = model.generate_content(content_parts)
        output = response.text.strip()

        # Extract JSON from response
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
        output = output.strip()

        data = json.loads(output)

        # Parse into PartExtraction dataclasses
        parts = []
        for p in data.get("parts", []):
            parts.append(PartExtraction(
                part_label=p.get("part_label", ""),
                steps=p.get("steps", []),
                student_final_answer=p.get("student_final_answer"),
                error_candidates=p.get("error_candidates", []),
                suspected_error_type=p.get("suspected_error_type"),
                confidence=p.get("confidence", 0.5),
                raw_transcription=p.get("raw_transcription"),
            ))

        logger.info(f"[vision_analyzer] Extracted {len(parts)} parts")
        return SolutionExtraction(
            parts=parts,
            overall_notes=data.get("overall_notes", ""),
            extraction_confidence=data.get("extraction_confidence", 0.5),
        )

    except Exception as e:
        logger.error(f"[vision_analyzer] Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_with_verifier(
    extraction: SolutionExtraction,
    problem: Problem,
) -> SolutionAnalysis:
    """
    Apply verifier to extracted data to determine correctness.

    Args:
        extraction: SolutionExtraction from extract_handwritten_solution()
        problem: The Problem object with official answers

    Returns:
        SolutionAnalysis with verified is_correct for each part
    """
    from verifier import verify_answer, AnswerVerificationResult

    analyzed_parts = []
    any_incorrect = False
    any_uncertain = False

    for i, ext in enumerate(extraction.parts):
        # Get official answer for this part
        official_answer = None
        if i < len(problem.parts):
            official_answer = problem.parts[i].final_answer

        # Run verifier
        verifier_result = None
        is_correct = False
        is_uncertain = True

        if ext.student_final_answer and official_answer:
            # Build problem context for verifier
            context = problem.stem or ""
            if i < len(problem.parts):
                context += " " + (problem.parts[i].question_text or "")

            vr = verify_answer(
                student_answer=ext.student_final_answer,
                official_answer=official_answer,
                problem_context=context,
            )
            verifier_result = {
                "is_correct": vr.is_correct,
                "is_uncertain": vr.is_uncertain,
                "verifier_type": vr.verifier_type,
                "reason": vr.reason,
                "confidence": vr.confidence,
            }
            is_correct = vr.is_correct
            is_uncertain = vr.is_uncertain
        elif not ext.student_final_answer:
            # No answer extracted
            is_correct = False
            is_uncertain = False
            verifier_result = {"reason": "No answer extracted from student work"}

        # Track overall status
        if not is_correct and not is_uncertain:
            any_incorrect = True
        if is_uncertain:
            any_uncertain = True

        # Generate feedback and hint based on verifier result
        if is_correct:
            feedback = "Correct!"
            hint = ""
            error_type = None
        elif is_uncertain:
            feedback = "Unable to verify your answer automatically."
            hint = "Please check your work carefully."
            error_type = ext.suspected_error_type
        else:
            # Incorrect - use LLM's error candidates
            feedback = f"Your answer doesn't match the expected result."
            if ext.error_candidates:
                first_error = ext.error_candidates[0]
                feedback += f" Possible issue: {first_error.get('description', '')}"
            hint = "Review your calculation steps."
            error_type = ext.suspected_error_type

        analyzed_parts.append(PartAnalysis(
            part_label=ext.part_label,
            steps=ext.steps,
            student_final_answer=ext.student_final_answer,
            official_answer=official_answer,
            is_correct=is_correct,
            is_uncertain=is_uncertain,
            verifier_result=verifier_result,
            error_candidates=ext.error_candidates,
            error_type=error_type,
            feedback=feedback,
            hint=hint,
            confidence=ext.confidence,
        ))

    # Generate overall summary
    correct_count = sum(1 for p in analyzed_parts if p.is_correct)
    total_count = len(analyzed_parts)
    summary = f"{correct_count}/{total_count} parts correct."
    if any_uncertain:
        summary += " Some parts could not be verified automatically."

    return SolutionAnalysis(
        parts=analyzed_parts,
        overall_summary=summary,
        profile_update_hints={},  # Will be populated by caller if needed
        any_incorrect=any_incorrect,
        any_uncertain=any_uncertain,
    )


def analyze_handwritten_solution(
    problem: Problem,
    image_urls: list[str],
) -> Optional[SolutionAnalysis]:
    """
    Full pipeline: extract from images + verify with SymPy.

    This is the main entry point that combines extraction and verification.

    Args:
        problem: The Problem object with parts and answers
        image_urls: List of signed URLs for uploaded images

    Returns:
        SolutionAnalysis with verified results, or None on error
    """
    # Step 1: Extract from images
    extraction = extract_handwritten_solution(problem, image_urls)
    if not extraction:
        return None

    # Step 2: Verify with SymPy
    analysis = analyze_with_verifier(extraction, problem)

    logger.info(f"[vision_analyzer] Analysis complete: {analysis.overall_summary}")
    return analysis


def analysis_to_grading_result(
    analysis: SolutionAnalysis,
    part_index: int = 0,
) -> GradingResult:
    """
    Convert SolutionAnalysis to GradingResult for display compatibility.

    Args:
        analysis: Full solution analysis
        part_index: Which part to extract (default first)

    Returns:
        GradingResult for the specified part
    """
    if not analysis or not analysis.parts:
        return GradingResult(
            error_step=None,
            error_type=None,
            feedback="Unable to analyze solution",
            hint="",
            is_correct=False,
        )

    # Get the specified part (or first if index out of range)
    if part_index < len(analysis.parts):
        part = analysis.parts[part_index]
    else:
        part = analysis.parts[0]

    # Find first error step if any
    error_step = None
    if part.error_candidates:
        error_step = part.error_candidates[0].get("step", 0)

    return GradingResult(
        error_step=error_step,
        error_type=part.error_type,
        feedback=part.feedback,
        hint=part.hint,
        is_correct=part.is_correct,
    )


def get_combined_feedback(analysis: SolutionAnalysis) -> str:
    """
    Get combined feedback string for all parts.

    Args:
        analysis: Full solution analysis

    Returns:
        Formatted feedback string
    """
    if not analysis or not analysis.parts:
        return "Unable to analyze solution."

    lines = []

    # Per-part feedback
    for part in analysis.parts:
        label = f"({part.part_label})" if part.part_label else ""

        if part.is_correct:
            lines.append(f"**Part {label}**: Correct!")
        else:
            lines.append(f"**Part {label}**: {part.feedback}")
            if part.hint:
                lines.append(f"  *Hint: {part.hint}*")

        lines.append("")

    # Overall summary
    if analysis.overall_summary:
        lines.append(f"**Summary:** {analysis.overall_summary}")

    return "\n".join(lines)
