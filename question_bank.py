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
# EXTRACTION DEBUG STATS
# ============================================================

# Module-level stats for debugging extraction issues
_extraction_stats = {}


def _reset_extraction_stats(filename: str):
    """Reset stats for a new file extraction."""
    _extraction_stats.clear()
    _extraction_stats.update({
        "file": filename,
        "pages": 0,
        "raw_text_length": 0,
        # Main question segmentation (new pre-processing step)
        "main_questions_detected": 0,
        "main_question_numbers": [],
        "used_main_segmentation": False,
        # Pattern matching stats
        "pattern_matches": {"pattern0": 0, "pattern1": 0, "pattern2": 0},
        "pattern_match_ids": {"pattern0": [], "pattern1": [], "pattern2": []},
        # Filtering stats
        "filtered_too_short": 0,
        "filtered_duplicate": 0,
        "filtered_not_calculus": 0,
        "fallback_paragraph_used": False,
        # Final results
        "questions_final": 0,
        "question_ids_final": [],
    })


def _print_extraction_stats():
    """Print extraction stats summary."""
    if not _extraction_stats:
        return

    stats = _extraction_stats
    total_matches = sum(stats["pattern_matches"].values())
    total_filtered = (
        stats["filtered_too_short"] +
        stats["filtered_duplicate"] +
        stats["filtered_not_calculus"]
    )

    print("\n" + "=" * 60)
    print("[EXTRACTION DEBUG]")
    print("=" * 60)
    print(f"  file:                {stats['file']}")
    print(f"  pages:               {stats['pages']}")
    print(f"  raw_text_length:     {stats['raw_text_length']}")
    print("-" * 40)
    print("  [Main Question Segmentation]")
    print(f"  main_q_detected:     {stats['main_questions_detected']}")
    print(f"  main_q_numbers:      {stats['main_question_numbers']}")
    print(f"  used_main_segment:   {stats['used_main_segmentation']}")
    print("-" * 40)
    print("  [Pattern Matching - only if main segmentation failed]")
    print(f"  pattern0 matches:    {stats['pattern_matches']['pattern0']}  (Problem/Question N.)")
    print(f"    → IDs:             {stats['pattern_match_ids']['pattern0']}")
    print(f"  pattern1 matches:    {stats['pattern_matches']['pattern1']}  (N. + keyword)")
    print(f"    → IDs:             {stats['pattern_match_ids']['pattern1']}")
    print(f"  pattern2 matches:    {stats['pattern_matches']['pattern2']}  ((a)(b)(c) subparts)")
    print(f"    → IDs:             {stats['pattern_match_ids']['pattern2']}")
    print("-" * 40)
    print("  [Filtering]")
    print(f"  filtered_too_short:  {stats['filtered_too_short']}")
    print(f"  filtered_duplicate:  {stats['filtered_duplicate']}")
    print(f"  filtered_not_calc:   {stats['filtered_not_calculus']}")
    print(f"  total_filtered:      {total_filtered}")
    print(f"  fallback_paragraph:  {stats['fallback_paragraph_used']}")
    print("-" * 40)
    print("  [Final Result]")
    print(f"  questions_final:     {stats['questions_final']}")
    print(f"  question_ids_final:  {stats['question_ids_final']}")
    print("=" * 60 + "\n")


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
    question_type: str = "open"      # tf, mcq, or open
    correct_answer: Optional[str] = None  # For tf/mcq: "True", "B", etc.
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
        """Format a readable source citation like 'MATH 125 Final AU24 Problem 2'."""
        import re
        name = Path(self.source).stem  # Remove extension

        # Parse common exam filename patterns like "125finalA24", "math125_midterm1_sp23"
        # Extract: course number, exam type, term/year
        parts = []

        # Always prefix with MATH if it looks like a course number
        course_match = re.search(r'(\d{3})', name)
        if course_match:
            parts.append(f"MATH {course_match.group(1)}")

        # Detect exam type
        name_lower = name.lower()
        if 'final' in name_lower:
            parts.append("Final")
        elif 'midterm' in name_lower or 'mid' in name_lower:
            mid_match = re.search(r'midterm\s*(\d)', name_lower) or re.search(r'mid\s*(\d)', name_lower)
            if mid_match:
                parts.append(f"Midterm {mid_match.group(1)}")
            else:
                parts.append("Midterm")
        elif 'quiz' in name_lower:
            quiz_match = re.search(r'quiz\s*(\d)', name_lower)
            if quiz_match:
                parts.append(f"Quiz {quiz_match.group(1)}")
            else:
                parts.append("Quiz")

        # Detect term/year (e.g., A24, AU24, SP23, F22, W23)
        term_match = re.search(r'([ASWF]U?)\s*(\d{2})', name, re.IGNORECASE)
        if term_match:
            term_code = term_match.group(1).upper()
            year = term_match.group(2)
            term_map = {'A': 'AU', 'AU': 'AU', 'S': 'SP', 'SP': 'SP', 'W': 'WI', 'WI': 'WI', 'F': 'FA', 'FA': 'FA'}
            term = term_map.get(term_code, term_code)
            parts.append(f"{term}{year}")

        # Add problem identifier
        if self.problem_id:
            parts.append(self.problem_id)

        # Fallback if nothing matched
        if not parts:
            name = name.replace("_", " ").replace("-", " ")
            if self.problem_id:
                return f"{name} {self.problem_id}"
            return name

        return " ".join(parts)

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

