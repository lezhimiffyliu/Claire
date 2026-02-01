"""
Calctoa AI Agent Core
Using OpenAI GPT as brain, Mathics as math engine
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from mathics_engine import MathicsEngine
from sympy_backup import SymPyBackupEngine

load_dotenv()

class CalctoaAgent:
    """Calctoa AI Agent - Calculus Teaching Assistant"""
    
    def __init__(self):
        self.ai_client = self._init_ai_client()
        self.mathics_engine = MathicsEngine()
        self.sympy_engine = SymPyBackupEngine()
        self.conversation_history = []
        self.user_level = "beginner"
        self.preferred_engine = "mathics"
        
        print("\n" + "="*60)
        print("🤖 Calctoa AI Agent Initialized")
        print("="*60)
        
        if self.mathics_engine.is_available:
            print("✅ Mathics Engine: READY (Wolfram Mathematica syntax)")
        else:
            print("⚠️  Mathics Engine: NOT AVAILABLE")
            print("   Falling back to SymPy")
        
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
        
        commands = {
            "help": self._show_help(),
            "examples": self._show_examples(),
            "capabilities": self._show_capabilities(),
            "clear": "Conversation history cleared.",
            "reset": "Agent reset to initial state.",
            "status": self._show_status(),
            "level beginner": self._set_level("beginner"),
            "level intermediate": self._set_level("intermediate"),
            "level advanced": self._set_level("advanced"),
            "engine mathics": self._set_engine("mathics"),
            "engine sympy": self._set_engine("sympy"),
        }
        
        if user_input_lower in commands:
            return commands[user_input_lower]
        
        return None
    
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
        print(f"🔧 Processing math calculation: {query}")
        
        if self.mathics_engine.is_available and self.preferred_engine in ["mathics", "auto"]:
            result = self.mathics_engine.query(query)
            
            if result['success']:
                if self.ai_client:
                    explanation = self._get_ai_explanation(query, result['result'])
                    return self._format_math_response(result, explanation)
                else:
                    return self._format_math_response(result)
            elif self.preferred_engine == "mathics":
                return f"❌ Mathics failed: {result['error']}\nTry using SymPy syntax or ask differently."
        
        try:
            sympy_expr = self._convert_to_sympy(query)
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
                    {"role": "system", "content": "You are Calctoa, an expert calculus teaching assistant."},
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
                    {"role": "system", "content": "You are an expert calculus teacher who makes complex ideas simple."},
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
                    {"role": "system", "content": "You are a patient calculus tutor who shows all working."},
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
                    {"role": "system", "content": "You are Calctoa, a calculus teaching assistant."},
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
                    {"role": "system", "content": "You are an inspiring calculus teacher."},
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
        query_lower = query.lower()
        
        conversions = {
            "derivative of": "diff",
            "integral of": "integrate",
            "limit of": "limit",
            "solve": "solve",
            "simplify": "simplify"
        }
        
        for phrase, func in conversions.items():
            if phrase in query_lower:
                expr = query_lower.split(phrase)[1].strip()
                expr = expr.replace(" as x->", ", x, ")
                expr = expr.replace(" with respect to x", "")
                return f"{func}({expr})"
        
        return query
    
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
        return """**Calctoa Help Commands:**
- `help` - Show this help
- `examples` - Show example questions
- `capabilities` - Show what I can do
- `status` - Show system status
- `clear` - Clear conversation history
- `level [beginner|intermediate|advanced]` - Set your level
- `engine [mathics|sympy]` - Choose math engine

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
- `Calculate limit of (sin x)/x as x->0`

**Mathics/Wolfram syntax:**
- `D[Sin[x], x]`
- `Integrate[x^2, x]`
- `Limit[Sin[x]/x, x -> 0]`
- `Solve[x^2 - 4 == 0, x]`"""
    
    def _show_capabilities(self) -> str:
        caps = []
        
        if self.mathics_engine.is_available:
            caps.append("✅ Mathics Engine: Wolfram Mathematica syntax")
        else:
            caps.append("❌ Mathics Engine: Not available")
        
        caps.append("✅ SymPy Engine: Symbolic mathematics")
        
        if self.ai_client:
            caps.append("✅ AI Brain: Natural language understanding")
        else:
            caps.append("⚠️  AI Brain: Limited (add API key for full power)")
        
        return "\n".join(caps)
    
    def _show_status(self) -> str:
        status = [
            f"User Level: {self.user_level}",
            f"Preferred Engine: {self.preferred_engine}",
            f"Conversation History: {len(self.conversation_history)} messages",
            f"Mathics Available: {self.mathics_engine.is_available}",
            f"AI Available: {self.ai_client is not None}"
        ]
        return "\n".join(status)
    
    def _set_level(self, level: str) -> str:
        if level in ["beginner", "intermediate", "advanced"]:
            self.user_level = level
            return f"✅ User level set to: {level}"
        return "❌ Invalid level. Use: beginner, intermediate, advanced"
    
    def _set_engine(self, engine: str) -> str:
        if engine in ["mathics", "sympy"]:
            if engine == "mathics" and not self.mathics_engine.is_available:
                return "❌ Mathics engine not available. Install with: pip install mathics"
            self.preferred_engine = engine
            return f"✅ Math engine set to: {engine}"
        return "❌ Invalid engine. Use: mathics, sympy"