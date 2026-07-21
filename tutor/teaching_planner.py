"""
Teaching Planner

TASK-BASED teaching, not chat.

HARD RULE for "I'm stuck":
- DO NOT ask "where are you stuck"
- DO NOT ask "what would you try"
- PROACTIVELY give the first step of the current part
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

PLANNER_MODEL = "claude-sonnet-4-6"

# Applied to every planner call. Students type math in plain text, so the tutor
# must read it charitably and never nitpick notation when the meaning is clear.
PLANNER_SYSTEM = """You are a calculus tutor guiding a student through a problem.

Students often type mathematics in plain text.
When interpreting student work, prefer charitable parsing.
Expressions such as:
  1/(x+1)
  sin(x)^2
  e^(x+y)
  (x+1)/(x-1)
should be interpreted according to normal calculator-style notation.
Do not criticize notation if the mathematical meaning is clear.
If multiple interpretations are possible, ask for clarification instead of declaring the work incorrect.

When a student's plain-text math expression is syntactically valid but commonly ambiguous,
do not immediately mark it wrong. Students frequently omit grouping parentheses around a
denominator or numerator (e.g. they type 1/x+1 when they mean 1/(x+1)). If the surrounding
problem context or expected answer suggests the student likely intended a grouped
denominator/numerator, treat the math idea as correct and give a light notation reminder.

Example:
  Student writes: 1/x+1
  Expected structure: 1/(x+1)
  Bad feedback: "This is wrong; 1/x+1 means 1/x plus 1."
  Good feedback: "I think you mean 1/(x+1). Your math idea is right — just add parentheses
  around x+1 so it reads clearly."

Do not over-penalize notation when the intended mathematical meaning is recoverable.
Only ask for clarification if both interpretations are genuinely plausible in the problem context."""

_client: Optional[Anthropic] = None

def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def execute_teaching_action(
    intent: str,
    problem_context: Dict[str, Any],
    current_part_index: int = 0,
    student_message: Optional[str] = None,
    stuck_count: int = 0,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Execute a teaching action.

    CRITICAL: problem_context MUST contain the problem info.
    If missing, we cannot teach.
    """
    if not problem_context:
        return {
            "concept_bridge": "",
            "next_micro_step": "I need to know which problem you're working on. Please select a problem first.",
        }

    stem = problem_context.get("stem", "")
    parts = problem_context.get("parts", [])
    topic = problem_context.get("topic", "calculus")

    if not stem and not parts:
        return {
            "concept_bridge": "",
            "next_micro_step": "I don't see a problem loaded. Please select a problem to work on.",
        }

    current_part = parts[current_part_index] if current_part_index < len(parts) else None
    part_text = current_part.get("question_text", "") if current_part else stem
    part_label = current_part.get("label", chr(97 + current_part_index)) if current_part else "a"

    needs_scaffolding = stuck_count >= 2 or _is_confused_message(student_message)

    if intent == "student_stuck":
        return _handle_student_stuck(stem, part_text, part_label, topic, needs_scaffolding)
    elif intent == "student_hint":
        return _handle_student_hint(stem, part_text, part_label, topic, student_message, needs_scaffolding, recent_thread)
    elif intent == "student_check":
        return _handle_student_check()
    elif intent == "followup":
        return _handle_followup(stem, part_text, part_label, topic, student_message, recent_thread)
    else:
        return _handle_student_stuck(stem, part_text, part_label, topic, needs_scaffolding)


def _format_conversation(recent_thread: Optional[List[Dict[str, Any]]]) -> str:
    """Render the recent thread as a simple transcript for the planner prompt."""
    if not recent_thread:
        return ""
    lines = []
    for msg in recent_thread:
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        speaker = "Student" if msg.get("role") == "user" else "Tutor"
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def _is_confused_message(message: Optional[str]) -> bool:
    if not message:
        return False
    msg = message.lower().strip()
    confused_patterns = [
        "idk", "i don't know", "i dont know", "no idea",
        "still confused", "still stuck", "confused",
        "what", "huh", "help", "?",
        "i forgot", "don't understand", "dont understand",
    ]
    return any(p in msg for p in confused_patterns)


