"""
Claire SymPy Tools - LangChain tool wrappers for symbolic mathematics
"""
import re
from langchain_core.tools import tool
import sympy as sp
from sympy import symbols, diff, integrate, limit, solve, simplify, series, Eq
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Define symbolic variables
x, y, z = symbols('x y z')

# Safe namespace for expression parsing
SAFE_NAMESPACE = {
    'x': x, 'y': y, 'z': z,
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'sec': sp.sec, 'csc': sp.csc, 'cot': sp.cot,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
    'exp': sp.exp, 'log': sp.log, 'ln': sp.log,
    'sqrt': sp.sqrt, 'abs': sp.Abs,
    'pi': sp.pi, 'e': sp.E, 'E': sp.E,
    'oo': sp.oo, 'inf': sp.oo,
}


def parse_expression(expr_str: str) -> sp.Expr:
    """
    Parse a string expression into a SymPy expression.
    Handles common notations like ^ for exponentiation.
    """
    # Clean up the expression
    expr_str = expr_str.strip()

    # Convert common notations
    expr_str = expr_str.replace('^', '**')
    expr_str = expr_str.replace('ln(', 'log(')

    # Handle implicit multiplication (e.g., 2x -> 2*x)
    transformations = standard_transformations + (implicit_multiplication_application,)

    try:
        return parse_expr(expr_str, local_dict=SAFE_NAMESPACE, transformations=transformations)
    except Exception:
        # Fallback to eval with safe namespace
        return eval(expr_str, {"__builtins__": {}}, SAFE_NAMESPACE)


@tool
def calculate_derivative(expression: str, variable: str = "x", order: int = 1) -> str:
    """
    Calculate the derivative of a mathematical expression.

    Use this tool when the student asks to:
    - Find the derivative of a function
    - Differentiate an expression
    - Calculate d/dx, f'(x), or dy/dx
    - Apply differentiation rules (power rule, chain rule, product rule, etc.)

    Args:
        expression: The mathematical expression to differentiate (e.g., "x^3 + 2*x", "sin(x)*cos(x)")
        variable: The variable to differentiate with respect to (default: "x")
        order: The order of derivative (1 for first derivative, 2 for second, etc.)

    Returns:
        The derivative as a string, including both the symbolic result and LaTeX format.
    """
    try:
        expr = parse_expression(expression)
        var = symbols(variable)
        result = diff(expr, var, order)
        latex_result = sp.latex(result)
        return f"Result: {result}\nLaTeX: ${latex_result}$"
    except Exception as e:
        return f"Error calculating derivative: {str(e)}. Please check the expression format."


@tool
def calculate_integral(expression: str, variable: str = "x", lower_bound: str = None, upper_bound: str = None) -> str:
    """
    Calculate the integral (antiderivative) of a mathematical expression.

    Use this tool when the student asks to:
    - Find the integral of a function
    - Integrate an expression
    - Calculate the antiderivative
    - Find the area under a curve (definite integral)
    - Apply integration techniques (substitution, parts, etc.)

    Args:
        expression: The mathematical expression to integrate (e.g., "x^2", "sin(x)")
        variable: The variable of integration (default: "x")
        lower_bound: Lower bound for definite integral (optional, e.g., "0")
        upper_bound: Upper bound for definite integral (optional, e.g., "pi")

    Returns:
        The integral result. For indefinite integrals, remember to mention "+ C" (constant of integration).
    """
    try:
        expr = parse_expression(expression)
        var = symbols(variable)

        if lower_bound is not None and upper_bound is not None:
            # Definite integral
            lower = parse_expression(lower_bound)
            upper = parse_expression(upper_bound)
            result = integrate(expr, (var, lower, upper))
            latex_result = sp.latex(result)
            return f"Definite integral from {lower_bound} to {upper_bound}:\nResult: {result}\nLaTeX: ${latex_result}$"
        else:
            # Indefinite integral
            result = integrate(expr, var)
            latex_result = sp.latex(result)
            return f"Indefinite integral:\nResult: {result} + C\nLaTeX: ${latex_result} + C$\n(Don't forget the constant of integration!)"
    except Exception as e:
        return f"Error calculating integral: {str(e)}. Please check the expression format."


