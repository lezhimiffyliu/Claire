"""
Past Paper → Structured Exam Parser

Converts uploaded exam PDFs into structured JSON for exam simulation.
NOT about solving questions - about structuring them.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Optional

# ────────────────────────────────────────────────────────────
# Data structures
# ────────────────────────────────────────────────────────────

@dataclass
class ExamMeta:
    title: str = ""
    total_points: int = 100
    estimated_duration_minutes: int = 60
    topics_overview: list[str] = field(default_factory=list)


@dataclass
class QuestionSubpart:
    label: str  # e.g., "a", "b"
    text: str


@dataclass
class ParsedQuestion:
    question_id: str  # e.g., "Q1"
    question_text: str
    topic: str
    difficulty: str  # easy, medium, hard
    points: int
    concepts: list[str] = field(default_factory=list)
    subparts: list[QuestionSubpart] = field(default_factory=list)


@dataclass
class ParsedExam:
    meta: ExamMeta
    questions: list[ParsedQuestion]
    raw_text: str = ""  # Keep original for reference
    parse_success: bool = True
    error_message: str = ""


# ────────────────────────────────────────────────────────────
# PDF Text Extraction
# ────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except Exception as e:
        print(f"[exam_parser] PDF extraction error: {e}")
        return ""


def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract text from uploaded file (PDF or text)."""
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    else:
        # Assume text file
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")


# ────────────────────────────────────────────────────────────
# LLM Parsing
# ────────────────────────────────────────────────────────────

PARSE_PROMPT = '''You are given the text content of a past exam paper.

Your job is NOT to explain or solve the problems.

Your job is to convert the exam into a structured format for an exam simulation system.

---

OUTPUT FORMAT (strict JSON):

{
  "exam_meta": {
    "title": "...",
    "total_points": number,
    "estimated_duration_minutes": number,
    "topics_overview": ["...", "..."]
  },
  "questions": [
    {
      "question_id": "Q1",
      "question_text": "...",
      "topic": "...",
      "difficulty": "easy | medium | hard",
      "points": number,
      "concepts": ["...", "..."],
      "subparts": [
        {
          "label": "a",
          "text": "..."
        }
      ]
    }
  ]
}

---

INSTRUCTIONS:

1. Split the exam into individual questions
2. Group subparts under each question
3. Remove noise (headers, instructions, page numbers)
4. Infer topic, difficulty, and points
5. Extract key concepts
6. Fill exam_meta fields

---

IMPORTANT:

- DO NOT solve problems
- DO NOT explain
- ONLY output valid JSON

---

INPUT:
'''


def parse_exam_to_json(raw_text: str, llm=None) -> dict:
    """
    Call LLM to parse exam text into structured JSON.

    Args:
        raw_text: Extracted text from exam PDF/file
        llm: LangChain LLM instance (if None, will try to create one)

    Returns:
        Parsed JSON dict or empty dict on failure
    """
    if not raw_text.strip():
        return {}

    # Truncate if too long (avoid token limits)
    max_chars = 15000
    if len(raw_text) > max_chars:
        raw_text = raw_text[:max_chars] + "\n\n[...truncated...]"

    # Build prompt
    full_prompt = PARSE_PROMPT + raw_text

    # Get or create LLM
    if llm is None:
        llm = _get_llm()
        if llm is None:
            return {}

    try:
        # Call LLM
        response = llm.invoke(full_prompt)

        # Extract content
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)

        # Parse JSON from response
        return _extract_json(response_text)

    except Exception as e:
        print(f"[exam_parser] LLM parsing error: {e}")
        return {}


