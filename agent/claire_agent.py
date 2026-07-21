"""
Claire - Making Calculus Clear

Rewrite:
- Native Anthropic SDK, no LangChain/LangGraph
- Multi-model tiering: Opus orchestrates, Sonnet writes dialogue, Haiku writes cards
- Forward propagation enforced structurally via tool API
- Preserved: exam_context, student level, weak-topic tracking, system commands

Usage:
    agent = ClaireAgent()
    agent.set_user_level("intermediate")
    agent.set_exam_context(ctx)
    agent.process_query(user_input, on_event=callback)
"""

import os
import json
from typing import Callable, Optional, List, Dict, Any
from dotenv import load_dotenv
from anthropic import Anthropic

from agent.prompts import build_system_prompt
from agent.teaching_tools import TEACHING_TOOL_SCHEMAS, execute_teaching_tool

load_dotenv()


# Orchestrator model — does the judgment work (which tool, what params)
# Phase 5: Use Opus for strategic decisions, Sonnet for simple queries
ORCHESTRATOR_MODEL_PREMIUM = "claude-opus-4-5"
ORCHESTRATOR_MODEL_BASIC = "claude-sonnet-4-20250514"  # Sonnet for simple intents

# Cap agent loop iterations as a safety net
MAX_TURNS_PER_QUERY = 6


def get_secret(key: str) -> Optional[str]:
    return os.getenv(key)