def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, list[dict]]:
    """
    Extract text from PDF bytes using PyMuPDF.

    Returns:
        (full_text, page_info_list)
        page_info_list: [{"page_num": 1, "text": "...", "has_questions": bool}, ...]
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_info = []

    # Pattern to detect question starts: "1." or "1)" at line start
    question_pattern = re.compile(r'^\s*(\d{1,2})\.\s*\(', re.MULTILINE)

    for i, page in enumerate(doc):
        text = page.get_text()

        # Detect if this page has question patterns
        matches = question_pattern.findall(text)
        has_questions = len(matches) > 0

        # Filter out cover pages and mostly empty pages
        is_cover = (
            i == 0 and
            ('name:' in text.lower() or 'exam' in text.lower()) and
            len(matches) == 0
        )
        is_empty = len(text.strip()) < 100

        page_info.append({
            "page_num": i + 1,
            "text": text,
            "has_questions": has_questions,
            "question_nums": [int(m) for m in matches],
            "is_cover": is_cover,
            "is_empty": is_empty,
        })

        print(f"[PDF DEBUG] Page {i+1}: {len(text)} chars, questions={matches}, cover={is_cover}, empty={is_empty}")

    # Track stats
    if _extraction_stats:
        _extraction_stats["pages"] = len(doc)

    doc.close()

    # Build full text from non-cover, non-empty pages
    valid_pages = [p for p in page_info if not p["is_cover"] and not p["is_empty"]]
    full_text = "\n\n".join(p["text"] for p in valid_pages)

    if _extraction_stats:
        _extraction_stats["raw_text_length"] = len(full_text)
        _extraction_stats["valid_pages"] = len(valid_pages)

    return full_text, page_info


def extract_text_from_file(file_bytes: bytes, filename: str) -> tuple[str, list[dict]]:
    """
    Extract text from file based on extension.

    Returns:
        (text, page_info) - page_info is empty list for non-PDF files
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in [".txt", ".md", ".text", ".markdown"]:
        text = file_bytes.decode("utf-8", errors="ignore")
        return text, []
    else:
        # Try as text
        text = file_bytes.decode("utf-8", errors="ignore")
        return text, []


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

6. Classify question_type as ONE of:
   - "tf": True/False question
   - "mcq": Multiple choice with (A)(B)(C)(D) or similar options
   - "open": Open-ended problem (computation, proof, multi-part with a) b) c), etc.)

7. For "tf" and "mcq" questions, determine the correct answer:
   - "correct_answer": the correct choice (e.g., "True", "B", "2x")
   - If you cannot determine the correct answer reliably, set to null

OUTPUT FORMAT (strict JSON, no explanation):
{
  "questions": [
    {
      "id": "Q1",
      "text": "The derivative of $\\\\sin(x)$ is $\\\\cos(x)$.",
      "topics": ["derivatives"],
      "difficulty": "easy",
      "question_type": "tf",
      "correct_answer": "True"
    },
    {
      "id": "Q2",
      "text": "What is $\\\\frac{d}{dx}[x^2]$? (A) $x$ (B) $2x$ (C) $2$ (D) $x^2$",
      "topics": ["derivatives"],
      "difficulty": "easy",
      "question_type": "mcq",
      "correct_answer": "B"
    }
  ]
}