@tool
def calculate_limit(expression: str, variable: str, approaching: str, direction: str = None) -> str:
    """
    Calculate the limit of an expression as a variable approaches a value.

    Use this tool when the student asks about:
    - Limit of a function as x approaches a value
    - One-sided limits (from left or right)
    - Limits at infinity
    - L'Hopital's rule applications
    - Continuity analysis

    Args:
        expression: The mathematical expression (e.g., "sin(x)/x", "(x^2-1)/(x-1)")
        variable: The variable in the limit (e.g., "x")
        approaching: The value the variable approaches (e.g., "0", "oo" for infinity, "-oo")
        direction: Optional. "+" for right-hand limit, "-" for left-hand limit

    Returns:
        The limit value as a string.
    """
    try:
        expr = parse_expression(expression)
        var = symbols(variable)

        # Parse the approaching value
        if approaching in ['oo', 'inf', 'infinity']:
            approach_val = sp.oo
        elif approaching in ['-oo', '-inf', '-infinity']:
            approach_val = -sp.oo
        else:
            approach_val = parse_expression(approaching)

        # Calculate limit with optional direction
        if direction == '+':
            result = limit(expr, var, approach_val, '+')
            dir_str = "from the right (x → {}⁺)".format(approaching)
        elif direction == '-':
            result = limit(expr, var, approach_val, '-')
            dir_str = "from the left (x → {}⁻)".format(approaching)
        else:
            result = limit(expr, var, approach_val)
            dir_str = "(x → {})".format(approaching)

        latex_result = sp.latex(result)
        return f"Limit {dir_str}:\nResult: {result}\nLaTeX: ${latex_result}$"
    except Exception as e:
        return f"Error calculating limit: {str(e)}. Please check the expression format."


@tool
def solve_equation(equation: str, variable: str = "x") -> str:
    """
    Solve an equation or find the roots of an expression.

    Use this tool when the student asks to:
    - Solve an equation for a variable
    - Find roots or zeros of a function
    - Find where a function equals zero
    - Solve polynomial equations
    - Find critical points (when combined with derivative)

    Args:
        equation: The equation to solve. Can be in form "expr = value" or just "expr" (assumes = 0)
        variable: The variable to solve for (default: "x")

    Returns:
        The solution(s) as a string.
    """
    try:
        var = symbols(variable)

        # Check if equation contains '='
        if '=' in equation:
            parts = equation.split('=')
            lhs = parse_expression(parts[0].strip())
            rhs = parse_expression(parts[1].strip())
            eq = Eq(lhs, rhs)
            result = solve(eq, var)
        else:
            expr = parse_expression(equation)
            result = solve(expr, var)

        if isinstance(result, list):
            if len(result) == 0:
                return "No solutions found in the real numbers."
            elif len(result) == 1:
                latex_result = sp.latex(result[0])
                return f"Solution: {variable} = {result[0]}\nLaTeX: ${variable} = {latex_result}$"
            else:
                solutions = [f"{variable} = {sol}" for sol in result]
                latex_solutions = [f"${variable} = {sp.latex(sol)}$" for sol in result]
                return f"Solutions:\n" + "\n".join(solutions) + "\n\nLaTeX:\n" + "\n".join(latex_solutions)
        else:
            return f"Solution: {result}"
    except Exception as e:
        return f"Error solving equation: {str(e)}. Please check the equation format."


@tool
def simplify_expression(expression: str) -> str:
    """
    Simplify a mathematical expression.

    Use this tool to:
    - Simplify complex algebraic expressions
    - Reduce fractions
    - Combine like terms
    - Apply trigonometric identities
    - Factor or expand expressions

    Args:
        expression: The expression to simplify (e.g., "(x^2-1)/(x-1)", "sin(x)^2 + cos(x)^2")

    Returns:
        The simplified expression.
    """
    try:
        expr = parse_expression(expression)
        result = simplify(expr)
        latex_result = sp.latex(result)
        return f"Simplified result: {result}\nLaTeX: ${latex_result}$"
    except Exception as e:
        return f"Error simplifying expression: {str(e)}. Please check the expression format."


# Export all tools as a list for easy import
CLAIRE_TOOLS = [
    calculate_derivative,
    calculate_integral,
    calculate_limit,
    solve_equation,
    simplify_expression,
]