def _get_llm():
    """Get LLM instance using existing setup."""
    try:
        from claire_agent_old import get_secret
        api_key = get_secret("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0,
            max_tokens=4096,
        )
    except Exception as e:
        print(f"[exam_parser] Failed to get LLM: {e}")
        return None


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response text."""
    # Try to find JSON block
    # Look for ```json ... ``` or just { ... }

    # Try markdown code block first
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object
    # Find first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


# ────────────────────────────────────────────────────────────
# Validation & Conversion
# ────────────────────────────────────────────────────────────

def validate_and_convert(parsed_json: dict, raw_text: str = "") -> ParsedExam:
    """
    Validate parsed JSON and convert to ParsedExam object.
    Returns ParsedExam with parse_success=False if invalid.
    """
    if not parsed_json:
        return ParsedExam(
            meta=ExamMeta(),
            questions=[],
            raw_text=raw_text,
            parse_success=False,
            error_message="Failed to parse exam structure"
        )

    try:
        # Parse meta
        meta_json = parsed_json.get("exam_meta", {})
        meta = ExamMeta(
            title=meta_json.get("title", "Uploaded Exam"),
            total_points=meta_json.get("total_points", 100),
            estimated_duration_minutes=meta_json.get("estimated_duration_minutes", 60),
            topics_overview=meta_json.get("topics_overview", []),
        )

        # Parse questions
        questions = []
        for q_json in parsed_json.get("questions", []):
            # Parse subparts
            subparts = []
            for sp in q_json.get("subparts", []):
                subparts.append(QuestionSubpart(
                    label=sp.get("label", ""),
                    text=sp.get("text", ""),
                ))

            questions.append(ParsedQuestion(
                question_id=q_json.get("question_id", f"Q{len(questions)+1}"),
                question_text=q_json.get("question_text", ""),
                topic=q_json.get("topic", "general"),
                difficulty=q_json.get("difficulty", "medium"),
                points=q_json.get("points", 20),
                concepts=q_json.get("concepts", []),
                subparts=subparts,
            ))

        if not questions:
            return ParsedExam(
                meta=meta,
                questions=[],
                raw_text=raw_text,
                parse_success=False,
                error_message="No questions found in exam"
            )

        return ParsedExam(
            meta=meta,
            questions=questions,
            raw_text=raw_text,
            parse_success=True,
        )

    except Exception as e:
        return ParsedExam(
            meta=ExamMeta(),
            questions=[],
            raw_text=raw_text,
            parse_success=False,
            error_message=f"Validation error: {str(e)}"
        )


# ────────────────────────────────────────────────────────────
# Main Pipeline
# ────────────────────────────────────────────────────────────

def parse_exam_file(filename: str, file_bytes: bytes, llm=None) -> ParsedExam:
    """
    Main entry point: file → text → LLM → structured exam.

    Args:
        filename: Original filename
        file_bytes: File content as bytes
        llm: Optional LLM instance

    Returns:
        ParsedExam object
    """
    # Step 1: Extract text
    raw_text = extract_text_from_file(filename, file_bytes)
    if not raw_text.strip():
        return ParsedExam(
            meta=ExamMeta(title=filename),
            questions=[],
            raw_text="",
            parse_success=False,
            error_message="Could not extract text from file"
        )

    # Step 2: Call LLM to parse
    parsed_json = parse_exam_to_json(raw_text, llm)

    # Step 3: Retry once if failed
    if not parsed_json:
        print("[exam_parser] First parse failed, retrying...")
        parsed_json = parse_exam_to_json(raw_text, llm)

    # Step 4: Validate and convert
    return validate_and_convert(parsed_json, raw_text)


# ────────────────────────────────────────────────────────────
# Convert to Exam Mode format
# ────────────────────────────────────────────────────────────

def parsed_exam_to_exam_questions(parsed: ParsedExam) -> list:
    """
    Convert ParsedExam to exam_mode.ExamQuestion list.
    """
    from exam_mode import ExamQuestion

    questions = []
    for pq in parsed.questions:
        # Combine main text with subparts
        full_text = pq.question_text
        if pq.subparts:
            full_text += "\n\n"
            for sp in pq.subparts:
                full_text += f"({sp.label}) {sp.text}\n"

        questions.append(ExamQuestion(
            id=pq.question_id,
            text=full_text.strip(),
            topic=pq.topic.lower().replace(" ", "_"),
            points=pq.points,
            difficulty=pq.difficulty,
            source=parsed.meta.title,
            correct_answer="",  # Not solving
        ))

    return questions
