"""
SymPy Backup Engine - Fallback when Mathics is unavailable
"""
from typing import Dict, Any
import sympy as sp
from sympy import symbols, diff, integrate, limit, series, solve, Eq, simplify
from sympy.abc import x, y, z

class SymPyBackupEngine:
    """SymPy backup mathematical engine"""
    
    def __init__(self):
        self.x, self.y, self.z = symbols('x y z')
        self.is_available = True
    
    def evaluate(self, expression: str) -> Dict[str, Any]:
        """Calculate using SymPy"""
        try:
            safe_dict = {
                'x': self.x, 'y': self.y, 'z': self.z,
                'diff': diff, 'integrate': integrate, 'limit': limit,
                'solve': solve, 'Eq': Eq, 'simplify': simplify,
                'series': series,
                'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
                'pi': sp.pi, 'E': sp.E, 'oo': sp.oo
            }
            
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return {
                'success': True,
                'result': str(result),
                'latex': sp.latex(result) if hasattr(result, '__len__') else '',
                'engine': 'SymPy',
                'is_exact': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'engine': 'SymPy'
            }