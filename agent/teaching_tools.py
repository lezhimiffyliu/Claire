"""
Teaching action tools — Claire's "action primitives".

Design:
- The orchestrator (Opus) dispatches these actions via tool_use
- Each tool's input is a structured pedagogical intent, not finished prose
- The handler internally uses cheaper models (Sonnet/Haiku) to turn intent
  into natural language
- Each handler returns:
    {
        "render": {...},   # event for the student, pushed via on_event callback
        "summary": "..."   # short status for the orchestrator, enters message history
    }

Why doesn't the orchestrator write the prose directly?
- Opus is expensive ($5/$25 per MTok). Let it do judgment; let Sonnet do generation.
- Separating judgment from generation makes prompt engineering easier — to change
  style, you edit the writer prompt without touching the orchestrator.
"""

import os
import json
import re
from typing import Optional
from anthropic import Anthropic


def _extract_json(text: str) -> str:
    """Extract JSON from model output, handling various formats."""
    text = text.strip()

    # 1. Strip markdown code fences: ```json ... ``` or ``` ... ```
    fence_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.match(fence_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 2. Find JSON object/array in the text
    # Look for { ... } or [ ... ]
    brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    bracket_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text, re.DOTALL)
    if bracket_match:
        return bracket_match.group(0)

    return text

_client: Optional[Anthropic] = None

def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


# Model assignment
WRITER_MODEL = "claude-sonnet-4-5"   # Claire's voice — generates dialogue
CARD_MODEL = "claude-haiku-4-5"      # Claire's hands — generates structured cards


# ============================================================
# Tool schemas (Anthropic native format)
# ============================================================

TEACHING_TOOL_SCHEMAS = [
    {
        "name": "say",
        "description": (
            "Speak a short message to the student. This is your primary tool. "
            "Use for: brief acknowledgment, a single hint that unlocks the next step (NOT the answer), "
            "a micro-explanation (1-3 sentences). "
            "Keep it short. If you want to say a lot, you're doing too much in one turn — break it up."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": (
                        "The pedagogical intent of this message. Specific = better generation. "
                        "Good: 'acknowledge they got the derivative right, then ask what to do at critical points'. "
                        "Bad: 'explain the next step'."
                    ),
                },
                "tone": {
                    "type": "string",
                    "enum": ["neutral", "encouraging", "playful", "concerned", "firm"],
                    "description": (
                        "Tone of voice. Use 'encouraging' when student is stuck or hesitant, "
                        "'firm' when redirecting after repeated errors, 'neutral' by default."
                    ),
                },
            },
            "required": ["intent", "tone"],
        },
    },
    {
        "name": "ask_back",
        "description": (
            "Ask the student a question instead of answering. Core forward-propagation tool. "
            "Use when: student asks 'why/how come', you want them to articulate the next step, "
            "you need to diagnose exactly where they're stuck, or you want to verify understanding "
            "before continuing. "
            "If the student needs hints to even attempt your question, set offer_hints=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": (
                        "What you want the student to think about. "
                        "Good: 'get them to notice that x^2-4x is incomplete square form'. "
                        "Bad: 'ask about completing the square'."
                    ),
                },
                "offer_hints": {
                    "type": "boolean",
                    "description": (
                        "Whether to offer 2-3 quick-reply hints below the question as scaffolding. "
                        "Use true when the question might be too open-ended for the student to attempt."
                    ),
                },
            },
            "required": ["intent", "offer_hints"],
        },
    },
    {
        "name": "concept_card",
        "description": (
            "Display a structured concept card to the student. "
            "Reserve for genuine conceptual gaps — when the student is missing a foundational "
            "concept that can't be conveyed in 1-2 sentences. "
            "Do NOT use for things `say` can handle. Cards are a heavier UI interruption."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Concept name, e.g., 'vertex of a parabola', 'chain rule'.",
                },
                "context": {
                    "type": "string",
                    "description": (
                        "What the student is stuck on right now, so the card can connect "
                        "back to their immediate problem."
                    ),
                },
                "depth": {
                    "type": "string",
                    "enum": ["minimal", "standard", "detailed"],
                    "description": (
                        "minimal: 1-liner + tiny example. "
                        "standard: definition + intuition + example. "
                        "detailed: above plus edge cases and connections."
                    ),
                },
            },
            "required": ["concept", "context", "depth"],
        },
    },
]


