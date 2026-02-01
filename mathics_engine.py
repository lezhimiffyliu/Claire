"""
Mathics Engine - Open source implementation of Wolfram Mathematica syntax
"""
from typing import Dict, Any
import re

class MathicsEngine:
    """Mathics mathematical computation engine"""
    
    def __init__(self):
        try:
            from mathics.core.definitions import Definitions
            from mathics.core.evaluation import Evaluation
            from mathics.core.parser import parse
            
            print("🚀 Initializing Mathics Engine (Wolfram Mathematica syntax)...")
            
            self.definitions = Definitions(add_builtin=True)
            self.evaluation = Evaluation(definitions=self.definitions)
            self.is_available = True
            print("✅ Mathics Engine initialized successfully!")
            
        except ImportError as e:
            print(f"⚠️ Mathics not available: {e}")
            print("  Install with: pip install mathics")
            self.is_available = False
        except Exception as e:
            print(f"⚠️ Mathics initialization failed: {e}")
            self.is_available = False
    
    def evaluate(self, expression: str) -> Dict[str, Any]:
        """Execute Mathics/Wolfram expression"""
        if not self.is_available:
            return {
                'success': False,
                'error': 'Mathics engine not available',
                'result': None,
                'engine': 'Mathics'
            }
        
        try:
            from mathics.core.parser import parse
            expr = parse(expression, self.definitions)
            result = expr.evaluate(self.evaluation)
            result_str = str(result)
            
            return {
                'success': True,
                'result': result_str,
                'engine': 'Mathics',
                'input': expression,
                'is_exact': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'engine': 'Mathics',
                'input': expression
            }
    
    def query(self, natural_language: str) -> Dict[str, Any]:
        """Convert natural language to Mathics commands"""
        
        query_patterns = {
            r'(?:what is the |find |calculate |compute )?derivative of (.+)': 
                lambda m: f"D[{m.group(1).strip()}, x]",
            r'differentiate (.+)': 
                lambda m: f"D[{m.group(1).strip()}, x]",
            r'd/dx (.+)': 
                lambda m: f"D[{m.group(1).strip()}, x]",
            
            r'(?:what is the |find |calculate |compute )?integral of (.+)': 
                lambda m: f"Integrate[{m.group(1).strip()}, x]",
            r'integrate (.+)': 
                lambda m: f"Integrate[{m.group(1).strip()}, x]",
            r'∫(.+)dx': 
                lambda m: f"Integrate[{m.group(1).strip()}, x]",
            
            r'limit of (.+) as x->(.+)': 
                lambda m: f"Limit[{m.group(1).strip()}, x -> {m.group(2).strip()}]",
            r'lim_\{x→(.+)\} (.+)': 
                lambda m: f"Limit[{m.group(2).strip()}, x -> {m.group(1).strip()}]",
            
            r'solve (.+)': 
                lambda m: f"Solve[{m.group(1).strip()}, x]",
            r'find roots of (.+)': 
                lambda m: f"Solve[{m.group(1).strip()} == 0, x]",
            
            r'taylor series of (.+) at x=(.+)': 
                lambda m: f"Series[{m.group(1).strip()}, {{x, {m.group(2).strip()}, 5}}]",
            
            r'evaluate (.+)': 
                lambda m: f"N[{m.group(1).strip()}]",
            r'numerical value of (.+)': 
                lambda m: f"N[{m.group(1).strip()}]",
        }
        
        for pattern, converter in query_patterns.items():
            match = re.search(pattern, natural_language, re.IGNORECASE)
            if match:
                mathics_command = converter(match)
                print(f"🔧 Converted to Mathics: {mathics_command}")
                return self.evaluate(mathics_command)
        
        return self.evaluate(natural_language)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get engine capabilities"""
        capabilities = {
            'engine': 'Mathics',
            'available': self.is_available,
            'features': [
                'Symbolic computation (like Mathematica)',
                'Calculus: derivatives, integrals, limits',
                'Algebra: equation solving, polynomial operations',
                'Linear algebra: matrices, vectors',
                'Series expansions',
                'Plotting (basic)',
                'Exact and numerical results'
            ],
            'syntax_examples': [
                "D[Sin[x], x]  # derivative",
                "Integrate[x^2, x]  # integral",
                "Limit[Sin[x]/x, x -> 0]  # limit",
                "Solve[x^2 - 4 == 0, x]  # solve equation",
                "Series[Exp[x], {x, 0, 5}]  # Taylor series"
            ]
        }
        return capabilities