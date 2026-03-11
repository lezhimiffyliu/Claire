"""
Question Bank Module - Extract and organize problems from course materials.

Supports: PDF, TXT, MD files
Extracts questions, classifies by pattern, links to heuristics.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from pattern_tools import detect_pattern, PATTERNS


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Question:
    """A single calculus problem extracted from course materials."""
    id: str                          # Unique hash ID
    text: str                        # Problem text
    source: str                      # Source file name
    pattern: str                     # Detected pattern type
    difficulty: str = "intermediate" # beginner/intermediate/advanced
    heuristic_file: str = ""         # Path to heuristic .md file
    solution: Optional[str] = None   # Solution if available
    metadata: dict = field(default_factory=dict)  # Extra info

    def __post_init__(self):
        # Generate ID from text hash if not provided
        if not self.id:
            self.id = hashlib.md5(self.text.encode()).hexdigest()[:8]
        # Set heuristic file based on pattern
        if not self.heuristic_file and self.pattern in PATTERNS:
            self.heuristic_file = f"heuristics/{self.pattern}.md"


@dataclass
class QuestionBank:
    """Collection of questions with indexing by pattern and source."""
    questions: list[Question] = field(default_factory=list)

    # Indices (built automatically)
    _by_pattern: dict[str, list[Question]] = field(default_factory=dict)
    _by_source: dict[str, list[Question]] = field(default_factory=dict)

    def add(self, question: Question) -> None:
        """Add a question to the bank."""
        self.questions.append(question)
        self._index_question(question)

    def _index_question(self, q: Question) -> None:
        """Add question to indices."""
        if q.pattern not in self._by_pattern:
            self._by_pattern[q.pattern] = []
        self._by_pattern[q.pattern].append(q)

        if q.source not in self._by_source:
            self._by_source[q.source] = []
        self._by_source[q.source].append(q)

    def get_by_pattern(self, pattern: str) -> list[Question]:
        """Get all questions for a pattern."""
        return self._by_pattern.get(pattern, [])

    def get_by_source(self, source: str) -> list[Question]:
        """Get all questions from a source file."""
        return self._by_source.get(source, [])

    def get_patterns(self) -> list[str]:
        """Get list of patterns with questions."""
        return list(self._by_pattern.keys())

    def get_pattern_counts(self) -> dict[str, int]:
        """Get count of questions per pattern."""
        return {p: len(qs) for p, qs in self._by_pattern.items()}

    def sample_by_pattern(self, pattern: str, n: int = 1) -> list[Question]:
        """Get N random questions for a pattern."""
        import random
        qs = self.get_by_pattern(pattern)
        return random.sample(qs, min(n, len(qs)))

    def __len__(self) -> int:
        return len(self.questions)


# ============================================================
# PDF PARSING
# ============================================================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    text_parts = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        text = page.get_text()
        text_parts.append(text)

    doc.close()
    return "\n\n".join(text_parts)


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract text from file based on extension."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in [".txt", ".md", ".text", ".markdown"]:
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        # Try as text
        return file_bytes.decode("utf-8", errors="ignore")


# ============================================================
# QUESTION EXTRACTION
# ============================================================

# Patterns that indicate a question/problem
QUESTION_PATTERNS = [
    # Numbered problems
    r"(?:^|\n)\s*(?:Problem|Question|Exercise|Q\.?|P\.?)\s*(\d+)[.:\s](.+?)(?=\n\s*(?:Problem|Question|Exercise|Q\.?|P\.?)\s*\d+|\n\n\n|\Z)",
    # Numbered list with math keywords
    r"(?:^|\n)\s*(\d+)[.)\s]+\s*((?:Find|Calculate|Compute|Evaluate|Determine|Solve|Prove|Show|What|If|Let|Given).+?)(?=\n\s*\d+[.)\s]|\n\n\n|\Z)",
    # Lettered problems (a), (b), etc.
    r"(?:^|\n)\s*\(([a-z])\)\s*((?:Find|Calculate|Compute|Evaluate|Determine|Solve).+?)(?=\n\s*\([a-z]\)|\n\n|\Z)",
]

# Keywords that strongly indicate a calculus problem
CALCULUS_KEYWORDS = [
    "derivative", "differentiate", "d/dx", "f'(x)",
    "integral", "integrate", "∫", "antiderivative",
    "limit", "lim", "approaches",
    "maximize", "minimize", "maximum", "minimum",
    "rate of change", "related rates",
    "lagrange", "constraint", "subject to",
    "tangent", "slope", "critical point",
    "area under", "volume of revolution",
]


def is_calculus_question(text: str) -> bool:
    """Check if text looks like a calculus question."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CALCULUS_KEYWORDS)