def _handle_student_stuck(
    stem: str,
    part_text: str,
    part_label: str,
    topic: str,
    needs_scaffolding: bool,
) -> Dict[str, Any]:
    """
    HARD RULE: Give the first step. DO NOT ask where they're stuck.
    """
    prompt = f"""You are a calculus tutor. Student clicked "I'm stuck".

PROBLEM:
{stem}

CURRENT PART ({part_label}):
{part_text}

TOPIC: {topic}

===== CRITICAL RULES =====
1. DO NOT ask "where are you stuck?" or "what would you try?"
2. DO NOT ask generic questions
3. PROACTIVELY give the FIRST concrete step

You must:
- Give a short concept_bridge (1 sentence, what rule/concept applies)
- Give a SPECIFIC next_micro_step telling them exactly what to compute

===== OUTPUT FORMAT (JSON only) =====
{{
  "concept_bridge": "<the key concept/rule they need, e.g. 'When taking partial derivative w.r.t x, treat y as constant.'>",
  "next_micro_step": "<SPECIFIC instruction, e.g. 'Find $\\partial f/\\partial x$ by treating $y$ as constant. What is $\\frac{{d}}{{dx}}[xy]$?'>"
}}

===== GOOD EXAMPLES =====
For f(x,y) = sin(xy), find f_x:
{{
  "concept_bridge": "For partial derivatives, treat the other variable as a constant.",
  "next_micro_step": "Start by identifying the outer and inner functions. What's inside the sin()?"
}}

For optimization with constraint:
{{
  "concept_bridge": "Use Lagrange multipliers: set gradient of f equal to lambda times gradient of g.",
  "next_micro_step": "First, compute $\\nabla f$. What are $f_x$ and $f_y$?"
}}

===== BAD EXAMPLES (DO NOT DO THIS) =====
- "Where are you stuck?"
- "What would you try first?"
- "What do you think?"
- "Can you tell me more?"
"""

    result = _call_planner(prompt, stem, part_text, topic)

    if needs_scaffolding:
        result["quick_replies"] = [
            "I don't understand the concept",
            "Show me an example first",
            "What formula do I use?",
        ]

    return result