class ClaireAgent:
    """Claire — calculus tutor agent."""

    def __init__(self):
        # Student profile
        self.user_level: str = "intermediate"
        self.weak_topics: List[str] = []
        self.strong_topics: List[str] = []

        # Conversation history (Anthropic format)
        self.conversation_history: List[Dict[str, Any]] = []

        # Exam materials context (set externally via set_exam_context)
        self.exam_context = None

        # Model tier: "premium" = Opus, "basic" = Haiku
        self.model_tier: str = "premium"

        # Anthropic client
        api_key = get_secret("ANTHROPIC_API_KEY")
        if not api_key:
            print("[ClaireAgent] ANTHROPIC_API_KEY not found in env")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)

        print(f"[ClaireAgent] initialized (tier={self.model_tier})")

    # ============================================================
    # Public API
    # ============================================================

    def process_query(
        self,
        user_input: str,
        on_event: Optional[Callable[[dict], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process a student message.

        Args:
            user_input: the student's message
            on_event: optional callback fired immediately when each tool produces
                      a render event. Signature: on_event(event_dict). For sync
                      callers that just want the final result, leave this None
                      and read 'events' from the returned dict.

        Returns:
            {
                "events": [render_event, ...],  # all events from this query in order
                "turns": int,                    # how many orchestrator iterations
            }
        """
        # System commands short-circuit
        sys_response = self._check_system_commands(user_input)
        if sys_response is not None:
            event = {"event": "say", "text": sys_response, "tone": "neutral"}
            if on_event:
                on_event(event)
            return {"events": [event], "turns": 0}

        if not self.client:
            event = {
                "event": "say",
                "text": "I'm having trouble connecting right now. Please try again in a moment.",
                "tone": "concerned",
            }
            if on_event:
                on_event(event)
            return {"events": [event], "turns": 0}

        # Inject exam context as a separate user message before the actual input.
        # Kept out of system prompt because it changes between turns — putting it
        # there would bust the system-prompt cache.
        injected_user_content = self._compose_user_message(user_input)

        self.conversation_history.append(
            {"role": "user", "content": injected_user_content}
        )

        events_collected: List[dict] = []
        turns = 0

        try:
            turns = self._run_agent_loop(events_collected, on_event)
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_event = {
                "event": "say",
                "text": f"Something went wrong on my end: {e}",
                "tone": "concerned",
            }
            events_collected.append(err_event)
            if on_event:
                on_event(err_event)

        self._trim_history()
        return {"events": events_collected, "turns": turns}

    # ============================================================
    # Agent loop
    # ============================================================

    def _run_agent_loop(
        self,
        events_collected: List[dict],
        on_event: Optional[Callable[[dict], None]],
    ) -> int:
        """
        Run the agent loop until orchestrator stops calling tools.
        Mutates self.conversation_history. Returns number of turns.
        """
        system_prompt = build_system_prompt(self.user_level, self.weak_topics)
        orchestrator_model = (
            ORCHESTRATOR_MODEL_PREMIUM
            if self.model_tier == "premium"
            else ORCHESTRATOR_MODEL_BASIC
        )

        for turn in range(MAX_TURNS_PER_QUERY):
            response = self.client.messages.create(
                model=orchestrator_model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TEACHING_TOOL_SCHEMAS,
                messages=self.conversation_history,
            )

            # Append assistant message to history
            self.conversation_history.append(
                {"role": "assistant", "content": response.content}
            )

            # End condition: orchestrator finished without calling a tool
            if response.stop_reason == "end_turn":
                # Orchestrator emitted text but we told it not to. Surface as say
                # so the student isn't left hanging.
                text_blocks = [b.text for b in response.content if b.type == "text" and b.text]
                if text_blocks:
                    fallback_event = {
                        "event": "say",
                        "text": "\n".join(text_blocks),
                        "tone": "neutral",
                    }
                    events_collected.append(fallback_event)
                    if on_event:
                        on_event(fallback_event)
                return turn + 1

            if response.stop_reason != "tool_use":
                # Unexpected — bail out
                print(f"[agent_loop] unexpected stop_reason={response.stop_reason}")
                return turn + 1

            # Execute every tool_use block in the response
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for tool_use in tool_uses:
                result = execute_teaching_tool(
                    name=tool_use.name,
                    tool_input=tool_use.input,
                    level=self.user_level,
                )

                # Push render event to caller
                if result["render"]:
                    events_collected.append(result["render"])
                    if on_event:
                        on_event(result["render"])

                # Build tool_result for orchestrator
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result["summary"],
                })

            # Feed tool results back to orchestrator
            self.conversation_history.append(
                {"role": "user", "content": tool_results}
            )

            # Forward-propagation discipline: after a tool runs and the student
            # has seen something, stop and wait for them. Don't let the
            # orchestrator chain a follow-up tool in the same query.
            return turn + 1

        # Hit max turns
        return MAX_TURNS_PER_QUERY

    # ============================================================
    # Message composition (exam context injection)
    # ============================================================

    def _compose_user_message(self, user_input: str) -> str:
        """Wrap the student's input with exam context if relevant."""
        context_info = ""
        if self.exam_context and self.exam_context.has_context():
            context_info = self._format_exam_context(user_input)

        if context_info:
            return f"{user_input}\n{context_info}"
        return user_input

    def _format_exam_context(self, user_input: str = "") -> str:
        """
        Surface exam materials to the orchestrator.
        Only dumps full problem text when student appears to reference a problem.
        """
        if not self.exam_context:
            return ""

        referencing = self._is_referencing_problem(user_input)

        if not referencing:
            if self.exam_context.has_questions():
                count = len(self.exam_context.question_bank.questions)
                names = ", ".join(self.exam_context.material_names[:3])
                return (
                    f"\n[Note: Student has {count} problems loaded from: {names}. "
                    "If they reference a specific problem, you can access it.]"
                )
            return ""

        lines = ["\n[COURSE MATERIALS]"]
        lines.append(f"Files: {', '.join(self.exam_context.material_names[:3])}")

        if self.exam_context.has_questions():
            bank = self.exam_context.question_bank
            matched = self._find_referenced_problems(user_input)
            if matched:
                lines.append("\n=== REFERENCED PROBLEM(S) ===")
                for q in matched[:3]:
                    lines.append(f"\n**{q.format_source()}**")
                    if getattr(q, "categories", None):
                        lines.append(f"Topics: {', '.join(q.categories)}")
                    lines.append(f"Problem: {q.text}")
                    lines.append("---")
            else:
                lines.append(f"\nTotal: {len(bank.questions)} problems")
                lines.append("Problem list:")
                for i, q in enumerate(bank.questions[:10]):
                    lines.append(f"  #{i+1}: {q.format_source()} - {q.text[:60]}...")

        lines.append("[END MATERIALS]")
        return "\n".join(lines)

    def _is_referencing_problem(self, user_input: str) -> bool:
        if not user_input:
            return False
        text = user_input.lower()
        ref_patterns = [
            "problem ", "question ", "q ", "p ", "#",
            "sample", "exam", "spring", "fall", "midterm", "final",
            "the first", "the second", "the third",
            "help me with", "work on", "practice",
        ]
        if any(p in text for p in ref_patterns):
            return True
        import re
        return bool(re.search(r"\b(problem|question|q|p)\s*\d+", text, re.IGNORECASE))

    def _find_referenced_problems(self, user_input: str) -> list:
        if not self.exam_context or not self.exam_context.has_questions():
            return []
        bank = self.exam_context.question_bank
        text = user_input.lower()
        import re

        num_match = re.search(r"(?:problem|question|q|p|#)\s*(\d+)", text, re.IGNORECASE)
        if num_match:
            idx = int(num_match.group(1)) - 1
            if 0 <= idx < len(bank.questions):
                return [bank.questions[idx]]

        matched = []
        for q in bank.questions:
            source_lower = q.format_source().lower()
            source_words = source_lower.replace("-", " ").replace("_", " ").split()
            if any(w in text for w in source_words if len(w) > 2):
                matched.append(q)
                if len(matched) >= 3:
                    break
        return matched

    # ============================================================
    # History management
    # ============================================================

    def _trim_history(self):
        """Keep history bounded. Orchestrator still benefits from system-prompt cache."""
        # Keep last 20 messages (~10 exchanges). Tune based on real usage.
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    # ============================================================
    # System commands
    # ============================================================

    def _check_system_commands(self, user_input: str) -> Optional[str]:
        cmd = user_input.lower().strip()
        if cmd == "clear":
            self.conversation_history = []
            return "Conversation cleared."
        if cmd == "reset":
            self.conversation_history = []
            self.user_level = "intermediate"
            self.weak_topics = []
            self.strong_topics = []
            return "Agent reset."
        if cmd == "status":
            return self._show_status()
        if cmd.startswith("level "):
            level = cmd.split("level ", 1)[1].strip()
            return self._set_level_cmd(level)
        return None

    def _show_status(self) -> str:
        return (
            f"**Claire status**\n"
            f"- Student level: {self.user_level}\n"
            f"- Weak topics: {', '.join(self.weak_topics) or 'none'}\n"
            f"- Model tier: {self.model_tier}\n"
            f"- History: {len(self.conversation_history)} messages\n"
            f"- Exam context: {'loaded' if self.exam_context and self.exam_context.has_context() else 'none'}"
        )

    def _set_level_cmd(self, level: str) -> str:
        if level in ("beginner", "intermediate", "advanced"):
            self.user_level = level
            return f"Level set to: {level}"
        return "Invalid level. Use: beginner, intermediate, advanced"

    # ============================================================
    # Setters used by the rest of the app
    # ============================================================

    def set_user_level(self, level: str) -> None:
        if level in ("beginner", "intermediate", "advanced"):
            self.user_level = level

    def set_diagnostic_result(self, result) -> None:
        if result.level in ("beginner", "intermediate", "advanced"):
            self.user_level = result.level
        self.weak_topics = list(getattr(result, "weak_topics", []))
        self.strong_topics = list(getattr(result, "strong_topics", []))

    def set_model_tier(self, tier: str) -> None:
        if tier in ("premium", "basic"):
            self.model_tier = tier
            print(f"[ClaireAgent] tier switched to {tier}")

    def set_exam_context(self, context) -> None:
        self.exam_context = context

    def clear_exam_context(self) -> None:
        self.exam_context = None

    def get_exam_patterns(self) -> list:
        if self.exam_context and self.exam_context.has_context():
            return self.exam_context.detected_patterns
        return []

    def suggest_practice(self) -> Optional[str]:
        if not self.exam_context or not self.exam_context.has_context():
            return None
        top_patterns = self.exam_context.get_top_patterns(3)
        if not top_patterns:
            return None
        top = top_patterns[0]
        return (
            f"Based on your course materials, **{top.name.replace('_', ' ').title()}** "
            f"appears frequently. {top.priority}"
        )