RAW TEXT:
'''


def _get_parsing_llm():
    """Get LLM for PDF parsing. Uses DeepSeek (cheaper) for batch processing."""
    try:
        from claire_agent_old import get_secret

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

            # Get question type (tf, mcq, open)
            question_type = q_data.get("question_type", "open")
            if question_type not in ("tf", "mcq", "open"):
                question_type = "open"

            # Get correct answer for tf/mcq
            correct_answer = q_data.get("correct_answer")

            questions.append(Question(
                id=q_data.get("id", f"Q{i+1}"),
                text=q_text,
                source=source,
                pattern=pattern,
                problem_id=q_data.get("id", f"Problem {i+1}"),
                difficulty=q_data.get("difficulty", "medium"),
                question_type=question_type,
                correct_answer=correct_answer,
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


# ============================================================
# PER-QUESTION LLM REFINEMENT
# ============================================================

def _refine_question_with_llm(question: Question) -> Question:
    """
    Refine a single main question block with LLM.

    - Cleans up math notation (proper LaTeX)
    - Extracts subparts (a), (b), (c) if present
    - Mutates and returns the same Question object

    On failure: silently returns original question unchanged.
    """
    llm = _get_parsing_llm()
    if not llm:
        return question

    prompt = f"""STRICT TRANSCRIPTION: Convert math symbols to LaTeX. Do NOT modify content.

YOU ARE A TRANSCRIBER, NOT A WRITER.

ALLOWED transformations (ONLY these):
- Z → $\\int$  (corrupted integral symbol)
- x2 → $x^2$  (missing superscript)
- √ → $\\sqrt{{}}$
- lim → $\\lim$
- sin, cos, ln → $\\sin$, $\\cos$, $\\ln$

FORBIDDEN (will cause rejection):
- Adding subparts (a), (b), (c) that don't exist in input
- Changing what the problem asks
- Guessing missing information
- Reordering or restructuring
- Adding "Find", "Evaluate", etc. if not in original

If input has NO (a), (b), (c) → output must have NO (a), (b), (c)
If something is unclear → keep it exactly as-is, do NOT guess

Input:
{question.text}

Output JSON (subparts array ONLY if they exist in input):
{{"cleaned_text": "...", "subparts": []}}"""

    try:
        original_text = question.text
        original_len = len(original_text)

        # DEBUG: Show input to LLM
        print(f"\n{'='*60}")
        print(f"[refine DEBUG] {question.problem_id} - INPUT:")
        print(f"{'='*60}")
        print(original_text[:500] + ("..." if len(original_text) > 500 else ""))
        print(f"{'='*60}\n")

        response = llm.invoke(prompt)

        # DEBUG: Show raw LLM response
        print(f"\n{'='*60}")
        print(f"[refine DEBUG] {question.problem_id} - LLM RAW RESPONSE:")
        print(f"{'='*60}")
        print(response.content[:800] + ("..." if len(response.content) > 800 else ""))
        print(f"{'='*60}\n")

        data = _extract_json(response.content)

        if data and "cleaned_text" in data:
            cleaned = data["cleaned_text"]
            cleaned_len = len(cleaned)

            # DEBUG: Show cleaned text
            print(f"\n{'='*60}")
            print(f"[refine DEBUG] {question.problem_id} - CLEANED TEXT:")
            print(f"{'='*60}")
            print(cleaned[:500] + ("..." if len(cleaned) > 500 else ""))
            print(f"{'='*60}\n")

            # Safety check: reject if output lost too much content (< 50% of original)
            if cleaned_len < original_len * 0.5:
                print(f"[refine] ✗ {question.problem_id} - rejected: output too short ({cleaned_len} < {original_len * 0.5:.0f})")
                question.metadata["refined"] = False
                return question

            # Safety check: subparts must match exactly
            orig_subparts = set(re.findall(r'\([a-z]\)', original_text, re.IGNORECASE))
            new_subparts = set(re.findall(r'\([a-z]\)', cleaned, re.IGNORECASE))

            # CRITICAL: If LLM added subparts that don't exist in original, reject
            invented_subparts = new_subparts - orig_subparts
            if invented_subparts:
                print(f"[refine] ✗ {question.problem_id} - rejected: LLM invented subparts {invented_subparts}")
                question.metadata["refined"] = False
                return question

            # If original has subparts but output lost some, reject
            if orig_subparts and len(new_subparts) < len(orig_subparts):
                print(f"[refine] ✗ {question.problem_id} - rejected: lost subparts ({new_subparts} < {orig_subparts})")
                question.metadata["refined"] = False
                return question

            question.text = cleaned
            question.metadata["subparts"] = data.get("subparts", [])
            question.metadata["refined"] = True
            print(f"[refine] ✓ {question.problem_id} refined, {len(question.metadata.get('subparts', []))} subparts")
        else:
            print(f"[refine] ✗ {question.problem_id} - no valid JSON returned")
            print(f"[refine DEBUG] Extracted data: {data}")

    except Exception as e:
        print(f"[refine] ✗ {question.problem_id} - error: {e}")
        import traceback
        traceback.print_exc()

    return question


def start_background_refinement(questions: list[Question]) -> None:
    """
    Start background thread to refine all questions.

    Non-blocking - returns immediately.
    Questions are mutated in-place as refinement completes.
    """
    import threading

    def refine_all():
        print(f"[refine] Starting background refinement for {len(questions)} questions...")
        for i, q in enumerate(questions, 1):
            print(f"[refine] Processing {i}/{len(questions)}: {q.problem_id}")
            _refine_question_with_llm(q)
        print(f"[refine] Background refinement complete.")

    thread = threading.Thread(target=refine_all, daemon=True)
    thread.start()


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
# MAIN QUESTION SEGMENTATION (pre-processing step)
# ============================================================

def _segment_main_questions(text: str, page_info: list[dict] = None) -> list[tuple[str, str]]:
    """
    Segment raw text into main question blocks.

    Strategy: Find ALL "N. (" patterns, then find the longest consecutive sequence.

    Returns list of (question_id, block_text) tuples.
    """
    # Pattern: "N. (" at line start - standard exam format
    main_q_pattern = re.compile(
        r'(?:^|\n)\s{0,2}(\d{1,2})\.\s*\(',
        re.MULTILINE
    )

    matches = list(main_q_pattern.finditer(text))

    print(f"[_segment DEBUG] Found {len(matches)} raw matches")
    for m in matches:
        ctx = text[m.start():m.start()+60].replace('\n', ' ')
        print(f"  - Q{m.group(1)} @ {m.start()}: {ctx!r}")

    if len(matches) < 2:
        print(f"[_segment DEBUG] Too few matches, skipping segmentation")
        return []

    # Build list of (question_num, match_obj)
    numbered = [(int(m.group(1)), m) for m in matches]

    # Find the longest consecutive sequence
    # Try starting from each position
    best_sequence = []
    for start_idx in range(len(numbered)):
        sequence = [numbered[start_idx]]
        expected_next = numbered[start_idx][0] + 1

        for j in range(start_idx + 1, len(numbered)):
            if numbered[j][0] == expected_next:
                sequence.append(numbered[j])
                expected_next += 1

        if len(sequence) > len(best_sequence):
            best_sequence = sequence

    print(f"[_segment DEBUG] Best sequence: {[q[0] for q in best_sequence]}")

    if len(best_sequence) < 2:
        print(f"[_segment DEBUG] No good sequence found")
        return []

    # Extract blocks from best sequence
    valid_matches = []
    for i, (q_num, m) in enumerate(best_sequence):
        start_pos = m.start()

        # End at next question in sequence, or end of text
        if i + 1 < len(best_sequence):
            end_pos = best_sequence[i + 1][1].start()
        else:
            end_pos = len(text)

        block_text = text[start_pos:end_pos].strip()

        # Basic validation
        if len(block_text) < 30:
            print(f"[_segment DEBUG] Q{q_num} too short, skipping")
            continue

        valid_matches.append((str(q_num), block_text, start_pos, end_pos))

    print(f"[_segment DEBUG] Extracted {len(valid_matches)} questions")

    # Must have at least 2 main questions to be confident this is structured
    if len(valid_matches) < 2:
        print(f"[_segment DEBUG] Only {len(valid_matches)} questions found, falling back")
        return []

    # Track stats
    if _extraction_stats:
        _extraction_stats["main_questions_detected"] = len(valid_matches)
        _extraction_stats["main_question_numbers"] = [q[0] for q in valid_matches]

    # Return (question_id, block_text) pairs
    return [(f"Problem {q[0]}", q[1]) for q in valid_matches]


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


def _detect_has_figure(text: str) -> bool:
    """
    Detect if question references a figure, graph, or diagram.
    Returns True if the question likely requires visual content.
    """
    text_lower = text.lower()
    # Common figure reference patterns
    figure_patterns = [
        "figure", "fig.", "fig ", "graph", "diagram", "sketch",
        "shown above", "shown below", "see the", "as shown",
        "picture", "illustration", "plot", "curve shown",
        "region shown", "shaded region", "the following graph",
    ]
    return any(pattern in text_lower for pattern in figure_patterns)


def _detect_corrupted_math(text: str) -> bool:
    """
    Detect if text has corrupted math symbols from PDF extraction.

    Common corruptions:
    - ∫ becomes Z or empty
    - √ becomes √ or v or empty
    - Fractions split across lines
    - Exponents lost
    """
    # Patterns that indicate corrupted integral
    # "dx" or "dy" alone without ∫ suggests integral was lost
    has_dx_dy = bool(re.search(r'\bdx\b|\bdy\b', text, re.IGNORECASE))
    has_integral_symbol = '∫' in text or '\\int' in text

    # "Z" at start of expression often means corrupted ∫
    has_suspicious_z = bool(re.search(r'\bZ\s*[a-z\d(]', text))

    # Fragmented math: isolated operators or symbols
    has_fragments = bool(re.search(r'\n\s*[+\-*/√]\s*\n', text))

    # "evaluate" + "integral" but no ∫ symbol
    mentions_integral = 'integral' in text.lower()

    is_corrupted = (
        (has_dx_dy and not has_integral_symbol and mentions_integral) or
        has_suspicious_z or
        has_fragments
    )

    if is_corrupted:
        print(f"[CORRUPTED MATH] Detected: dx/dy={has_dx_dy}, ∫={has_integral_symbol}, Z={has_suspicious_z}, fragments={has_fragments}")

    return is_corrupted


def _extract_questions_regex(text: str, source: str, page_info: list[dict] = None) -> list[Question]:
    """
    Extract questions using regex patterns.

    Flow:
    1. Try main question segmentation (structured exams)
    2. If that fails, fall back to pattern matching
    """
    questions = []
    seen_texts = set()

    # ============================================================
    # STEP 1: Try main question segmentation first
    # ============================================================
    main_questions = _segment_main_questions(text, page_info)

    # DEBUG: Show what was extracted from PDF
    if main_questions:
        print(f"\n{'#'*60}")
        print(f"[PDF EXTRACTION DEBUG] Found {len(main_questions)} main questions:")
        print(f"{'#'*60}")
        for i, (pid, block) in enumerate(main_questions):
            print(f"\n--- {pid} (raw block, first 400 chars) ---")
            print(block[:400] + ("..." if len(block) > 400 else ""))
        print(f"{'#'*60}\n")

    if main_questions:
        if _extraction_stats:
            _extraction_stats["used_main_segmentation"] = True

        for problem_id, block_text in main_questions:
            # Normalize whitespace
            q_text = re.sub(r'\s+', ' ', block_text).strip()

            if len(q_text) < 20:
                if _extraction_stats:
                    _extraction_stats["filtered_too_short"] += 1
                continue

            if q_text in seen_texts:
                if _extraction_stats:
                    _extraction_stats["filtered_duplicate"] += 1
                continue

            # For structured main questions, use relaxed calculus check:
            # Either has calculus keywords OR is long enough to be a real problem
            is_calc = is_calculus_question(q_text)
            is_substantial = len(q_text) > 100  # Long enough to likely be a real question

            if not is_calc and not is_substantial:
                if _extraction_stats:
                    _extraction_stats["filtered_not_calculus"] += 1
                continue

            seen_texts.add(q_text)
            calc_pattern = detect_pattern(q_text)
            formatted_text = format_math_text(q_text)
            has_figure = _detect_has_figure(q_text)
            needs_vision = _detect_corrupted_math(q_text)

            metadata = {}
            if has_figure:
                metadata["has_figure"] = True
            if needs_vision:
                metadata["needs_vision"] = True
                print(f"[EXTRACT] {problem_id} marked for vision reconstruction")

            questions.append(Question(
                id="",
                text=formatted_text,
                source=source,
                pattern=calc_pattern,
                problem_id=problem_id,
                metadata=metadata,
            ))

        # If main segmentation found questions, we're done
        if questions:
            if _extraction_stats:
                _extraction_stats["questions_final"] = len(questions)
                _extraction_stats["question_ids_final"] = [q.problem_id for q in questions]

                # Add extraction quality warnings
                warnings = []
                pages = _extraction_stats.get("pages", 0)
                if pages >= 3 and len(questions) < 3:
                    warnings.append(f"Only {len(questions)} questions from {pages}-page document")

                q_nums = _extraction_stats.get("main_question_numbers", [])
                if q_nums:
                    expected = list(range(1, len(q_nums) + 1))
                    actual = [int(n) for n in q_nums if n.isdigit()]
                    if actual and actual != expected[:len(actual)]:
                        warnings.append(f"Non-sequential questions: {q_nums}")

                fig_count = sum(1 for q in questions if q.metadata.get("has_figure"))
                if fig_count > 0:
                    warnings.append(f"{fig_count} question(s) reference figures (may need visual context)")

                if warnings:
                    _extraction_stats["warnings"] = warnings

            return questions

    # ============================================================
    # STEP 2: Fall back to pattern matching
    # ============================================================
    for pattern_idx, pattern in enumerate(QUESTION_PATTERNS):
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        pattern_key = f"pattern{pattern_idx}"

        for match in matches:
            problem_id = ""
            identifier = ""
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

            # Track pattern match (before filtering)
            if _extraction_stats:
                _extraction_stats["pattern_matches"][pattern_key] += 1
                if identifier:
                    _extraction_stats["pattern_match_ids"][pattern_key].append(identifier)

            q_text = re.sub(r'\s+', ' ', q_text).strip()

            # Track filtering reasons
            if len(q_text) < 20:
                if _extraction_stats:
                    _extraction_stats["filtered_too_short"] += 1
                continue
            if q_text in seen_texts:
                if _extraction_stats:
                    _extraction_stats["filtered_duplicate"] += 1
                continue
            if not is_calculus_question(q_text):
                if _extraction_stats:
                    _extraction_stats["filtered_not_calculus"] += 1
                continue

            seen_texts.add(q_text)
            calc_pattern = detect_pattern(q_text)

            # Apply basic formatting (not LLM)
            formatted_text = format_math_text(q_text)
            has_figure = _detect_has_figure(q_text)

            questions.append(Question(
                id="",
                text=formatted_text,
                source=source,
                pattern=calc_pattern,
                problem_id=problem_id,
                metadata={"has_figure": has_figure} if has_figure else {},
            ))

    # Fallback: split by paragraphs
    if not questions:
        if _extraction_stats:
            _extraction_stats["fallback_paragraph_used"] = True

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
            has_figure = _detect_has_figure(para)

            questions.append(Question(
                id="",
                text=formatted_text,
                source=source,
                pattern=calc_pattern,
                metadata={"has_figure": has_figure} if has_figure else {},
            ))

    # Track final results
    if _extraction_stats:
        _extraction_stats["questions_final"] = len(questions)
        _extraction_stats["question_ids_final"] = [q.problem_id for q in questions if q.problem_id]

        # Extraction quality warnings
        warnings = []

        # Check 1: Very few questions from multi-page document
        pages = _extraction_stats.get("pages", 0)
        if pages >= 3 and len(questions) < 3:
            warnings.append(f"Only {len(questions)} questions from {pages}-page document")

        # Check 2: Non-sequential question numbers (gaps)
        if _extraction_stats.get("used_main_segmentation"):
            q_nums = _extraction_stats.get("main_question_numbers", [])
            if q_nums:
                expected = list(range(1, len(q_nums) + 1))
                actual = [int(n) for n in q_nums if n.isdigit()]
                if actual and actual != expected[:len(actual)]:
                    warnings.append(f"Non-sequential questions: {q_nums}")

        # Check 3: Figure references but no visual content warning
        fig_count = sum(1 for q in questions if q.metadata.get("has_figure"))
        if fig_count > 0:
            warnings.append(f"{fig_count} question(s) reference figures (may need visual context)")

        if warnings:
            _extraction_stats["warnings"] = warnings

    return questions


def extract_questions_from_text(text: str, source: str, page_info: list[dict] = None) -> list[Question]:
    """
    Extract questions from text - uses FAST regex parsing only.
    LLM cleaning happens in background, not here.
    """
    # Fast regex parsing only - no LLM wait
    return _extract_questions_regex(text, source, page_info)


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
        # Reset debug stats for this file
        _reset_extraction_stats(filename)

        try:
            # Extract text and page info
            text, page_info = extract_text_from_file(file_bytes, filename)

            # Extract questions (pass page_info for better segmentation)
            questions = extract_questions_from_text(text, filename, page_info)

            # Add to bank
            for q in questions:
                bank.add(q)

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            continue
        finally:
            # Always print debug stats
            _print_extraction_stats()

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
