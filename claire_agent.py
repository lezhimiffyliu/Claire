"""
Claire 2.0 - Calculus Exam Preparation Agent

Architecture: Pattern Detection → Heuristic Teaching → Guided Learning
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class ClaireAgent:
    """Claire 2.0 - Calculus Exam Preparation Agent"""

    SYSTEM_PROMPT = """You are Claire, a calculus exam preparation teaching assistant.
Your mission: Teach students to recognize problem PATTERNS and apply solving HEURISTICS.

=== CRITICAL RULES ===

1. You are a TEACHER, not a solver. NEVER jump directly to the final answer.

2. ALWAYS structure your response in this exact order:
   a) Acknowledge the detected pattern
   b) Present the relevant heuristic template
   c) Guide the student through the FIRST step only
   d) Ask the student a question to check understanding

3. DO NOT compute the final answer immediately. Guide step by step.

4. DO NOT use SymPy tools until the student needs verification or is stuck.
   - First, teach the method
   - Then, guide them to try it
   - Only use tools to CHECK their work, not to do it for them

=== RESPONSE STRUCTURE (MANDATORY) ===

Your response MUST follow this format:

**Pattern:** [pattern name from the detection]

**Heuristic Template:**
[Summarize the key steps from the heuristic - 3-5 bullet points max]

**Let's Begin:**
[Guide the student through Step 1 of the template]

**Your Turn:**
[Ask the student to identify or compute something specific]

=== TOOL USAGE POLICY ===

- Call get_heuristic() ONCE at the start to load the template
- DO NOT call SymPy tools (derivative, integral, etc.) unless:
  - The student provides an answer that needs verification
  - The student is stuck and needs a hint
  - You are at the FINAL step and need to confirm the result
- NEVER call the same tool twice for the same expression
- Prefer teaching over computing

=== SOCRATIC METHOD ===

Instead of: "The derivative is 2x"
Say: "What rule would you use to differentiate x²?"

Instead of: "The maximum is at x=5"
Say: "Now that we have f'(x)=0, what value of x solves this equation?"

=== HEURISTIC TEACHING ===

When you retrieve a heuristic:
1. Summarize the decision tree (when to use which approach)
2. List the key steps (not all details, just the template)
3. Point out the most common mistake for this pattern
4. Guide the student to apply Step 1 to their specific problem

=== EXAM CONTEXT ===

If exam context is provided (from uploaded course materials), prioritize patterns
that appear in the student's course materials. Mention when a problem type is
"likely on your exam" based on the context.

=== LaTeX FORMATTING ===
- Inline math: $x^2 + 1$
- Display equations: $$\\frac{d}{dx}(x^2) = 2x$$

=== LANGUAGE ===
Respond in the same language as the student's question.
"""

    def __init__(self):
        """Initialize Claire 2.0 Agent"""
        self.conversation_history: List[Dict[str, str]] = []
        self.user_level = "intermediate"
        self.current_pattern: Optional[str] = None
        self.current_heuristic: Optional[str] = None

        # Exam context from uploaded materials
        self.exam_context = None

        # LangChain components
        self.llm = None
        self.tools = None
        self.executor = None

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
                prompt=self.SYSTEM_PROMPT
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
        return f"""[CONTINUATION - STUDENT IS ANSWERING]

The student is responding to your previous question.
Current pattern: {self.current_pattern.replace('_', ' ').title()}

STUDENT'S RESPONSE:
{user_input}

YOUR TASK:
1. Evaluate if the student's answer is correct
2. If correct: Acknowledge briefly, then guide to the NEXT step
3. If incorrect: Point out the specific error, give a hint
4. Ask a follow-up question for the next step
5. Still avoid giving final answers directly
6. Only use SymPy tools if you need to verify their calculation

Remember: Continue teaching, step by step."""

    def _build_teaching_input(self, user_input: str, pattern: str, heuristic: str) -> str:
        """Build input that enforces teaching behavior."""
        # Extract key parts of heuristic for the prompt
        heuristic_summary = self._summarize_heuristic(heuristic)

        # Check if this pattern is in exam context
        exam_relevance = ""
        if self.exam_context and self.exam_context.has_context():
            exam_patterns = self.exam_context.get_pattern_names()
            if pattern in exam_patterns:
                exam_relevance = f"\n[EXAM RELEVANCE: This pattern ({pattern}) was detected in the student's course materials. Mention that this is likely exam content.]"

        return f"""[TEACHING MODE - DO NOT SOLVE DIRECTLY]

DETECTED PATTERN: {pattern.replace('_', ' ').title()}
{exam_relevance}

HEURISTIC TEMPLATE (already loaded - do NOT call get_heuristic again):
{heuristic_summary}

STUDENT'S PROBLEM:
{user_input}

STUDENT LEVEL: {self.user_level}

YOUR TASK:
1. Start your response with "**Pattern:** {pattern.replace('_', ' ').title()}"
2. Show the heuristic template (summarized)
3. Guide the student through Step 1 ONLY
4. Ask them a question to check understanding
5. DO NOT compute the final answer
6. DO NOT use SymPy tools unless absolutely necessary for verification

Remember: You are teaching the METHOD, not solving the problem."""

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
        return """**Claire 2.0 - Exam Preparation Agent**

**Commands:**
- `help` - Show this help
- `patterns` - Show available problem patterns
- `status` - Show system status
- `clear` - Clear conversation
- `level [beginner|intermediate|advanced]` - Set difficulty

**How Claire teaches:**
1. You enter a calculus problem
2. Claire detects the problem pattern
3. Claire shows you the solving heuristic
4. Claire guides you through step by step
5. You practice applying the method

Claire will NOT give you the answer directly.
Claire teaches you HOW to solve it yourself.
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
