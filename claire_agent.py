"""
Claire AI Agent Core
Using OpenAI GPT as brain, SymPy as math engine
"""
import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from sympy_backup import SymPyBackupEngine

load_dotenv()

class ClaireAgent:
    """Claire AI Agent - Making Calculus Clear"""

    # Base system prompt with LaTeX formatting instructions
    SYSTEM_PROMPT_BASE = """You are Claire, an expert calculus teaching assistant. Your name comes from "Making Calculus Clear".

CRITICAL LaTeX formatting rules - you MUST follow these exactly:
- For inline math, wrap with DOLLAR SIGNS: $x^2 + 1$
- For display equations, use DOUBLE DOLLAR SIGNS: $$\\frac{d}{dx}(x^2) = 2x$$
- NEVER use parentheses ( ) or brackets [ ] as LaTeX delimiters
- ALWAYS use $ or $$ as delimiters, nothing else
- Use LaTeX commands: \\frac{}{}, \\sqrt{}, \\int, \\lim, \\sin, \\cos, etc.

Example of CORRECT formatting:
The derivative of $f(x) = x^2$ is $f'(x) = 2x$.

For a complex equation:
$$\\frac{dy}{dx} = \\frac{1}{2\\sqrt{x}}$$"""

    def __init__(self):
        self.ai_client = self._init_ai_client()
        self.sympy_engine = SymPyBackupEngine()
        self.conversation_history = []
        self.user_level = "beginner"
        self.guided_mode = False

        print("\n" + "="*60)
        print("🤖 Claire AI Agent Initialized")
        print("="*60)
        print("✅ Math Engine: READY (SymPy)")

        if self.ai_client:
            print("✅ AI Brain: READY (OpenAI GPT)")
        else:
            print("⚠️  AI Brain: LIMITED (No API key)")
    
    def _init_ai_client(self):
        """Initialize AI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                return OpenAI(api_key=api_key)
            except ImportError:
                print("⚠️ OpenAI package not installed. Run: pip install openai")
        return None
    
    def process_query(self, user_input: str) -> str:
        """Process user input - main entry point"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        system_response = self._check_system_commands(user_input)
        if system_response:
            self.conversation_history.append({"role": "assistant", "content": system_response})
            return system_response
        
        query_type = self._analyze_query_type(user_input)
        
        if query_type == "math_calculation":
            response = self._handle_math_calculation(user_input)
        elif query_type == "concept_explanation":
            response = self._handle_concept_explanation(user_input)
        elif query_type == "problem_solving":
            response = self._handle_problem_solving(user_input)
        elif query_type == "teaching_request":
            response = self._handle_teaching_request(user_input)
        else:
            response = self._handle_general_query(user_input)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return response
    
    def _check_system_commands(self, user_input: str) -> Optional[str]:
        """Check system commands"""
        user_input_lower = user_input.lower().strip()

        # Simple string responses
        if user_input_lower == "clear":
            self.conversation_history = []
            return "Conversation history cleared."
        if user_input_lower == "reset":
            self.conversation_history = []
            self.user_level = "beginner"
            self.guided_mode = False
            return "Agent reset to initial state."

        # Commands that call methods (only call when matched)
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

Switched back to normal mode. I'll calculate and explain answers directly."""
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze query type"""
        query_lower = query.lower()
        
        math_keywords = ["calculate", "compute", "solve", "find", "evaluate", 
                        "=", "+", "-", "*", "/", "^", "**", "sin(", "cos(", "exp("]
        
        concept_keywords = ["what is", "explain", "define", "meaning of", 
                          "how does", "why is", "difference between"]
        
        teaching_keywords = ["teach me", "show me", "demonstrate", "how to",
                           "step by step", "example of", "walk me through"]
        
        if any(keyword in query_lower for keyword in math_keywords):
            return "math_calculation"
        elif any(keyword in query_lower for keyword in concept_keywords):
            return "concept_explanation"
        elif any(keyword in query_lower for keyword in teaching_keywords):
            return "teaching_request"
        elif any(word in query_lower for word in ["problem", "exercise", "question"]):
            return "problem_solving"
        else:
            return "general_query"
    
    def _handle_math_calculation(self, query: str) -> str:
        """Handle mathematical calculation"""
        # Check if guided mode is enabled
        if self.guided_mode:
            return self._handle_guided_learning(query)

        print(f"🔧 Processing math calculation: {query}")

        try:
            sympy_expr = self._convert_to_sympy(query)
            print(f"🔧 Converted to SymPy: {sympy_expr}")
            result = self.sympy_engine.evaluate(sympy_expr)

            if result['success']:
                if self.ai_client:
                    explanation = self._get_ai_explanation(query, result['result'])
                    return self._format_math_response(result, explanation)
                else:
                    return self._format_math_response(result)
            else:
                return self._ask_ai_directly(query)

        except Exception as e:
            return f"❌ Calculation error: {str(e)}\n\nPlease try rephrasing your question."
    
    def _handle_concept_explanation(self, query: str) -> str:
        """Handle concept explanation"""
        if self.ai_client:
            return self._explain_concept_with_ai(query)
        else:
            return self._explain_concept_basic(query)
    
    def _handle_problem_solving(self, query: str) -> str:
        """Handle problem solving"""
        if self.ai_client:
            return self._solve_problem_with_ai(query)
        else:
            return self._handle_math_calculation(query)
    
    def _handle_teaching_request(self, query: str) -> str:
        """Handle teaching request"""
        if self.ai_client:
            return self._teach_with_ai(query)
        else:
            return "I need AI capabilities for teaching. Please add your OpenAI API key to .env file."
    
    def _handle_general_query(self, query: str) -> str:
        """Handle general query"""
        if self.ai_client:
            return self._ask_ai_directly(query)
        else:
            return f"I understand you're asking: '{query}'\n\nFor calculus help, try:\n- 'What is a derivative?'\n- 'Calculate integral of x^2'\n- 'Solve x^2 - 4 = 0'"

    def _handle_guided_learning(self, query: str) -> str:
        """Handle math query in guided learning mode using Socratic method"""
        if not self.ai_client:
            return "⚠️ Guided learning mode requires AI capabilities. Please add your OpenAI API key to .env file."

        # Build context from conversation history for continuity
        recent_context = ""
        if len(self.conversation_history) > 1:
            recent_msgs = self.conversation_history[-4:]  # Last 2 exchanges
            recent_context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_msgs])

        prompt = f"""You are a calculus tutor using the Socratic method. A student asked a math question. Your task is to guide them to think, NOT to give the answer directly.

