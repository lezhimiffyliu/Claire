"""
Claire - Making Calculus Clear

Exam prep agent: Pattern Detection → Heuristic Teaching → Guided Practice
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class ClaireAgent:
    """Claire - Making Calculus Clear"""

    SYSTEM_PROMPT_TEMPLATE = """You are Claire, a calculus tutor.

IMPORTANT: When course materials are loaded, you have access to the FULL problem texts.
When a student asks to work on a specific problem (e.g., "Problem 5", "Q3"), find it in the loaded materials and USE the actual problem text. Do NOT ask the student to provide the problem - you already have it.

CRITICAL TEACHING RULE - NEVER GIVE THE FINAL ANSWER:
- Do NOT solve the problem completely
- Do NOT reveal the answer (e.g., "The answer is C")
- Do NOT compute the final result for them
- INSTEAD: Guide them to discover it themselves

When teaching a problem:
1. Restate the problem with proper math notation
2. FIRST: Teach the key formula/rule they need (this is factual, they must memorize it)
3. THEN: Have them apply it step by step
4. If they get stuck, give a hint, not the answer
5. Only confirm when THEY provide the correct answer

IMPORTANT: Always teach the rule BEFORE asking them to apply it. Students can't apply what they don't know.

Example flow for second derivative test:
- "This is about classifying critical points. Here's what you need to know:
   - We compute D = f_xx * f_yy - (f_xy)^2
   - If D > 0 and f_xx > 0 → local minimum
   - If D > 0 and f_xx < 0 → local maximum
   - If D < 0 → saddle point
   - If D = 0 → test is inconclusive
   You must memorize these rules!"
- "Now, let's compute D with the given values. What do you get?"
- [Student computes]
- "Good! So D = -11. Based on the rules above, what type of point is this?"

{level_instructions}

Teaching style:
- Be concise and clear
- Use natural math teacher language
- Never use words like "pattern", "heuristic", "AI", "system", "detected"
- Cite the source when using problems from materials

Math: Use $...$ for inline and $$...$$ for display equations.

Respond in the same language as the student.
"""

    LEVEL_INSTRUCTIONS = {
        "beginner": """STUDENT LEVEL: BEGINNER — Foundations need work.
- Use simple, everyday language. Avoid jargon; if you must use a term, define it immediately.
- Be very explicit about each step — never skip steps or assume prior knowledge.
- Use intuitive analogies and visual descriptions (e.g., "think of the derivative as the slope of the hill you're walking on").
- Encourage frequently. Mistakes are learning opportunities — be patient and supportive.
- Break problems into very small sub-steps (one operation per step).
- Always restate what symbols mean (e.g., "f'(x), which means the derivative of f").""",

        "intermediate": """STUDENT LEVEL: INTERMEDIATE — Has basics but calculus is shaky.
- Reinforce method selection: explain WHY you pick a certain approach, not just how.
- Point out common traps and mistakes for the problem type.
- Still explain each step, but you can combine straightforward operations.
- Ask the student to justify their choices ("Why did you pick u-substitution here?").
- When they make errors, ask guiding questions rather than just correcting.""",

        "advanced": """STUDENT LEVEL: ADVANCED — Strong student, focus on speed and strategy.
