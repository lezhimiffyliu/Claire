"""
Response Adapter

Generates Claire's response by adapting retrieved teaching chunks
to the specific student message and context.

Uses Sonnet for natural, contextual adaptation.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from anthropic import Anthropic

from tutor.retrieval import TeachingChunk
from tutor.classifier import Classification

# Sonnet for adaptation (good balance of quality/cost)
ADAPTER_MODEL = "claude-sonnet-4-6"


@dataclass
class ClaireEvent:
    """A Claire teaching event."""
    event: str  # "say", "ask_back", "concept_card"
    text: Optional[str] = None
    question: Optional[str] = None
    hints: Optional[List[str]] = None
    tone: str = "neutral"
    card: Optional[Dict[str, Any]] = None


@dataclass
class AdaptedResponse:
    """Result of response adaptation."""
    events: List[ClaireEvent]
    model_used: str
    chunks_used: List[str]  # Chunk IDs used


_client: Optional[Anthropic] = None

def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def generate_adapted_response(
    retrieved_chunks: List[TeachingChunk],
    classification: Classification,
    message: str,
    problem_context: Optional[Dict[str, Any]] = None,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> AdaptedResponse:
    """
    Generate Claire's response by adapting retrieved teaching chunks.

    Args:
        retrieved_chunks: Teaching chunks from retrieval
        classification: Intent/concept classification
        message: Original student message
        problem_context: Current problem info
        recent_thread: Recent conversation for context

    Returns:
        AdaptedResponse with Claire events
    """
    # Build chunk context
    chunk_info = ""
    if retrieved_chunks:
        chunk_info = "\n\nTEACHING RESOURCES:\n"
        for i, chunk in enumerate(retrieved_chunks[:3]):
            chunk_info += f"""
Resource {i+1} (score: {chunk.score:.2f}):
- Concept: {chunk.concept}
- Explanation: {chunk.canonical_explanation}
- Socratic prompt: {chunk.socratic_prompt}
- Example: {chunk.mini_example}
- When to use: {chunk.when_to_use}
- Avoid: {chunk.avoid}
"""

    # Build problem context
    problem_info = ""
    if problem_context:
        problem_info = f"""
CURRENT PROBLEM:
- Topic: {problem_context.get('topic', 'unknown')}
- Course: Math {problem_context.get('course', '126')}
- Stem: {problem_context.get('stem', '')[:300]}
"""
        if problem_context.get('parts'):
            current_part = problem_context['parts'][0] if problem_context['parts'] else None
            if current_part:
                problem_info += f"- Current part: {current_part.get('question_text', '')[:200]}\n"

    # Build thread context
    thread_info = ""
    if recent_thread:
        recent = recent_thread[-4:]
        thread_info = "\nRECENT CONVERSATION:\n" + "\n".join(
            f"- {msg.get('role', 'user')}: {str(msg.get('text', msg.get('content', '')))[:100]}"
            for msg in recent
        )

    # Build the adaptation prompt
    prompt = f"""You are Claire, a calculus tutor. Generate a response to the student.

CLASSIFICATION:
- Intent: {classification.intent}
- Concept: {classification.concept or 'general'}
- Language: {classification.language}
{problem_info}
{thread_info}
{chunk_info}

STUDENT MESSAGE: "{message}"

OUTPUT FORMAT (JSON only, no markdown):
Choose ONE response type based on what's most appropriate:

Option 1 - Say (brief message, 1-3 sentences):
{{"event": "say", "text": "...", "tone": "neutral|encouraging|concerned"}}

Option 2 - Ask back (Socratic question):
{{"event": "ask_back", "question": "...", "hints": ["hint1", "hint2"]}}

Option 3 - Concept card (for fundamental concept gaps):
{{"event": "concept_card", "card": {{"title": "...", "one_liner": "...", "explanation": "...", "example": "..."}}}}

RULES:
- Use the teaching resources above to inform your response
- Keep "say" SHORT (1-3 sentences max)
- Use "ask_back" to push student thinking forward
- Use {classification.language} language (en or zh)
- Use $...$ for inline math

CRITICAL FOR ACKNOWLEDGMENT/OK:
- If the student just said "ok", "got it", "I see" etc., they are acknowledging YOUR PREVIOUS MESSAGE
- Look at what Claire said in RECENT CONVERSATION above
- Your response must CONTINUE from that point, NOT restart the problem
- Example: If Claire just explained f_x, respond with "Great! Now try f_y yourself. What do you get?"
- NEVER say "Let's get started" or repeat the problem introduction after an acknowledgment
- Be warm but concise
- Don't just repeat the canonical explanation verbatim - adapt it to the student's specific question"""

    try:
        response = _get_client().messages.create(
            model=ADAPTER_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Parse JSON
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        data = json.loads(raw)

        # Convert to ClaireEvent
        event_type = data.get("event", "say")
        event = ClaireEvent(
            event=event_type,
            text=data.get("text"),
            question=data.get("question"),
            hints=data.get("hints", []),
            tone=data.get("tone", "neutral"),
            card=data.get("card"),
        )

        return AdaptedResponse(
            events=[event],
            model_used=ADAPTER_MODEL,
            chunks_used=[c.id for c in retrieved_chunks[:3]],
        )

    except Exception as e:
        print(f"[adapter] Error: {e}")
        # Fallback response
        fallback_text = "I'm here to help. Could you tell me more about what's confusing you?"
        if classification.language == "zh":
            fallback_text = "我在这里帮助你。能告诉我你哪里不懂吗？"

        return AdaptedResponse(
            events=[ClaireEvent(event="say", text=fallback_text, tone="encouraging")],
            model_used="fallback",
            chunks_used=[],
        )


def events_to_dict(events: List[ClaireEvent]) -> List[Dict[str, Any]]:
    """Convert ClaireEvents to dict format for API response."""
    result = []
    for e in events:
        d = {"event": e.event, "tone": e.tone}
        if e.event == "say":
            d["text"] = e.text
        elif e.event == "ask_back":
            d["question"] = e.question
            d["hints"] = e.hints or []
        elif e.event == "concept_card":
            d["card"] = e.card
        result.append(d)
    return result
