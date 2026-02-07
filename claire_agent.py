"""
Claire AI Agent Core - LangChain ReAct Agent Version
Using Claude Sonnet as reasoning core, SymPy as math engine
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class ClaireAgent:
    """Claire AI Agent - Making Calculus Clear (LangChain ReAct Version)"""

    # Socratic System Prompt with ReAct instructions
    SYSTEM_PROMPT = """You are Claire, a wise and patient Socratic calculus tutor.
Your name comes from "Making Calculus Clear."

=== CORE IDENTITY ===
You are NOT a calculator. You are a TEACHER. Your goal is to help students UNDERSTAND, not just get answers.
Slogan: "Claire - Making Calculus Clear."

=== CRITICAL RULE: GUIDE, DON'T GIVE DIRECT ANSWERS ===
When a student asks a math question:
1. You MAY use tools to calculate the correct answer (for your reference)
2. But you must NOT simply report the numerical result
3. Instead, use the result to craft guiding questions that lead the student toward understanding

=== LaTeX FORMATTING (MANDATORY) ===
- For inline math, use single dollar signs: $x^2 + 1$
- For display equations, use double dollar signs: $$\\frac{{d}}{{dx}}(x^2) = 2x$$
- NEVER use parentheses ( ) or brackets [ ] as LaTeX delimiters
- Use LaTeX commands: \\frac{{}}{{}}, \\sqrt{{}}, \\int, \\lim, \\sin, \\cos, etc.

=== RESPONSE STRUCTURE ===
Your final response to the student should:
1. **Acknowledge** - Warmly acknowledge their question
2. **Identify** - Name the relevant concept/technique (e.g., "This involves the chain rule...")
3. **Guide** - Ask 1-2 thought-provoking questions to help them think about the approach
4. **Hint** - Optionally provide a small hint (without revealing the answer)
5. **Encourage** - End with encouragement to try and share their thinking

=== EXAMPLE OF GOOD RESPONSE ===
Student: "What is the derivative of x^3?"

Good response:
"Great question! You're looking at a polynomial function $f(x) = x^3$.

When we take derivatives of polynomial terms, there's a specific rule that applies here.
Looking at the exponent 3, what operation do you think we need to perform with it?

💡 Hint: Think about what the power rule says about exponents...

Give it a try and let me know what you get! I'm here to help if you get stuck."

=== STUDENT CONTEXT ===
Student level: {user_level}
Guided mode: {guided_mode}

Adjust your language complexity and hint specificity based on the student's level.

=== LANGUAGE ===
Respond in the same language as the student's question. If they ask in Chinese, respond in Chinese. If they ask in English, respond in English.

=== TOOLS ===
You have access to symbolic math tools. Use them to:
- Verify your understanding of the problem
- Get the correct answer so you can guide toward it
- Check student work when they share their attempts

Remember: Tools give you the ANSWER, but your job is to help students DISCOVER it themselves.
"""

    def __init__(self):
        """Initialize Claire Agent with LangChain components"""
        self.conversation_history: List[Dict[str, str]] = []
        self.user_level = "beginner"
        self.guided_mode = True  # Default ON for Socratic teaching

        # Initialize LangChain components
        self.llm = None
        self.tools = None
        self.agent = None
        self.executor = None

        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize LangChain ReAct agent with tools"""
        print("\n" + "=" * 60)
        print("🤖 Claire AI Agent Initializing...")
        print("=" * 60)

        # Check for Anthropic API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not found in environment")
            print("   Please add it to your .env file")
            print("   Claire will have limited functionality")
            return

        try:
            # Import LangChain components (LangChain 1.x uses langgraph)
            from langchain_anthropic import ChatAnthropic
            from langgraph.prebuilt import create_react_agent

            # Import our custom tools
            from sympy_tools import CLAIRE_TOOLS

            # Initialize Claude Sonnet
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                temperature=0.7,
                max_tokens=1024
            )
            print("✅ AI Brain: READY (Claude Sonnet)")

            # Set up tools
            self.tools = CLAIRE_TOOLS
            print(f"✅ Math Tools: READY ({len(self.tools)} tools loaded)")

            # Create ReAct agent using langgraph (LangChain 1.x)
            # The system prompt is passed via the 'prompt' parameter
            self.executor = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=self.SYSTEM_PROMPT
            )
            print("✅ ReAct Agent: READY")

        except ImportError as e:
            print(f"⚠️  Missing dependency: {e}")
            print("   Run: pip install -r requirements.txt")
        except Exception as e:
            print(f"❌ Agent initialization error: {e}")

        print("=" * 60)

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through ReAct agent.

        Args:
            user_input: The user's question or command

        Returns:
            Dict with keys:
            - 'output': Final response string
            - 'intermediate_steps': List of (AgentAction, observation) tuples
        """
        # Check system commands first
        system_response = self._check_system_commands(user_input)
        if system_response:
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": system_response})
            return {'output': system_response, 'intermediate_steps': []}

        # If agent not initialized, return error
        if not self.executor:
            error_msg = ("⚠️ Claire is not fully initialized. "
                        "Please add ANTHROPIC_API_KEY to your .env file and restart.")
            return {'output': error_msg, 'intermediate_steps': []}

        # Invoke the agent (langgraph API)
        try:
            # Add context about student level and guided mode to the query
            context_info = f"\n[Student level: {self.user_level}, Guided mode: {'ON' if self.guided_mode else 'OFF'}]"
            enhanced_input = user_input + context_info

            # Invoke using langgraph's message-based API
            from langchain_core.messages import HumanMessage

            result = self.executor.invoke({
                "messages": [HumanMessage(content=enhanced_input)]
            })

            # Extract the final response from langgraph result
            messages = result.get('messages', [])
            final_output = ""
            intermediate_steps = []

            for msg in messages:
                if hasattr(msg, 'content') and msg.content:
                    # The last AI message is the final output
                    if hasattr(msg, 'type') and msg.type == 'ai':
                        final_output = msg.content
                    # Tool messages are intermediate steps
                    if hasattr(msg, 'type') and msg.type == 'tool':
                        intermediate_steps.append(msg)

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": final_output})

            # Trim history to last 10 messages
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return {
                'output': final_output,
                'intermediate_steps': intermediate_steps
            }

        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {'output': error_msg, 'intermediate_steps': []}

    def _check_system_commands(self, user_input: str) -> Optional[str]:
        """Check and handle system commands"""
        user_input_lower = user_input.lower().strip()

        # Simple string responses
        if user_input_lower == "clear":
            self.conversation_history = []
            return "Conversation history cleared."

        if user_input_lower == "reset":
            self.conversation_history = []
            self.user_level = "beginner"
            self.guided_mode = True
            return "Agent reset to initial state."

        # Commands that call methods
        if user_input_lower == "help":
            return self._show_help()

        if user_input_lower == "examples":
            return self._show_examples()

        if user_input_lower == "capabilities":
            return self._show_capabilities()

        if user_input_lower == "status":
            return self._show_status()

        if user_input_lower == "/study":
            return self._toggle_guided_mode()

        # Level commands
        if user_input_lower.startswith("level "):
            level = user_input_lower.split("level ")[1].strip()
            return self._set_level(level)

        return None

    def _toggle_guided_mode(self) -> str:
        """Toggle guided learning mode"""
        self.guided_mode = not self.guided_mode
        if self.guided_mode:
            return """📖 **Guided Learning Mode: ON**

