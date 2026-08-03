"""
Problem Alignment Checker - Detect when student uploads a solution to the wrong problem.

This module prevents false positive grading by checking if the student's uploaded
work actually corresponds to the current problem before running the verifier.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlignmentSignals:
    """Extracted signals for alignment comparison."""
    numbers: set[str]  # Key numbers found (e.g., "8", "3.14", "1/2")
    expressions: set[str]  # Key expressions (e.g., "x^2", "sin(x)")
    keywords: set[str]  # Domain keywords (e.g., "derivative", "integral", "limit")
    functions: set[str]  # Function names (e.g., "f(x)", "L(x)", "g(t)")


@dataclass
class AlignmentResult:
    """Result of alignment check."""
    is_aligned: bool
    mismatch_score: int  # 0=aligned, higher=more mismatched
    details: str
    student_signals: Optional[AlignmentSignals] = None
    problem_signals: Optional[AlignmentSignals] = None


# Keywords that indicate problem structure/type
STRUCTURE_KEYWORDS = {
    # Calculus operations
    "derivative", "differentiate", "d/dx", "f'", "prime",
    "integral", "integrate", "antiderivative", "∫",
    "limit", "lim", "approaches", "→",
    # Optimization
    "maximize", "minimize", "maximum", "minimum", "critical", "extrema",
    "lagrange", "constraint", "subject to",
    # Linear approximation
    "linear approximation", "linearization", "L(x)", "tangent line",
    # Series
    "taylor", "maclaurin", "series", "expansion",
    # Multivariable
    "partial", "gradient", "∇", "directional derivative",
    "double integral", "triple integral", "polar", "cylindrical", "spherical",
    # Related rates
    "rate", "related rates", "per second", "per minute", "how fast",
    # Other
    "evaluate", "simplify", "solve", "find",
}

# Function name patterns
FUNCTION_PATTERNS = [
    r'\b[fghFGH]\s*\([xyztuvw]\)',  # f(x), g(t), h(y)
    r'\b[fghFGH]\s*\([xyztuvw],\s*[xyztuvw]\)',  # f(x,y), g(s,t)
    r'\bL\s*\([xyztuvw]\)',  # L(x) for linear approximation
    r'\b[fgh]_[xyz]\b',  # f_x, g_y (partial derivatives)
    r'\b[fgh]_{[xyz]+}\b',  # f_{xx}, g_{xy} (second derivatives)
]


def _extract_numbers(text: str) -> set[str]:
    """Extract significant numbers from text."""
    numbers = set()

    # Match integers, decimals, fractions
    # Integers and decimals
    for match in re.finditer(r'-?\b\d+\.?\d*\b', text):
        num = match.group()
        # Skip trivial numbers (0, 1, 2) that appear everywhere
        if num not in {'0', '1', '2', '-1', '-2'}:
            numbers.add(num)

    # Fractions like 1/2, 3/4
    for match in re.finditer(r'\b(\d+)\s*/\s*(\d+)\b', text):
        numbers.add(f"{match.group(1)}/{match.group(2)}")

    # Special constants
    if 'pi' in text.lower() or 'π' in text:
        numbers.add('pi')
    if re.search(r'\be\b', text) and 'exp' not in text.lower():
        numbers.add('e')

    return numbers


def _extract_expressions(text: str) -> set[str]:
    """Extract mathematical expressions from text."""
    expressions = set()
    text_lower = text.lower()

    # Common function forms
    trig_funcs = ['sin', 'cos', 'tan', 'sec', 'csc', 'cot',
                  'arcsin', 'arccos', 'arctan', 'asin', 'acos', 'atan',
                  'sinh', 'cosh', 'tanh']
    for func in trig_funcs:
        if func in text_lower:
            expressions.add(func)

    # Exponential/logarithmic
    if 'exp' in text_lower or 'e^' in text_lower or 'e**' in text_lower:
        expressions.add('exp')
    if 'log' in text_lower or 'ln' in text_lower:
        expressions.add('log')

    # Power expressions x^n
    for match in re.finditer(r'[xyzt]\s*[\^*]{1,2}\s*(\d+)', text):
        power = match.group(1)
        expressions.add(f"power_{power}")

    # Square root
    if 'sqrt' in text_lower or '√' in text:
        expressions.add('sqrt')

    # Absolute value
    if 'abs' in text_lower or '|' in text:
        expressions.add('abs')

    return expressions


def _extract_keywords(text: str) -> set[str]:
    """Extract structural keywords from text."""
    keywords = set()
    text_lower = text.lower()

    for keyword in STRUCTURE_KEYWORDS:
        if keyword.lower() in text_lower:
            keywords.add(keyword.lower())

    return keywords


def _extract_functions(text: str) -> set[str]:
    """Extract function names from text."""
    functions = set()

    for pattern in FUNCTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Normalize: f(x) -> f(x), F(x) -> f(x)
            func = match.group().lower().replace(' ', '')
            functions.add(func)

    return functions


def extract_signals(text: str) -> AlignmentSignals:
    """Extract alignment signals from text."""
    return AlignmentSignals(
        numbers=_extract_numbers(text),
        expressions=_extract_expressions(text),
        keywords=_extract_keywords(text),
        functions=_extract_functions(text),
    )


def extract_signals_from_problem(problem) -> AlignmentSignals:
    """Extract signals from a Problem object."""
    # Combine all problem text
    text_parts = []

    if problem.stem:
        text_parts.append(problem.stem)

    for part in problem.parts:
        if part.question_text:
            text_parts.append(part.question_text)
        if part.final_answer:
            text_parts.append(str(part.final_answer))

    combined_text = " ".join(text_parts)
    return extract_signals(combined_text)


def extract_signals_from_extraction(extraction) -> AlignmentSignals:
    """Extract signals from a SolutionExtraction object."""
    text_parts = []

    for part in extraction.parts:
        # Steps
        text_parts.extend(part.steps or [])
        # Final answer
        if part.student_final_answer:
            text_parts.append(part.student_final_answer)
        # Raw transcription
        if part.raw_transcription:
            text_parts.append(part.raw_transcription)

    # Overall notes
    if extraction.overall_notes:
        text_parts.append(extraction.overall_notes)

    combined_text = " ".join(text_parts)
    return extract_signals(combined_text)


def _set_overlap(set1: set, set2: set) -> bool:
    """Check if two sets have any overlap."""
    return bool(set1 & set2)


def check_alignment(
    student_signals: AlignmentSignals,
    problem_signals: AlignmentSignals,
    threshold: int = 2,
) -> AlignmentResult:
    """
    Check if student work aligns with the problem.

    Args:
        student_signals: Signals extracted from student's work
        problem_signals: Signals extracted from the problem
        threshold: Mismatch score threshold (>= this = mismatch)

    Returns:
        AlignmentResult with is_aligned status
    """
    mismatch_score = 0
    details_parts = []

    # Check numbers overlap
    if problem_signals.numbers and not _set_overlap(student_signals.numbers, problem_signals.numbers):
        mismatch_score += 1
        details_parts.append(f"Numbers: problem has {problem_signals.numbers}, student has {student_signals.numbers}")

    # Check keywords overlap
    if problem_signals.keywords and not _set_overlap(student_signals.keywords, problem_signals.keywords):
        mismatch_score += 1
        details_parts.append(f"Keywords: problem has {problem_signals.keywords}, student has {student_signals.keywords}")

    # Check expressions overlap
    if problem_signals.expressions and not _set_overlap(student_signals.expressions, problem_signals.expressions):
        mismatch_score += 1
        details_parts.append(f"Expressions: problem has {problem_signals.expressions}, student has {student_signals.expressions}")

    # Check functions overlap (only if problem has specific functions)
    if problem_signals.functions and not _set_overlap(student_signals.functions, problem_signals.functions):
        mismatch_score += 1
        details_parts.append(f"Functions: problem has {problem_signals.functions}, student has {student_signals.functions}")

    is_aligned = mismatch_score < threshold

    if is_aligned:
        details = "Student work appears to match the problem."
    else:
        details = "Possible mismatch: " + "; ".join(details_parts)

    logger.info(f"[alignment] Score: {mismatch_score}, Aligned: {is_aligned}")
    logger.debug(f"[alignment] Details: {details}")

    return AlignmentResult(
        is_aligned=is_aligned,
        mismatch_score=mismatch_score,
        details=details,
        student_signals=student_signals,
        problem_signals=problem_signals,
    )


def check_problem_alignment(problem, extraction) -> AlignmentResult:
    """
    Main entry point: Check if student's extracted work aligns with the problem.

    Args:
        problem: Problem object with parts and answers
        extraction: SolutionExtraction from vision model

    Returns:
        AlignmentResult with is_aligned=True if aligned, False if mismatched
    """
    problem_signals = extract_signals_from_problem(problem)
    student_signals = extract_signals_from_extraction(extraction)

    logger.info(f"[alignment] Problem signals: numbers={problem_signals.numbers}, "
                f"keywords={problem_signals.keywords}, expressions={problem_signals.expressions}")
    logger.info(f"[alignment] Student signals: numbers={student_signals.numbers}, "
                f"keywords={student_signals.keywords}, expressions={student_signals.expressions}")

    return check_alignment(student_signals, problem_signals)