Student question: {query}
Student level: {self.user_level}
{f"Recent conversation context:{chr(10)}{recent_context}" if recent_context else ""}

Respond in this Guided Learning style:

1. **Acknowledge & Restate** (1 sentence)
   - Briefly affirm the student's question
   - Restate the problem in your own words

2. **Guiding Questions** (core part)
   - Ask 1-2 thought-provoking questions to help them think about the first step
   - Questions should point toward key concepts or methods
   - Examples: "Looking at this expression, what rule do you think we should apply?"
   - Or: "What does the structure of this problem remind you of?"

3. **Hint** (optional)
   - If the problem is difficult, give a small hint that doesn't reveal the answer
   - Use format: "💡 Hint: ..."

4. **Encourage**
   - End with one sentence encouraging them to try
   - Let them know they can share their thoughts and you'll continue guiding

Important:
- NEVER give the final answer or complete solution steps
- Be friendly, patient, and inspiring
- For beginner level, ask simpler and more specific questions
- For advanced level, guide toward deeper thinking
- Keep response concise, under 150 words"""

        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE + " You are skilled in Socratic teaching. Your goal is to help students discover answers themselves, not to tell them the answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            return "🎓 **Guided Learning**\n\n" + response.choices[0].message.content
        except Exception as e:
            return f"❌ AI Error: {str(e)}"
    
    def _get_ai_explanation(self, query: str, math_result: str) -> str:
        """Use AI to explain mathematical result"""
        if not self.ai_client:
            return ""
        
        prompt = f"""As a calculus teacher, explain this mathematical result:

Student's question: {query}
Mathematical result: {math_result}

Explain in a {self.user_level}-friendly way:
1. What this calculation means
2. Key steps involved
3. Important concepts to remember
4. Real-world applications (if relevant)

Keep it clear and educational."""
        
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content
        except:
            return ""
    
    def _explain_concept_with_ai(self, query: str) -> str:
        """Use AI to explain concept"""
        prompt = f"""Explain this calculus concept to a {self.user_level} student:

Question: {query}

Provide:
1. Clear definition
2. Simple analogy or example
3. Mathematical notation
4. Common applications
5. Related concepts to explore

Make it engaging and educational!"""
        
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE + " You make complex ideas simple."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Error: {str(e)}"
    
    def _solve_problem_with_ai(self, query: str) -> str:
        """Use AI to solve problem"""
        math_result = self._handle_math_calculation(query)
        
        if "Result:" in math_result:
            return math_result
        
        prompt = f"""Solve this calculus problem and explain step-by-step:

Problem: {query}

Provide a complete solution for a {self.user_level} student:
1. Understand the problem
2. Show step-by-step solution
3. Explain key concepts used
4. Verify the answer
5. Suggest similar practice problems"""
        
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE + " You are patient and show all working."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Error: {str(e)}"
    
    def _ask_ai_directly(self, query: str) -> str:
        """Ask AI directly"""
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Error: {str(e)}"
    
    def _teach_with_ai(self, query: str) -> str:
        """Use AI for teaching"""
        prompt = f"""Teach this calculus topic to a {self.user_level} student:

Topic: {query}

Structure your teaching:
1. Introduction and motivation
2. Core concepts explained simply
3. Worked examples
4. Common mistakes to avoid
5. Practice exercises
6. Summary and next steps