def _handle_student_hint(
    stem: str,
    part_text: str,
    part_label: str,
    topic: str,
    student_message: Optional[str],
    needs_scaffolding: bool,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Give next micro-step based on context."""
    context = f"\nSTUDENT SAID: {student_message}" if student_message else ""
    conversation = _format_conversation(recent_thread)
    conversation_block = f"\nCONVERSATION SO FAR:\n{conversation}\n" if conversation else ""

    prompt = f"""You are a calculus tutor. Student wants a hint.

PROBLEM:
{stem}

CURRENT PART ({part_label}):
{part_text}

TOPIC: {topic}
{conversation_block}{context}

Use the CONVERSATION SO FAR to continue from where you left off — don't repeat a step the
student already completed or restart the problem.
Give the next specific step. Be concrete, not vague.

OUTPUT FORMAT (JSON only):
{{
  "concept_bridge": "<short, can be empty>",
  "next_micro_step": "<specific instruction or question about what to compute>"
}}"""

    result = _call_planner(prompt, stem, part_text, topic)

    if needs_scaffolding:
        result["quick_replies"] = ["Still confused", "Show me how", "What's the formula?"]

    return result


def _handle_followup(
    stem: str,
    part_text: str,
    part_label: str,
    topic: str,
    student_message: Optional[str],
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Handle student's follow-up response in teaching mode."""
    conversation = _format_conversation(recent_thread)
    conversation_block = f"\nCONVERSATION SO FAR:\n{conversation}\n" if conversation else ""

    prompt = f"""You are a calculus tutor mid-conversation with a student on this problem.

PROBLEM:
{stem}

CURRENT PART ({part_label}):
{part_text}

TOPIC: {topic}
{conversation_block}
STUDENT'S LATEST RESPONSE: {student_message}

Use the CONVERSATION SO FAR to stay consistent: remember what you already asked, what the
student already got right, and which sub-step you are on. Continue from there.
Do NOT restart the problem. Do NOT say you have no record of the previous exchange.
Do NOT jump ahead to combining everything if you only asked about one term — respond to the
specific step the student just answered.

Evaluate their latest response and guide them to the next step:
- If correct: acknowledge specifically (name what they got right) and give the next sub-step.
- If incorrect: gently point out the issue and guide them.
- If they're asking a question (e.g. "but you were asking me ..."): answer it directly,
  acknowledge what they already did, then continue the current step.

OUTPUT FORMAT (JSON only):
{{
  "concept_bridge": "<feedback referencing what they already did in this conversation>",
  "next_micro_step": "<the next instruction or question, continuing from where you left off>"
}}"""

    return _call_planner(prompt, stem, part_text, topic)


def _handle_student_check() -> Dict[str, Any]:
    return {
        "concept_bridge": "",
        "next_micro_step": "Upload a photo of your work so I can check it.",
        "quick_replies": ["Upload my work", "Give me a hint instead"],
    }


def _call_planner(prompt: str, stem: str, part_text: str, topic: str) -> Dict[str, Any]:
    """Call the planner model. Has smart fallback with context."""
    try:
        response = _get_client().messages.create(
            model=PLANNER_MODEL,
            max_tokens=400,
            system=PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        data = json.loads(raw)

        return {
            "concept_bridge": data.get("concept_bridge", ""),
            "next_micro_step": data.get("next_micro_step", ""),
            **({"quick_replies": data["quick_replies"]} if "quick_replies" in data else {}),
        }

    except Exception as e:
        print(f"[teaching_planner] Error: {e}")
        # SMART FALLBACK: Use problem context to give a sensible default
        return _generate_fallback(stem, part_text, topic)


def _generate_fallback(stem: str, part_text: str, topic: str) -> Dict[str, Any]:
    """Generate a context-aware fallback when API fails. Always be DIRECTIVE, not questioning."""
    text_lower = (stem + " " + part_text).lower()

    # Partial derivatives - detect which variable
    if "f_x" in text_lower or "partial" in text_lower and "x" in text_lower:
        return {
            "concept_bridge": "For $f_x$, treat $y$ as a constant.",
            "next_micro_step": "Apply the derivative rules to each term, treating $y$ as just a number. What derivative rule applies to the main operation?",
        }
    elif "f_y" in text_lower or "partial" in text_lower and "y" in text_lower:
        return {
            "concept_bridge": "For $f_y$, treat $x$ as a constant.",
            "next_micro_step": "Apply the derivative rules to each term, treating $x$ as just a number. What derivative rule applies to the main operation?",
        }
    elif "partial" in text_lower:
        return {
            "concept_bridge": "For partial derivatives, treat other variables as constants.",
            "next_micro_step": "Identify which variable you're differentiating with respect to, then treat all others as constants.",
        }
    elif "lagrange" in text_lower or "constraint" in text_lower or "subject to" in text_lower:
        return {
            "concept_bridge": "Set up $\\nabla f = \\lambda \\nabla g$ where $g$ is the constraint.",
            "next_micro_step": "First compute $\\nabla f$. Take the partial derivatives $f_x$ and $f_y$.",
        }
    elif "integral" in text_lower or "integrate" in text_lower:
        return {
            "concept_bridge": "Set up the integral with correct bounds.",
            "next_micro_step": "Sketch the region and identify the bounds for each variable.",
        }
    elif "derivative" in text_lower or "differentiate" in text_lower:
        return {
            "concept_bridge": "Apply differentiation rules: power, product, quotient, chain.",
            "next_micro_step": "Identify the outermost operation and apply the corresponding rule.",
        }
    elif "limit" in text_lower:
        return {
            "concept_bridge": "Try direct substitution first.",
            "next_micro_step": "Plug in the limit value. If you get 0/0, you'll need L'Hopital or factoring.",
        }
    elif "critical" in text_lower or "extrema" in text_lower or "maximum" in text_lower or "minimum" in text_lower:
        return {
            "concept_bridge": "Critical points are where both partial derivatives equal zero.",
            "next_micro_step": "Set $f_x = 0$ and $f_y = 0$, then solve the system.",
        }
    else:
        return {
            "concept_bridge": "Let's break this down.",
            "next_micro_step": "Identify the type of problem and the key formula or technique needed.",
        }
