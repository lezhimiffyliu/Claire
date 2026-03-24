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
    pattern: str                     # Legacy coarse pattern (for backwards compat)
    problem_id: str = ""             # Problem identifier (e.g., "Problem 1", "Q2", "(a)")
    difficulty: str = "medium"       # easy/medium/hard
    categories: list = field(default_factory=list)  # User-friendly category labels
    topics: list = field(default_factory=list)      # Fine-grained topic IDs (NEW)
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
        # Convert topics to display names for categories
        if self.topics and not self.categories:
            self.categories = self._topics_to_categories()

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

    def _topics_to_categories(self) -> list:
        """Convert fine-grained topics to display categories."""
        try:
            from topics import get_topic_display
            return [get_topic_display(t) for t in self.topics[:4]]
        except ImportError:
            return [t.replace("_", " ").title() for t in self.topics[:4]]

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
    """
    Convert plain text math notation to LaTeX for Streamlit display.
    Wraps math expressions in $...$ for inline rendering.

    Note: This is only used as fallback when LLM parsing is unavailable.
    Primary parsing happens at upload time via parse_questions_with_llm().
    """
    import re

    result = text

    # If already has LaTeX ($...$), don't double-process
    if '$' in result and ('\\' in result or '_' in result):
        return result

    # Subscript patterns: fxx -> $f_{xx}$, gxy -> $g_{xy}$
    result = re.sub(r'\b([fghFGH])([xyz]{2,3})\b', r'$\1_{\2}$', result)

    # Function with subscript: f_x, f_y, g_x
    result = re.sub(r'\b([fghFGH])_([xyz])\b', r'$\1_\2$', result)

    # Partial derivatives: ∂f/∂x, ∂²f/∂x²
    result = re.sub(r'∂([fghFGH])/∂([xyz])', r'$\\frac{\\partial \1}{\\partial \2}$', result)
    result = re.sub(r'∂²([fghFGH])/∂([xyz])²', r'$\\frac{\\partial^2 \1}{\\partial \2^2}$', result)

    # Simple fractions: a/b where a,b are numbers or single letters
    result = re.sub(r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$', result)

    # Integral symbols
    result = result.replace('∫∫∫', '$\\iiint$')
    result = result.replace('∫∫', '$\\iint$')
    result = result.replace('∫', '$\\int$')

    # Partial symbol standalone
    result = result.replace('∂', '$\\partial$')

    # Nabla/gradient
    result = result.replace('∇', '$\\nabla$')

    # Greek letters (standalone)
    greek = {
        'α': '$\\alpha$', 'β': '$\\beta$', 'γ': '$\\gamma$', 'δ': '$\\delta$',
        'θ': '$\\theta$', 'λ': '$\\lambda$', 'π': '$\\pi$', 'ρ': '$\\rho$',
        'σ': '$\\sigma$', 'φ': '$\\phi$', 'ψ': '$\\psi$', 'ω': '$\\omega$',
    }
    for sym, latex in greek.items():
        result = result.replace(sym, latex)

    # Superscripts: x^2, x^3, e^x - wrap in math mode
    result = re.sub(r'([a-zA-Z])\^(\d+)', r'$\1^{\2}$', result)
    result = re.sub(r'([a-zA-Z])\^([a-zA-Z])', r'$\1^{\2}$', result)

    # Common expressions: x², y², x³
    result = result.replace('²', '$^2$')
    result = result.replace('³', '$^3$')
    result = result.replace('⁴', '$^4$')

    # Square root
    result = result.replace('√', '$\\sqrt{}$')

    # Infinity
    result = result.replace('∞', '$\\infty$')

    # Plus/minus
    result = result.replace('±', '$\\pm$')

    # Fix adjacent dollar signs from multiple replacements: $...$ $...$ -> $... ...$
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
# LLM PARSING (at ingestion time, NOT display time)
# ============================================================

PARSE_PROMPT = '''You are parsing a calculus exam/worksheet PDF.

Convert the raw text into a structured JSON format with clean LaTeX math.

CRITICAL REQUIREMENTS:
1. Convert ALL math expressions to proper LaTeX:
   - Integrals: \\int_0^1, \\iint, \\iiint
   - Fractions: \\frac{a}{b}
   - Square roots: \\sqrt{x}
   - Powers: x^{2}, e^{x}
   - Greek letters: \\alpha, \\beta, \\theta
   - Partial derivatives: \\frac{\\partial f}{\\partial x}
   - Limits: \\lim_{x \\to 0}

2. Wrap inline math in $...$ and display math in $$...$$

3. Remove garbage text:
   - Printing instructions ("For your examination...")
   - Page numbers, headers, footers
   - ".T True .F False" formatting artifacts

4. Preserve the original meaning exactly - do not solve or explain

5. Detect SPECIFIC topics from this list (use snake_case IDs):
   - Limits: limit_definition, squeeze_theorem, continuity, lhopitals_rule
   - Derivatives: power_rule, product_rule, chain_rule, implicit_differentiation, related_rates
   - Optimization: critical_points, absolute_extrema, lagrange_multipliers, constrained_optimization
   - Integration: u_substitution, integration_by_parts, partial_fractions, improper_integrals
   - Applications: area_between_curves, volume_disk_method, volume_shell_method, arc_length
   - Series: taylor_series, power_series, ratio_test, geometric_series
   - Multivariable: partial_derivatives, gradient, double_integrals_rectangular, double_integrals_polar
   - Vector Calc: line_integrals_vector, greens_theorem, stokes_theorem, divergence_theorem

OUTPUT FORMAT (strict JSON, no explanation):
{
  "questions": [
    {
      "id": "Q1",
      "text": "Evaluate $\\\\int_0^1 \\\\sqrt{x+y^2} \\\\, dx$",
      "topics": ["double_integrals_rectangular"],
      "difficulty": "medium",
      "is_true_false": false
    }
  ]
}

RAW TEXT:
'''


def _get_parsing_llm():
    """Get LLM for PDF parsing. Uses DeepSeek (cheaper) for batch processing."""
    try:
        from claire_agent import get_secret

        # Try DeepSeek first (cheaper for batch processing)
        deepseek_key = get_secret("DEEPSEEK_API_KEY")
        if deepseek_key:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                temperature=0,  # Deterministic output
                max_tokens=4096,
            )

        # Fallback to Claude if no DeepSeek key
        anthropic_key = get_secret("ANTHROPIC_API_KEY")
        if anthropic_key:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=anthropic_key,
                temperature=0,
                max_tokens=4096,
            )

    except Exception as e:
        print(f"[_get_parsing_llm] Error: {e}")

    return None