- Be concise. Skip obvious algebra steps; focus on strategy and key decision points.
- Emphasize pattern recognition: "Notice this has the same structure as..."
- Push toward timed practice mindset — efficiency matters for exams.
- Challenge them with follow-up variations or edge cases.
- When they get it right, move on quickly. Don't over-explain what they already know.""",
    }

    @property
    @property
    def system_prompt(self) -> str:
        """Build system prompt based on current user level and weak topics."""
        level_text = self.LEVEL_INSTRUCTIONS.get(self.user_level, self.LEVEL_INSTRUCTIONS["intermediate"])

        weak_section = ""
        if self.weak_topics:
            try:
                from practice_planner import TOPIC_LABELS
                labels = [TOPIC_LABELS.get(t, t.replace("_", " ").title()) for t in self.weak_topics]
                weak_section = (
                    f"\n\nSTUDENT WEAK AREAS (from diagnostic): {', '.join(labels)}. "
                    "When a problem touches one of these areas, be especially thorough — "
                    "slow down, explain the concept from first principles, and verify understanding "
                    "before moving on. When suggesting what to practice next, prefer these topics."
                )
            except ImportError:
                pass

        return self.SYSTEM_PROMPT_TEMPLATE.format(
            level_instructions=level_text + weak_section
        )

    def __init__(self):
        """Initialize Claire 2.0 Agent"""
        self.conversation_history: List[Dict[str, str]] = []
        self.user_level = "intermediate"
        self.weak_topics: List[str] = []
        self.strong_topics: List[str] = []
        self.current_pattern: Optional[str] = None
        self.current_heuristic: Optional[str] = None

        # Exam context from uploaded materials
        self.exam_context = None

        # (legacy) study plan snippet — kept for backwards compat
        self._study_plan_snippet: str = ""

        # LangChain components
        self.llm = None
        self.tools = None
        self.executor = None
        self.model_tier = "premium"  # "premium" (Claude) or "basic" (DeepSeek)

        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize LangChain ReAct agent with tools"""
        print("\n" + "=" * 60)
        print("Claire 2.0 - Exam Preparation Agent")
        print("=" * 60)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("ANTHROPIC_API_KEY not found in environment")
            print("Please add it to your .env file")
            return

        try:
            from langchain_anthropic import ChatAnthropic
            from langgraph.prebuilt import create_react_agent

            # Import tools
            from sympy_tools import CLAIRE_TOOLS
            from pattern_tools import PATTERN_TOOLS

            # Initialize Claude
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                temperature=0.7,
                max_tokens=2048,
            )
            print("AI Engine: Claude Sonnet")

            # Combine all tools
            self.tools = CLAIRE_TOOLS + PATTERN_TOOLS
            print(f"Tools loaded: {len(self.tools)}")
            for tool in self.tools:
                print(f"  - {tool.name}")

            # Create ReAct agent
            self.executor = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=self.system_prompt
            )
            print("ReAct Agent: Ready")

        except ImportError as e:
            print(f"Missing dependency: {e}")
            print("Run: pip install -r requirements.txt")
        except Exception as e:
            print(f"Initialization error: {e}")

        print("=" * 60)

    def _is_student_answer(self, user_input: str) -> bool:
        """
        Detect if user input is a student answer to a previous question,
        rather than a new problem.
        """
        text = user_input.strip().lower()

        # If no conversation history, it's a new question
        if not self.conversation_history:
            return False

        # If no current pattern, it's a new question
        if not self.current_pattern:
            return False

        # Short responses are likely answers
        if len(text) < 100:
            return True

        # Starts with answer-like words
        answer_starters = ['yes', 'no', 'i think', 'the answer', 'it is', 'that would be',
                          'so', 'because', 'since', 'we get', 'this gives']
        if any(text.startswith(s) for s in answer_starters):
            return True

        # Does NOT start with question words (likely an answer)
        question_starters = ['what', 'how', 'why', 'find', 'calculate', 'solve',
                            'compute', 'determine', 'evaluate', 'prove', 'show',
                            'maximize', 'minimize', 'integrate', 'differentiate']
        if not any(text.startswith(q) for q in question_starters):
            # Short-ish text without question words = likely answer
            if len(text) < 200:
                return True

        return False

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through the exam preparation agent.

        Returns:
            Dict with 'output', 'intermediate_steps', 'pattern', 'heuristic'
        """
        # Check system commands first
        system_response = self._check_system_commands(user_input)
        if system_response:
            self._add_to_history(user_input, system_response)
            return {
                "output": system_response,
                "intermediate_steps": [],
                "pattern": None,
                "heuristic": None
            }

        if not self.executor:
            error_msg = (
                "Claire is not initialized. "
                "Please add ANTHROPIC_API_KEY to your .env file."
            )
            return {
                "output": error_msg,
                "intermediate_steps": [],
                "pattern": None,
                "heuristic": None
            }

        try:
            from pattern_tools import detect_pattern, get_heuristic

            # Check if this is a student answer or a new question
            is_continuation = self._is_student_answer(user_input)

            if is_continuation and self.current_pattern and self.current_heuristic:
                # Continue with existing pattern - don't re-detect
                detected_pattern = self.current_pattern
                heuristic_content = self.current_heuristic

                # Build continuation input
                enhanced_input = self._build_continuation_input(user_input)
            else:
                # New question - detect pattern and load heuristic
                is_continuation = False
                detected_pattern = detect_pattern(user_input)
                self.current_pattern = detected_pattern

                heuristic_content = get_heuristic.invoke({"pattern": detected_pattern})
                self.current_heuristic = heuristic_content

                # Build teaching input
                enhanced_input = self._build_teaching_input(
                    user_input, detected_pattern, heuristic_content
                )

            # Step 4: Invoke agent
            from langchain_core.messages import HumanMessage, AIMessage

            messages = []
            for msg in self.conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=enhanced_input))

            result = self.executor.invoke({"messages": messages})

            # Extract response
            final_output = ""
            intermediate_steps = []

            for msg in result.get("messages", []):
                if hasattr(msg, "type"):
                    if msg.type == "ai" and msg.content:
                        final_output = msg.content
                    elif msg.type == "tool":
                        intermediate_steps.append(msg)

            self._add_to_history(user_input, final_output)

            return {
                "output": final_output,
                "intermediate_steps": intermediate_steps,
                "pattern": detected_pattern,
                "heuristic": heuristic_content,
                "is_continuation": is_continuation
            }

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            import traceback
            traceback.print_exc()
            return {
                "output": error_msg,
                "intermediate_steps": [],
                "pattern": None,
                "heuristic": None
            }

    def _build_continuation_input(self, user_input: str) -> str:
        """Build input for when student is answering a previous question."""
        context_info = ""
        if self.exam_context and self.exam_context.has_context():
            context_info = self._format_exam_context()

        return f"""The student said: {user_input}
{context_info}
If this is an answer to your question: evaluate and guide to next step.
If this is a new question or request: help them with it.
Keep responses concise."""

    def _build_teaching_input(self, user_input: str, pattern: str, heuristic: str) -> str:
        """Build input that enforces teaching behavior."""
        heuristic_summary = self._summarize_heuristic(heuristic)

        # Map internal pattern names to user-friendly problem types
        problem_type_map = {
            "optimization": "optimization (finding max/min)",
            "constrained_optimization": "optimization with constraints",
            "related_rates": "related rates",
            "derivatives": "differentiation",
            "integration": "integration",
            "limits": "limits",
        }
        problem_type = problem_type_map.get(pattern, pattern.replace('_', ' '))

        # Add exam context if available
        context_info = ""
        if self.exam_context and self.exam_context.has_context():
            context_info = self._format_exam_context()

        return f"""{user_input}
{context_info}
[For your reference - do not mention these labels:
This is a {problem_type} problem.
Key steps: {heuristic_summary[:300]}]"""

    def _format_exam_context(self) -> str:
        """Format exam context for the prompt."""
        if not self.exam_context:
            return ""

        lines = ["\n[COURSE MATERIALS - YOU HAVE ACCESS TO THESE PROBLEMS]"]
        lines.append(f"Files: {', '.join(self.exam_context.material_names[:5])}")

        if self.exam_context.has_questions():
            bank = self.exam_context.question_bank
            lines.append(f"Total problems: {len(bank)}")

            # Show ALL problems with FULL text and metadata
            lines.append("\n=== PROBLEMS FROM STUDENT'S MATERIALS ===")
            for i, q in enumerate(bank.questions):
                source_cite = q.format_source()
                # Include multiple ways to reference this problem
                lines.append(f"\n[#{i+1}] {source_cite}")
                lines.append(f"ID: {q.id} | Short: P{i+1} | {q.problem_id}")
                if q.categories:
                    lines.append(f"Topics: {', '.join(q.categories)}")
                lines.append(f"Difficulty: {q.difficulty}")
                lines.append(f"Problem text: {q.text}")
                lines.append("---")

            # Quick reference guide
            lines.append("\n=== QUICK REFERENCE ===")
            lines.append("Students may refer to problems as:")
            lines.append("- 'Problem 1', 'P1', '#1', 'the first problem'")
            lines.append("- 'Sample 1 Problem 5', '18 Spring Problem 3'")
            lines.append("- By topic: 'a Lagrange problem', 'double integral question'")
            lines.append("Match their reference to the problems above and use the FULL text.")

        lines.append("\n[END MATERIALS]")
        return "\n".join(lines)

    def _summarize_heuristic(self, heuristic: str) -> str:
        """Extract the solving template section from heuristic."""
        lines = heuristic.split('\n')
        in_template = False
        template_lines = []

        for line in lines:
            if 'Solving Template' in line or 'Template' in line:
                in_template = True
                continue
            if in_template:
                if line.startswith('##') and 'Template' not in line:
                    break
                if line.strip():
                    template_lines.append(line)

        if template_lines:
            return '\n'.join(template_lines[:10])  # Limit to first 10 lines

        # Fallback: return first 15 lines
        return '\n'.join(lines[:15])

    def _add_to_history(self, user_input: str, response: str):
        """Add exchange to conversation history."""
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})

        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def _check_system_commands(self, user_input: str) -> Optional[str]:
        """Handle system commands."""
        cmd = user_input.lower().strip()

        if cmd == "clear":
            self.conversation_history = []
            return "Conversation cleared."

        if cmd == "reset":
            self.conversation_history = []
            self.user_level = "intermediate"
            self.current_pattern = None
            self.current_heuristic = None
            return "Agent reset."

        if cmd == "help":
            return self._show_help()

        if cmd == "patterns":
            return self._show_patterns()

        if cmd == "status":
            return self._show_status()

        if cmd.startswith("level "):
            level = cmd.split("level ")[1].strip()
            return self._set_level(level)

        return None

    def _show_help(self) -> str:
        return """**Claire** - Making Calculus Clear

**Commands:**
- `help` - Show this help
- `patterns` - Show problem types
- `status` - Show system status
- `clear` - Clear conversation

**How it works:**
1. Upload your course materials (past exams, notes)
2. Claire extracts problems and detects patterns
3. Ask to practice any problem
4. Claire guides you step by step

Claire teaches you HOW to solve, not just the answer.
"""

    def _show_patterns(self) -> str:
        from pattern_tools import get_available_patterns
        patterns = get_available_patterns()

        pattern_descriptions = {
            "optimization": "Maximize/minimize without constraints",
            "constrained_optimization": "Optimize with constraint equations (Lagrange)",
            "related_rates": "Rates of change with respect to time",
            "derivatives": "Differentiation (chain, product, quotient rules)",
            "integration": "Antiderivatives and definite integrals",
            "limits": "Limit evaluation and L'Hopital's rule",
        }

        lines = ["**Available Problem Patterns:**\n"]
        for p in patterns:
            desc = pattern_descriptions.get(p, "")
            lines.append(f"- **{p}**: {desc}")

        return "\n".join(lines)

    def _show_status(self) -> str:
        return f"""**Claire 2.0 Status**

Student Level: {self.user_level}
Current Pattern: {self.current_pattern or "None"}
History: {len(self.conversation_history)} messages

AI Engine: {"Ready" if self.llm else "Not initialized"}
Tools: {len(self.tools) if self.tools else 0} loaded
"""

    def _set_level(self, level: str) -> str:
        if level in ["beginner", "intermediate", "advanced"]:
            self.user_level = level
            return f"Level set to: {level}"
        return "Invalid level. Use: beginner, intermediate, or advanced"

    def set_user_level(self, level: str) -> None:
        """Set user level and rebuild agent with updated system prompt."""
        if level in ("beginner", "intermediate", "advanced"):
            self.user_level = level
            self._rebuild_executor()

    def set_diagnostic_result(self, result) -> None:
        """Apply full diagnostic result: level + weak/strong topics, then rebuild."""
        if result.level in ("beginner", "intermediate", "advanced"):
            self.user_level = result.level
        self.weak_topics = list(getattr(result, "weak_topics", []))
        self.strong_topics = list(getattr(result, "strong_topics", []))
        self._rebuild_executor()

    def set_study_plan(self, snippet: str) -> None:
        """Inject a study-plan block into the system prompt (legacy)."""
        self._study_plan_snippet = snippet
        self._rebuild_executor()

    def _rebuild_executor(self) -> None:
        """Rebuild the LangGraph executor with the current system prompt."""
        if self.llm and self.tools:
            try:
                from langgraph.prebuilt import create_react_agent
                self.executor = create_react_agent(
                    model=self.llm,
                    tools=self.tools,
                    prompt=self.system_prompt,
                )
            except Exception:
                pass

    def switch_to_deepseek(self) -> bool:
        """Switch LLM from Claude to DeepSeek. Returns True if successful."""
        if self.model_tier == "basic":
            return True  # already on basic
        try:
            import os
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("DEEPSEEK_API_KEY") or ""
            try:
                import streamlit as st
                api_key = api_key or st.secrets.get("DEEPSEEK_API_KEY", "")
            except Exception:
                pass
            if not api_key:
                return False
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=api_key,
                base_url="https://api.deepseek.com",
                temperature=0.7,
                max_tokens=2048,
            )
            self.model_tier = "basic"
            self._rebuild_executor()
            print("AI Engine: switched to DeepSeek (basic tier)")
            return True
        except Exception as e:
            print(f"DeepSeek switch failed: {e}")
            return False

    def set_exam_context(self, context) -> None:
        """Set exam context from analyzed course materials."""
        self.exam_context = context

    def clear_exam_context(self) -> None:
        """Clear exam context."""
        self.exam_context = None

    def get_exam_patterns(self) -> list:
        """Get patterns detected from exam context."""
        if self.exam_context and self.exam_context.has_context():
            return self.exam_context.detected_patterns
        return []

    def suggest_practice(self) -> Optional[str]:
        """Suggest a pattern to practice based on exam context."""
        if not self.exam_context or not self.exam_context.has_context():
            return None

        top_patterns = self.exam_context.get_top_patterns(3)
        if not top_patterns:
            return None

        # Suggest the top pattern
        top = top_patterns[0]
        return f"Based on your course materials, **{top.name.replace('_', ' ').title()}** appears frequently. {top.priority}"