# ============================================================
# Handlers
# ============================================================

def _say_handler(tool_input: dict, level: str = "intermediate") -> dict:
    intent = tool_input["intent"]
    tone = tool_input["tone"]

    writer_prompt = f"""You are Claire, a calculus tutor speaking to a {level} student.
Produce ONE message to the student.

Intent: {intent}
Tone: {tone}

Constraints:
- 1-3 sentences MAX. No exceptions.
- Natural conversation. No "Great question!" or other AI-tutor cliches.
- Use $...$ for inline math, $$...$$ for display math.
- Output ONLY the message text. No quotes, no preamble, no labels."""

    resp = _get_client().messages.create(
        model=WRITER_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": writer_prompt}],
    )
    text = resp.content[0].text.strip()

    return {
        "render": {"event": "say", "text": text, "tone": tone},
        "summary": f"said ({tone}): {text[:80]}",
    }


def _ask_back_handler(tool_input: dict, level: str = "intermediate") -> dict:
    intent = tool_input["intent"]
    offer_hints = tool_input["offer_hints"]

    hints_instruction = (
        "Also provide 2-3 short quick-reply hints (5-12 words each) as thinking scaffolds."
        if offer_hints
        else "No hints needed — just the question."
    )
    json_shape = (
        '{"question": "...", "hints": ["...", "..."]}'
        if offer_hints
        else '{"question": "..."}'
    )

    writer_prompt = f"""You are Claire, a calculus tutor speaking to a {level} student.
Produce a question to ask back to the student.

Intent: {intent}

{hints_instruction}

Output strict JSON, no markdown fence:
{json_shape}

Constraints:
- Question: 1 sentence, natural.
- Use $...$ for inline math.
- Hints (if any) should be possible starting thoughts, not answers."""

    resp = _get_client().messages.create(
        model=WRITER_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": writer_prompt}],
    )

    raw = resp.content[0].text.strip()
    raw = _extract_json(raw)
    try:
        parsed = json.loads(raw)
        question = parsed.get("question", raw)
        hints = parsed.get("hints", []) if offer_hints else []
    except json.JSONDecodeError:
        question = raw
        hints = []

    return {
        "render": {"event": "ask_back", "question": question, "hints": hints},
        "summary": f"asked: {question[:80]}",
    }


def _concept_card_handler(tool_input: dict, level: str = "intermediate") -> dict:
    concept = tool_input["concept"]
    context = tool_input["context"]
    depth = tool_input["depth"]

    sentence_count = {"minimal": "2-3", "standard": "4-6", "detailed": "6-10"}[depth]

    card_prompt = f"""Generate a math concept card for a {level} student.

Concept: {concept}
Student's current context: {context}
Depth: {depth} ({sentence_count} sentences in the explanation)

Output strict JSON, no markdown fence:
{{
  "title": "...",
  "one_liner": "one-sentence definition",
  "explanation": "explanation for a {level} student, {sentence_count} sentences",
  "example": "one concrete worked mini-example",
  "connect_to_current": "how this concept applies to what the student is stuck on right now"
}}

Use $...$ for inline math, $$...$$ for display math. Output ONLY the JSON."""

    resp = _get_client().messages.create(
        model=CARD_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": card_prompt}],
    )

    raw = resp.content[0].text.strip()
    raw = _extract_json(raw)
    try:
        card = json.loads(raw)
    except json.JSONDecodeError:
        card = {
            "title": concept,
            "one_liner": "",
            "explanation": raw,
            "example": "",
            "connect_to_current": "",
        }

    return {
        "render": {"event": "concept_card", "card": card},
        "summary": f"showed concept card: {concept}",
    }


# ============================================================
# Dispatcher
# ============================================================

_HANDLERS = {
    "say": _say_handler,
    "ask_back": _ask_back_handler,
    "concept_card": _concept_card_handler,
}


def execute_teaching_tool(name: str, tool_input: dict, level: str = "intermediate") -> dict:
    """
    Run a teaching tool by name. Returns {render, summary}.
    Errors are caught and returned as summaries so the orchestrator can recover.
    """
    handler = _HANDLERS.get(name)
    if not handler:
        return {
            "render": None,
            "summary": f"error: unknown tool '{name}'",
        }
    try:
        return handler(tool_input, level=level)
    except Exception as e:
        return {
            "render": None,
            "summary": f"error executing {name}: {e}",
        }