def parse_questions_with_llm(raw_text: str, source: str) -> list[Question]:
    """
    Parse raw PDF text into structured questions using LLM.

    This is called ONCE at upload time, NOT at display time.
    Uses DeepSeek (cheaper) for batch processing.
    """
    import json

    if not raw_text or len(raw_text.strip()) < 50:
        return []

    llm = _get_parsing_llm()
    if not llm:
        print("[parse_questions_with_llm] No LLM available, falling back to regex")
        return _extract_questions_regex(raw_text, source)

    # Truncate if too long
    max_chars = 12000
    if len(raw_text) > max_chars:
        raw_text = raw_text[:max_chars] + "\n\n[...truncated...]"

    prompt = PARSE_PROMPT + raw_text

    try:
        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # Extract JSON from response
        parsed = _extract_json(response_text)

        if not parsed or "questions" not in parsed:
            print("[parse_questions_with_llm] Invalid JSON response, falling back to regex")
            return _extract_questions_regex(raw_text, source)

        # Convert to Question objects
        questions = []
        for i, q_data in enumerate(parsed["questions"]):
            q_text = q_data.get("text", "")
            if not q_text or len(q_text) < 10:
                continue

            # Handle both old format (topic) and new format (topics)
            topics = q_data.get("topics", [])
            if not topics and q_data.get("topic"):
                topics = [q_data.get("topic")]

            # Get legacy pattern from first topic
            pattern = _topics_to_pattern(topics) if topics else "derivatives"

            questions.append(Question(
                id=q_data.get("id", f"Q{i+1}"),
                text=q_text,
                source=source,
                pattern=pattern,
                problem_id=q_data.get("id", f"Problem {i+1}"),
                difficulty=q_data.get("difficulty", "medium"),
                topics=topics,
            ))

        if questions:
            print(f"[parse_questions_with_llm] Parsed {len(questions)} questions from {source}")
            return questions

    except Exception as e:
        print(f"[parse_questions_with_llm] Error: {e}")

    # Fallback to regex parsing
    return _extract_questions_regex(raw_text, source)


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response."""
    import json

    # Try to find JSON block
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try raw JSON
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def _topics_to_pattern(topics: list[str]) -> str:
    """Convert fine-grained topics to legacy coarse pattern."""
    if not topics:
        return "derivatives"

    # Topic ID to legacy pattern mapping
    TOPIC_TO_PATTERN = {
        # Integration
        "u_substitution": "integration",
        "integration_by_parts": "integration",
        "partial_fractions": "integration",
        "trigonometric_integrals": "integration",
        "trigonometric_substitution": "integration",
        "improper_integrals": "integration",
        "double_integrals_rectangular": "integration",
        "double_integrals_polar": "integration",
        "triple_integrals_rectangular": "integration",
        "triple_integrals_cylindrical": "integration",
        "triple_integrals_spherical": "integration",
        "antiderivatives": "integration",
        "indefinite_integrals": "integration",

        # Optimization
        "lagrange_multipliers": "constrained_optimization",
        "constrained_optimization": "constrained_optimization",
        "critical_points": "optimization",
        "critical_points_multivariable": "optimization",
        "absolute_extrema": "optimization",
        "absolute_extrema_multivariable": "optimization",
        "optimization_word_problems": "optimization",

        # Related Rates
        "related_rates": "related_rates",

        # Limits
        "limit_definition": "limits",
        "one_sided_limits": "limits",
        "infinite_limits": "limits",
        "squeeze_theorem": "limits",
        "lhopitals_rule": "limits",
        "continuity": "limits",

        # Derivatives (default for most derivative topics)
        "power_rule": "derivatives",
        "product_rule": "derivatives",
        "quotient_rule": "derivatives",
        "chain_rule": "derivatives",
        "implicit_differentiation": "derivatives",
        "partial_derivatives": "derivatives",
        "gradient": "derivatives",
        "directional_derivative": "derivatives",
    }

    # Check first topic
    first_topic = topics[0].lower().replace(" ", "_").replace("-", "_")

    if first_topic in TOPIC_TO_PATTERN:
        return TOPIC_TO_PATTERN[first_topic]

    # Keyword-based fallback
    for topic in topics:
        topic_lower = topic.lower()
        if "integr" in topic_lower:
            return "integration"
        if "lagrange" in topic_lower or "constrain" in topic_lower:
            return "constrained_optimization"
        if "optim" in topic_lower or "extrema" in topic_lower:
            return "optimization"
        if "rate" in topic_lower:
            return "related_rates"
        if "limit" in topic_lower:
            return "limits"

    return "derivatives"


def _topic_to_pattern(topic: str) -> str:
    """Convert single topic name to pattern (backwards compat)."""
    return _topics_to_pattern([topic])


# ============================================================
# REGEX FALLBACK (when LLM is unavailable)
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


def _extract_questions_regex(text: str, source: str) -> list[Question]:
    """
    Fallback: Extract questions using regex patterns.
    Used when LLM is unavailable.
    """
    questions = []
    seen_texts = set()

    for pattern_idx, pattern in enumerate(QUESTION_PATTERNS):
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        for match in matches:
            problem_id = ""
            if isinstance(match, tuple) and len(match) >= 2:
                identifier = match[0]
                q_text = match[-1].strip()

                if pattern_idx == 0:
                    problem_id = f"Problem {identifier}"
                elif pattern_idx == 1:
                    problem_id = f"Q{identifier}"
                elif pattern_idx == 2:
                    problem_id = f"({identifier})"
            else:
                q_text = match.strip() if isinstance(match, str) else str(match)

            q_text = re.sub(r'\s+', ' ', q_text).strip()

            if len(q_text) < 20 or q_text in seen_texts:
                continue
            if not is_calculus_question(q_text):
                continue

            seen_texts.add(q_text)
            calc_pattern = detect_pattern(q_text)

            # Apply basic formatting (not LLM)
            formatted_text = format_math_text(q_text)

            questions.append(Question(
                id="",
                text=formatted_text,
                source=source,
                pattern=calc_pattern,
                problem_id=problem_id,
            ))

    # Fallback: split by paragraphs
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
            formatted_text = format_math_text(para)

            questions.append(Question(
                id="",
                text=formatted_text,
                source=source,
                pattern=calc_pattern,
            ))

    return questions


def extract_questions_from_text(text: str, source: str) -> list[Question]:
    """
    Extract questions from text - uses LLM parsing for clean LaTeX output.

    This is called at UPLOAD TIME, not display time.
    """
    # Use LLM parsing (with DeepSeek for cost efficiency)
    return parse_questions_with_llm(text, source)


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
