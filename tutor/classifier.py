"""
Intent and Concept Classifier

Classifies student messages into:
- intent: what the student wants (hint, explanation, check, etc.)
- concept: what math concept is being discussed
- misconception: suspected error pattern (if any)

Uses Haiku for cheap, fast classification.
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from anthropic import Anthropic

# Haiku for cheap classification
CLASSIFIER_MODEL = "claude-haiku-4-5"


@dataclass
class Classification:
    """Result of intent/concept classification."""
    intent: str  # e.g., "ask_hint", "confused", "check_answer", "acknowledgment"
    concept: Optional[str]  # e.g., "partial_derivative", "chain_rule"
    misconception: Optional[str]  # e.g., "forgot_constant", "wrong_rule"
    confidence: float  # 0.0 - 1.0
    language: str  # "en" or "zh"
    requires_strategy: bool  # True if needs Opus-level reasoning
    raw_analysis: Dict[str, Any]  # Full analysis for debugging


# Intent categories
INTENTS = {
    "ask_hint": "Student wants a hint or nudge",
    "ask_explanation": "Student wants something explained",
    "check_answer": "Student wants their answer checked",
    "confused": "Student is confused or stuck",
    "acknowledgment": "Student acknowledges understanding",
    "ask_next_step": "Student wants to know what to do next",
    "give_up": "Student wants to see the answer",
    "ask_why": "Student asks why something is true",
    "attempt_answer": "Student is attempting an answer",
    "clarify_question": "Student is asking about the problem statement",
    "off_topic": "Message is not about the current problem",
}

# Concepts for calculus
CONCEPTS = [
    "derivative", "partial_derivative", "chain_rule", "product_rule", "quotient_rule",
    "integral", "definite_integral", "indefinite_integral", "u_substitution",
    "integration_by_parts", "limit", "continuity", "lhopital",
    "critical_point", "extrema", "optimization", "lagrange_multiplier",
    "taylor_series", "power_series", "convergence",
    "double_integral", "triple_integral", "polar_coordinates", "cylindrical_coordinates",
    "gradient", "divergence", "curl", "line_integral", "surface_integral",
    "differential_equation", "separable_de", "linear_de",
]

# Common misconceptions
MISCONCEPTIONS = [
    "forgot_constant_rule",  # Treating variable as constant in partial derivative
    "wrong_chain_rule",  # Forgot inner derivative
    "wrong_product_rule",  # f'g + fg' confusion
    "integration_bounds_error",  # Wrong limits
    "algebra_error",  # Simple arithmetic/algebra mistake
    "sign_error",  # Positive/negative confusion
    "conceptual_misunderstanding",  # Fundamental concept wrong
    "notation_confusion",  # Confused by notation
    "order_of_operations",  # Wrong order
]


_client: Optional[Anthropic] = None

def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def classify_intent_and_concept(
    message: str,
    problem_context: Optional[Dict[str, Any]] = None,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> Classification:
    """
    Classify a student message into intent, concept, and misconception.

    Args:
        message: The student's message
        problem_context: Current problem info (topic, stem, parts, etc.)
        recent_thread: Last few messages for context

    Returns:
        Classification result
    """
    # Build context
    problem_info = ""
    if problem_context:
        problem_info = f"""
CURRENT PROBLEM:
- Topic: {problem_context.get('topic', 'unknown')}
- Course: {problem_context.get('course', 'unknown')}
- Stem: {problem_context.get('stem', '')[:200]}
"""

    thread_info = ""
    if recent_thread:
        recent = recent_thread[-4:]  # Last 4 messages
        thread_info = "\nRECENT CONVERSATION:\n" + "\n".join(
            f"- {msg.get('role', 'user')}: {str(msg.get('text', msg.get('content', '')))[:100]}"
            for msg in recent
        )

    prompt = f"""Classify this student message in a calculus tutoring context.

{problem_info}
{thread_info}

STUDENT MESSAGE: "{message}"

Output JSON only:
{{
  "intent": "<one of: {', '.join(INTENTS.keys())}>",
  "concept": "<calculus concept or null if not specific>",
  "misconception": "<suspected error pattern or null>",
  "confidence": <0.0-1.0>,
  "language": "<en or zh>",
  "requires_strategy": <true if needs complex teaching decision, false if simple response suffices>,
  "reasoning": "<brief explanation>"
}}

Concepts: {', '.join(CONCEPTS[:15])}...
Misconceptions: {', '.join(MISCONCEPTIONS[:5])}...

requires_strategy should be TRUE for:
- "ask_next_step" (needs to know where student is in solution)
- "check_answer" (needs to verify correctness)
- "attempt_answer" (needs to evaluate)
- Messages that need teaching path decisions

requires_strategy should be FALSE for:
- "acknowledgment" (just say "great, what's next")
- "ask_hint" with clear concept (can retrieve hint)
- "ask_explanation" with clear concept (can retrieve explanation)
- Simple clarification requests"""

    try:
        response = _get_client().messages.create(
            model=CLASSIFIER_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Parse JSON
        # Handle markdown code blocks
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        data = json.loads(raw)

        return Classification(
            intent=data.get("intent", "confused"),
            concept=data.get("concept"),
            misconception=data.get("misconception"),
            confidence=float(data.get("confidence", 0.5)),
            language=data.get("language", "en"),
            requires_strategy=data.get("requires_strategy", True),
            raw_analysis=data,
        )

    except Exception as e:
        print(f"[classifier] Error: {e}")
        # Fallback classification
        lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in message) else "en"
        return Classification(
            intent="confused",
            concept=None,
            misconception=None,
            confidence=0.3,
            language=lang,
            requires_strategy=True,  # Default to Opus when unsure
            raw_analysis={"error": str(e)},
        )