I'll now guide you through problems using the Socratic method instead of giving direct answers.
This approach helps you develop deeper understanding and independent problem-solving skills.

When you're ready, ask me a math question!"""
        else:
            return """📖 **Guided Learning Mode: OFF**

Switched back to direct mode. I'll provide more straightforward explanations.
Note: I'll still focus on teaching, but with more explicit guidance."""

    def _show_help(self) -> str:
        """Show help information"""
        return """**Claire Help Commands:**
- `help` - Show this help
- `examples` - Show example questions
- `capabilities` - Show what I can do
- `status` - Show system status
- `clear` - Clear conversation history
- `level [beginner|intermediate|advanced]` - Set your level
- `/study` - Toggle guided learning mode (Socratic method)

**Claire - Making Calculus Clear** ✨
Ask me anything about calculus!"""

    def _show_examples(self) -> str:
        """Show example questions"""
        return """**Example Questions:**

📐 **Derivatives:**
- What is the derivative of x^3 + 2x?
- Find d/dx of sin(x)*cos(x)
- Differentiate e^(2x)

∫ **Integrals:**
- Calculate the integral of x^2
- What is ∫sin(x)dx?
- Integrate 1/(1+x^2)

📊 **Limits:**
- Find the limit of sin(x)/x as x approaches 0
- What is lim(x→∞) of 1/x?

🔢 **Equations:**
- Solve x^2 - 5x + 6 = 0
- Find the roots of x^3 - 8

💡 **Concepts:**
- What is the chain rule?
- Explain integration by parts
- What is L'Hôpital's rule?

**Claire - Making Calculus Clear** ✨"""

    def _show_capabilities(self) -> str:
        """Show capabilities"""
        caps = []

        if self.executor:
            caps.append("✅ ReAct Agent: Active (Claude Sonnet)")
            caps.append(f"✅ Math Tools: {len(self.tools) if self.tools else 0} tools available")
            caps.append("   - calculate_derivative")
            caps.append("   - calculate_integral")
            caps.append("   - calculate_limit")
            caps.append("   - solve_equation")
            caps.append("   - simplify_expression")
        else:
            caps.append("⚠️  Agent: Not initialized (missing API key)")

        caps.append("\n**Teaching Modes:**")
        caps.append(f"📖 Guided Learning: {'ON' if self.guided_mode else 'OFF'}")
        caps.append(f"📊 Student Level: {self.user_level}")

        return "\n".join(caps)

    def _show_status(self) -> str:
        """Show system status"""
        status = [
            "**Claire System Status**",
            f"",
            f"Student Level: {self.user_level}",
            f"Guided Mode: {'ON 📖' if self.guided_mode else 'OFF'}",
            f"Conversation History: {len(self.conversation_history)} messages",
            f"",
            f"**Backend:**",
            f"AI Engine: {'Claude Sonnet ✅' if self.llm else 'Not initialized ⚠️'}",
            f"Math Tools: {len(self.tools) if self.tools else 0} loaded",
            f"ReAct Agent: {'Active ✅' if self.executor else 'Inactive ⚠️'}",
            f"",
            f"**Claire - Making Calculus Clear** ✨"
        ]
        return "\n".join(status)

    def _set_level(self, level: str) -> str:
        """Set student level"""
        if level in ["beginner", "intermediate", "advanced"]:
            self.user_level = level
            return f"✅ Student level set to: {level}"
        return "❌ Invalid level. Use: beginner, intermediate, or advanced"
