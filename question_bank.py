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

# User-friendly category names (mapped from internal patterns)
CATEGORY_LABELS = {
    "optimization": ["Optimization", "Max/Min"],
    "constrained_optimization": ["Lagrange Multipliers", "Constrained Optimization"],
    "related_rates": ["Related Rates"],
    "derivatives": ["Derivatives", "Differentiation"],
    "integration": ["Integration", "Integrals"],
    "limits": ["Limits", "L'Hôpital's Rule"],
}

# Additional topic keywords to detect
TOPIC_KEYWORDS = {
    "Double Integral": ["double integral", "∬", "dxdy", "dydx", "iterated integral"],
    "Triple Integral": ["triple integral", "∭", "dxdydz", "dzdydx"],
    "Polar Coordinates": ["polar", "r dr", "dθ", "r²"],
    "Spherical Coordinates": ["spherical", "ρ", "φ", "azimuthal"],
    "Cylindrical Coordinates": ["cylindrical", "r dz"],
    "Chain Rule": ["chain rule", "composite"],
    "Product Rule": ["product rule"],
    "Quotient Rule": ["quotient rule"],
    "Partial Derivatives": ["partial derivative", "∂", "fx", "fy", "fxy"],
    "Gradient": ["gradient", "∇f", "grad"],
    "Directional Derivative": ["directional derivative"],
    "Taylor Series": ["taylor", "maclaurin", "power series"],
    "U-Substitution": ["u-sub", "substitution", "let u ="],
    "Integration by Parts": ["by parts", "∫udv"],
    "Surface Area": ["surface area"],
    "Volume": ["volume", "solid of revolution"],
    "Arc Length": ["arc length"],
}


@dataclass
class Question:
    """A single calculus problem extracted from course materials."""
    id: str                          # Unique hash ID
    text: str                        # Problem text
    source: str                      # Source file name
    pattern: str                     # Detected pattern type
    problem_id: str = ""             # Problem identifier (e.g., "Problem 1", "Q2", "(a)")
    difficulty: str = "medium"       # easy/medium/hard
    categories: list = field(default_factory=list)  # User-friendly category labels
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
        # Generate categories if not provided
        if not self.categories:
            self.categories = self._detect_categories()
        # Estimate difficulty if not set
        if self.difficulty == "medium":
            self.difficulty = self._estimate_difficulty()

    def _detect_categories(self) -> list:
        """Detect user-friendly category labels from problem text."""
        categories = []
        text_lower = self.text.lower()

        # Add pattern-based categories
        if self.pattern in CATEGORY_LABELS:
            categories.append(CATEGORY_LABELS[self.pattern][0])

        # Detect additional topics
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                if topic not in categories:
                    categories.append(topic)

        return categories[:4]  # Limit to 4 labels

    def _estimate_difficulty(self) -> str:
        """Estimate difficulty based on problem characteristics."""
        text_lower = self.text.lower()
        score = 0

        # Length factor
        if len(self.text) > 300:
            score += 1
        if len(self.text) > 500:
            score += 1

        # Multi-step indicators
        hard_indicators = [
            "prove", "show that", "verify", "multiple", "combined",
            "spherical", "triple", "taylor", "series expansion",
            "partial fractions", "by parts"
        ]
        for indicator in hard_indicators:
            if indicator in text_lower:
                score += 1

        # Easy indicators
        easy_indicators = [
            "find the derivative of", "evaluate", "compute",
            "what is", "calculate"
        ]
        if any(ind in text_lower for ind in easy_indicators) and len(self.text) < 150:
            score -= 1

        if score >= 2:
            return "hard"
        elif score <= 0:
            return "easy"
        return "medium"

    def format_source(self) -> str:
        """Format a readable source citation like 'SP18 Midterm 2 Q2'."""
        # Clean up filename to readable form
        name = Path(self.source).stem  # Remove extension

        # Common exam naming patterns
        name = name.replace("_", " ").replace("-", " ")

        # Add problem identifier if available
        if self.problem_id:
            return f"{name} {self.problem_id}"
        return name

    def get_short_id(self) -> str:
        """Get a short identifier for quick reference."""
        if self.problem_id:
            # Extract just the number/letter
            import re
            match = re.search(r'(\d+|[a-z])', self.problem_id, re.I)
            if match:
                return f"P{match.group(1)}"
        return f"#{self.id[:4]}"

    def get_formatted_text(self) -> str:
        """Get problem text with basic math formatting for display."""
        return format_math_text(self.text)


def format_math_text(text: str) -> str:
    """Convert plain text math notation to LaTeX for display."""
    import re

    result = text

    # Subscript patterns: gxx -> g_{xx}, f_x -> f_x (already ok)
    # Match patterns like gxx, gyy, fxy, etc.
    result = re.sub(r'\b([fghFGH])([xyz]{2,3})\b', r'$\1_{\2}$', result)

    # Partial derivatives: ∂f/∂x
    result = re.sub(r'∂([fghFGH])/∂([xyz])', r'$\\partial \1/\\partial \2$', result)

    # Common function notations with parentheses: g(0,2) -> $g(0,2)$
    # But be careful not to double-wrap

    # Fractions in form a/b where a,b are simple
    result = re.sub(r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$', result)

    # Greek letters
    greek_map = {
        'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
        'theta': 'θ', 'lambda': 'λ', 'pi': 'π', 'rho': 'ρ',
        'sigma': 'σ', 'phi': 'φ', 'psi': 'ψ', 'omega': 'ω',
    }

    # Integral symbols
    result = result.replace('∫∫∫', '$\\iiint$')
    result = result.replace('∫∫', '$\\iint$')
    result = result.replace('∫', '$\\int$')

    # Partial symbol
    result = result.replace('∂', '$\\partial$')

    # Common superscripts: x^2, e^x
    result = re.sub(r'\^(\d+)', r'^{\1}', result)
    result = re.sub(r'\^([xyz])', r'^{\1}', result)

    # Fix double dollar signs from multiple replacements
    result = re.sub(r'\$\s*\$', ' ', result)

    return result


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
    for pattern_idx, pattern in enumerate(QUESTION_PATTERNS):
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        for match in matches:
            # Extract problem identifier and question text
            problem_id = ""
            if isinstance(match, tuple) and len(match) >= 2:
                # First group is the identifier (number or letter)
                identifier = match[0]
                q_text = match[-1].strip()

                # Format problem_id based on pattern type
                if pattern_idx == 0:  # Problem/Question/Exercise N
                    problem_id = f"Problem {identifier}"
                elif pattern_idx == 1:  # Numbered list (1. 2. 3.)
                    problem_id = f"Q{identifier}"
                elif pattern_idx == 2:  # Lettered ((a), (b), (c))
                    problem_id = f"({identifier})"
            else:
                q_text = match.strip() if isinstance(match, str) else str(match)

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
                problem_id=problem_id,
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