def extract_questions_from_text(text: str, source: str) -> list[Question]:
    """Extract individual questions from text content."""
    questions = []
    seen_texts = set()  # Deduplicate

    # Try each pattern
    for pattern in QUESTION_PATTERNS:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        for match in matches:
            # Extract question text (last group in match)
            if isinstance(match, tuple):
                q_text = match[-1].strip()
            else:
                q_text = match.strip()

            # Clean up
            q_text = re.sub(r'\s+', ' ', q_text)
            q_text = q_text.strip()

            # Skip if too short or already seen
            if len(q_text) < 20:
                continue
            if q_text in seen_texts:
                continue

            # Check if it's a calculus question
            if not is_calculus_question(q_text):
                continue

            seen_texts.add(q_text)

            # Detect pattern
            calc_pattern = detect_pattern(q_text)

            questions.append(Question(
                id="",
                text=q_text,
                source=source,
                pattern=calc_pattern,
            ))

    # If no structured questions found, try to split by double newlines
    if not questions:
        paragraphs = re.split(r'\n\n+', text)
        for para in paragraphs:
            para = para.strip()
            if len(para) < 30 or len(para) > 500:
                continue
            if not is_calculus_question(para):
                continue
            if para in seen_texts:
                continue

            seen_texts.add(para)
            calc_pattern = detect_pattern(para)

            questions.append(Question(
                id="",
                text=para,
                source=source,
                pattern=calc_pattern,
            ))

    return questions


# ============================================================
# MAIN API
# ============================================================

def build_question_bank(files: list[tuple[str, bytes]]) -> QuestionBank:
    """
    Build a question bank from uploaded files.

    Args:
        files: List of (filename, file_bytes) tuples

    Returns:
        QuestionBank with extracted and classified questions
    """
    bank = QuestionBank()

    for filename, file_bytes in files:
        try:
            # Extract text
            text = extract_text_from_file(file_bytes, filename)

            # Extract questions
            questions = extract_questions_from_text(text, filename)

            # Add to bank
            for q in questions:
                bank.add(q)

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    return bank


def merge_banks(banks: list[QuestionBank]) -> QuestionBank:
    """Merge multiple question banks into one."""
    merged = QuestionBank()
    seen_ids = set()

    for bank in banks:
        for q in bank.questions:
            if q.id not in seen_ids:
                merged.add(q)
                seen_ids.add(q.id)

    return merged


# ============================================================
# HEURISTIC INTEGRATION
# ============================================================

def get_questions_with_heuristics(bank: QuestionBank) -> dict[str, list[Question]]:
    """
    Group questions by their heuristic file.

    Returns:
        Dict mapping heuristic file path to list of questions
    """
    by_heuristic = {}

    for q in bank.questions:
        if q.heuristic_file:
            if q.heuristic_file not in by_heuristic:
                by_heuristic[q.heuristic_file] = []
            by_heuristic[q.heuristic_file].append(q)

    return by_heuristic


def get_practice_sequence(bank: QuestionBank, pattern: str, n: int = 5) -> list[Question]:
    """
    Get a practice sequence for a pattern.

    Returns questions in order from simple to complex based on text length
    as a rough proxy for difficulty.
    """
    questions = bank.get_by_pattern(pattern)

    # Sort by text length (rough difficulty proxy)
    sorted_qs = sorted(questions, key=lambda q: len(q.text))

    return sorted_qs[:n]