Make it interactive and engaging!"""
        
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_BASE + " You are inspiring and engaging."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=700
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Error: {str(e)}"
    
    def _convert_to_sympy(self, query: str) -> str:
        """Convert natural language to SymPy expression"""
        query_lower = query.lower().strip()

        # Pattern-based conversions (order matters - more specific patterns first)
        patterns = [
            # Derivatives
            (r'(?:what is the |find |calculate |compute )?derivative of (.+?)(?:\s+with respect to \w+)?$',
             lambda m: f"diff({self._clean_expr(m.group(1))}, x)"),
            (r'differentiate (.+)',
             lambda m: f"diff({self._clean_expr(m.group(1))}, x)"),
            (r'd/dx\s*(.+)',
             lambda m: f"diff({self._clean_expr(m.group(1))}, x)"),

            # Integrals
            (r'(?:what is the |find |calculate |compute )?integral of (.+?)(?:\s+dx)?$',
             lambda m: f"integrate({self._clean_expr(m.group(1))}, x)"),
            (r'integrate (.+)',
             lambda m: f"integrate({self._clean_expr(m.group(1))}, x)"),

            # Limits
            (r'limit of (.+) as x\s*(?:->|→|approaches)\s*(.+)',
             lambda m: f"limit({self._clean_expr(m.group(1))}, x, {m.group(2).strip()})"),

            # Solve
            (r'solve (.+?)(?:\s*=\s*0)?(?:\s+for \w+)?$',
             lambda m: f"solve({self._clean_expr(m.group(1))}, x)"),
            (r'find roots of (.+)',
             lambda m: f"solve({self._clean_expr(m.group(1))}, x)"),

            # Simplify
            (r'simplify (.+)',
             lambda m: f"simplify({self._clean_expr(m.group(1))})"),
        ]

        for pattern, converter in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return converter(match)

        # If no pattern matches, return cleaned query as-is
        return self._clean_expr(query)

    def _clean_expr(self, expr: str) -> str:
        """Clean and normalize math expression for SymPy"""
        expr = expr.strip()
        # Convert common notations
        expr = expr.replace('^', '**')
        expr = expr.replace('sin(', 'sin(').replace('cos(', 'cos(')
        expr = expr.replace('e^', 'exp(').rstrip() + ')' if 'e^' in expr else expr
        # Handle x squared, x cubed
        expr = re.sub(r'x\s*squared', 'x**2', expr)
        expr = re.sub(r'x\s*cubed', 'x**3', expr)
        return expr
    
    def _format_math_response(self, result: Dict[str, Any], explanation: str = "") -> str:
        """Format mathematical response"""
        response = f"🧮 **Mathematical Result** (via {result['engine']}):\n"
        response += f"```\n{result['result']}\n```\n"
        
        if explanation:
            response += f"\n📝 **Explanation**:\n{explanation}\n"
        
        return response
    
    def _explain_concept_basic(self, concept: str) -> str:
        """Basic concept explanation (without AI)"""
        concepts = {
            "derivative": """Derivative measures rate of change.
Notation: f'(x) or df/dx
Example: d/dx(x²) = 2x""",
            "integral": """Integral finds area under curve.
Notation: ∫f(x)dx
Example: ∫2x dx = x² + C""",
            "limit": """Limit is value function approaches.
Notation: lim_{x→a} f(x)
Example: lim_{x→0} sin(x)/x = 1"""
        }
        
        for key, value in concepts.items():
            if key in concept.lower():
                return value
        
        return f"I can explain: derivative, integral, limit. Ask specifically."
    
    def _show_help(self) -> str:
        return """**Claire Help Commands:**
- `help` - Show this help
- `examples` - Show example questions
- `capabilities` - Show what I can do
- `status` - Show system status
- `clear` - Clear conversation history
- `level [beginner|intermediate|advanced]` - Set your level
- `/study` - Toggle guided learning mode (Socratic method)

**Ask me anything about calculus!**"""
    
    def _show_examples(self) -> str:
        return """**Example Questions:**
- `What is a derivative?`
- `Calculate the integral of sin(x)`
- `Find the derivative of x^3 + 2x`
- `Explain the chain rule`
- `Solve x^2 - 5x + 6 = 0`
- `What is L'Hopital's rule?`
- `Teach me about integration by parts`
- `Limit of sin(x)/x as x->0`

**SymPy syntax:**
- `diff(sin(x), x)`
- `integrate(x**2, x)`
- `limit(sin(x)/x, x, 0)`
- `solve(x**2 - 4, x)`"""
    
    def _show_capabilities(self) -> str:
        caps = ["✅ SymPy Engine: Symbolic mathematics (derivatives, integrals, limits, solving)"]

        if self.ai_client:
            caps.append("✅ AI Brain: Natural language understanding")
        else:
            caps.append("⚠️  AI Brain: Limited (add API key for full power)")

        return "\n".join(caps)
    
    def _show_status(self) -> str:
        status = [
            f"User Level: {self.user_level}",
            f"Guided Mode: {'ON 📖' if self.guided_mode else 'OFF'}",
            f"Conversation History: {len(self.conversation_history)} messages",
            f"Math Engine: SymPy",
            f"AI Available: {self.ai_client is not None}"
        ]
        return "\n".join(status)
    
    def _set_level(self, level: str) -> str:
        if level in ["beginner", "intermediate", "advanced"]:
            self.user_level = level
            return f"✅ User level set to: {level}"
        return "❌ Invalid level. Use: beginner, intermediate, advanced"