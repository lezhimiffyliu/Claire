"""Quick placement test generation and scoring for Claire.

IMPORTANT: Diagnostic questions use a STATIC JSON bank with verified answers.
LLM is only used for explanations, NOT for determining correct answers.
This ensures reliable, deterministic scoring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pattern_tools import detect_fine_pattern

# Path to static diagnostic question bank
DIAGNOSTIC_BANK_PATH = Path(__file__).parent / "diagnostic_bank.json"


@dataclass
class PlacementQuestion:
    prompt: str            # Full display text (used when question_excerpt is empty)
    choices: list[str]
    correct_index: int
    explanation: str
    source: str
    difficulty: str
    topic: str = ""              # e.g. "derivatives", "integration", "limits"
    question_excerpt: str = ""   # Raw excerpt from uploaded material (if from bank)
    ask_text: str = ""           # The question stem shown below the excerpt


@dataclass
class PlacementResult:
    level: str
    title: str
    summary: str
    score: int
    total: int
    weak_topics: list[str] = field(default_factory=list)    # topics answered wrong
    strong_topics: list[str] = field(default_factory=list)  # topics answered correctly


# =============================================================================
# METHOD_CHOICES: Correct solving methods for each FINE-GRAINED pattern
#
# Each pattern has:
#   - Index 0: CORRECT method (derived from heuristics/*.md solving templates)
#   - Index 1-3: Plausible distractors (methods for different problem types)
#
# These are used in diagnostic questions where students choose the approach.
# =============================================================================

METHOD_CHOICES = {
    # -------------------------------------------------------------------------
    # MULTIVARIABLE CALCULUS
    # -------------------------------------------------------------------------
    "directional_derivative": [
        # CORRECT: From gradient concept - D_u f = ∇f · û
        "Compute the gradient ∇f and take the dot product with a unit direction vector.",
        "Set up Lagrange multipliers with the direction as a constraint.",
        "Differentiate implicitly with respect to the direction variable.",
        "Use the chain rule on f(x(t), y(t)) and set t = 0.",
    ],
    "gradient": [
        # CORRECT: ∇f = (∂f/∂x, ∂f/∂y)
        "Compute all partial derivatives and form the vector ∇f = (fₓ, fᵧ).",
        "Find the tangent plane and extract its normal vector.",
        "Use the second derivative test to find the direction.",
        "Integrate each component separately.",
    ],
    "tangent_plane": [
        # CORRECT: z - z₀ = fₓ(x₀,y₀)(x - x₀) + fᵧ(x₀,y₀)(y - y₀)
        "Compute partial derivatives at the point, then use z - z₀ = fₓ(x-x₀) + fᵧ(y-y₀).",
        "Find the gradient and set it equal to zero.",
        "Use implicit differentiation to find dz/dx and dz/dy.",
        "Set up a double integral over the tangent region.",
    ],
    "partial_derivatives": [
        # CORRECT: Differentiate with respect to one variable, holding others constant
        "Differentiate with respect to the target variable, treating all other variables as constants.",
        "Use the total derivative formula with chain rule.",
        "Compute the gradient and extract the relevant component.",
        "Set up an integral and differentiate under the integral sign.",
    ],
    "lagrange_multipliers": [
        # CORRECT: From constrained_optimization.md - ∇f = λ∇g, g = c
        "Set up ∇f = λ∇g along with the constraint equation g = c, then solve the system.",
        "Substitute the constraint into f to reduce variables, then set f' = 0.",
        "Find critical points of f ignoring the constraint, then check which satisfy g = c.",
        "Use the second derivative test on f restricted to the constraint curve.",
    ],

    # -------------------------------------------------------------------------
    # OPTIMIZATION
    # -------------------------------------------------------------------------
    "critical_points": [
        # CORRECT: From optimization.md - set f'(x) = 0
        "Set f'(x) = 0 and solve for x to find critical points.",
        "Set up Lagrange multipliers with an artificial constraint.",
        "Find where the second derivative equals zero.",
        "Evaluate f at the endpoints only.",
    ],
    "critical_points_multivariable": [
        # CORRECT: From optimization.md - ∇f = 0, then use discriminant D
        "Set ∇f = 0 to find critical points, then use D = fₓₓfᵧᵧ - (fₓᵧ)² to classify.",
        "Find where fₓₓ = 0 and fᵧᵧ = 0 separately.",
        "Use Lagrange multipliers with no constraint.",
        "Compute the directional derivative in all directions.",
    ],
    "second_derivative_test": [
        # CORRECT: From optimization.md - check f''(c) or discriminant D
        "At a critical point, compute D = fₓₓfᵧᵧ - (fₓᵧ)² and check its sign along with fₓₓ.",
        "Check if the gradient is zero at the point.",
        "Evaluate the function at nearby points to compare values.",
        "Use the mean value theorem to determine concavity.",
    ],
    "absolute_extrema": [
        # CORRECT: Closed interval method (1D)
        "Find all critical points inside the interval AND evaluate f at both endpoints, then compare.",
        "Only check where f'(x) = 0, ignoring endpoints.",
        "Only check the endpoints of the interval.",
        "Use the second derivative test at each critical point.",
    ],
    "extrema_on_bounded_region": [
        # CORRECT: Composite strategy for 2D bounded regions
        "Find interior critical points (set ∇f = 0), analyze the boundary (Lagrange multipliers if needed), then compare all candidate values.",
        "Use the second derivative test to classify each critical point, then pick the largest D value.",
        "Only use Lagrange multipliers on the boundary curve.",
        "Only find where fₓ = 0 and fᵧ = 0, ignoring the boundary.",
    ],
    "optimization": [
        # Legacy coarse pattern - general optimization
        "Find critical points by setting the derivative(s) to zero, then classify or compare values.",
        "Use implicit differentiation with respect to time.",
        "Apply L'Hôpital's Rule to find the optimum.",
        "Set up an integral and find where it's maximized.",
    ],
    "constrained_optimization": [
        # Legacy coarse pattern - use Lagrange
        "Use Lagrange multipliers: set ∇f = λ∇g and solve with the constraint g = c.",
        "Take a basic derivative and stop after solving f'(x) = 0.",
        "Use a u-substitution integral setup.",
        "Compute a one-sided limit from both directions.",
    ],

    # -------------------------------------------------------------------------
    # INTEGRATION TECHNIQUES
    # -------------------------------------------------------------------------
    "u_substitution": [
        # CORRECT: From u_substitution.md
        "Identify inner function u = g(x), compute du = g'(x)dx, rewrite integral in u, integrate, substitute back.",
        "Choose u and dv, then apply integration by parts formula.",
        "Factor the denominator and decompose into partial fractions.",
        "Use a trigonometric identity to simplify before integrating.",
    ],
    "integration_by_parts": [
        # CORRECT: From integration_by_parts.md - ∫udv = uv - ∫vdu
        "Choose u and dv using LIATE priority, then apply ∫udv = uv - ∫vdu.",
        "Let u equal the entire integrand and find du.",
        "Factor out constants and use basic antiderivative rules.",
        "Convert to partial fractions first.",
    ],
    "partial_fractions": [
        # CORRECT: From partial_fractions.md
        "Factor the denominator, decompose into partial fractions A/(x-a) + B/(x-b) + ..., then integrate each term.",
        "Use integration by parts with u = 1/denominator.",
        "Apply u-substitution with u = denominator.",
        "Use trigonometric substitution.",
    ],
    "trig_substitution": [
        # CORRECT: From trig_substitution.md
        "Match the form √(a²-x²), √(a²+x²), or √(x²-a²) to the correct trig substitution, then integrate.",
        "Use u-substitution with u equal to the expression under the radical.",
        "Apply integration by parts with the radical as dv.",
        "Factor out the constant and use a standard integral table.",
    ],
    "double_integrals": [
        # CORRECT: Thoughtful approach - understand region before computing
        "Sketch the region, interpret the bounds carefully, and decide whether reversing the order will make the integral easier.",
        "Convert to polar coordinates immediately, since double integrals are usually easier that way.",
        "Evaluate the two integrals separately without analyzing the region.",
        "Differentiate the integrand first to simplify the problem.",
    ],
    "triple_integrals": [
        # CORRECT: Similar to double_integrals.md
        "Identify the region, choose coordinate system (rectangular/cylindrical/spherical), set up limits, integrate from inside out.",
        "Always convert to spherical coordinates regardless of the region.",
        "Evaluate the outermost integral first.",
        "Reduce to a double integral by integrating symbolically.",
    ],
    "improper_integrals": [
        # CORRECT: Replace infinite limit with b, take limit as b→∞
        "Replace the infinite limit with a variable b, evaluate the definite integral, then take the limit as b→∞.",
        "Ignore the infinite bound and integrate normally.",
        "Use L'Hôpital's Rule directly on the integrand.",
        "Convert to a series and sum.",
    ],
    "integration": [
        # Legacy coarse pattern
        "Identify the integral type and choose the appropriate technique (substitution, parts, partial fractions, or trig sub).",
        "Differentiate both sides with respect to time.",
        "Set up a constrained optimization system.",
        "Compare one-sided limits.",
    ],

    # -------------------------------------------------------------------------
    # DERIVATIVES
    # -------------------------------------------------------------------------
    "chain_rule": [
        # CORRECT: From derivatives.md
        "Identify outer and inner functions, then apply d/dx[f(g(x))] = f'(g(x)) · g'(x).",
        "Use the product rule on f and g separately.",
        "Differentiate the inner function only.",
        "Use implicit differentiation treating g(x) as a constant.",
    ],
    "product_rule": [
        # CORRECT: From derivatives.md - (fg)' = f'g + fg'
        "Apply (fg)' = f'g + fg': differentiate each factor separately and combine.",
        "Differentiate the first factor and multiply by the second (ignoring the second term).",
        "Use the quotient rule by writing fg as f/(1/g).",
        "Use logarithmic differentiation for all products.",
    ],
    "quotient_rule": [
        # CORRECT: (f/g)' = (f'g - fg') / g²
        "Apply (f/g)' = (f'g - fg') / g²: differentiate top and bottom, combine per the formula.",
        "Differentiate the numerator only and divide by the original denominator.",
        "Use the product rule on f · (1/g) instead.",
        "Multiply top and bottom by g before differentiating.",
    ],
    "implicit_differentiation": [
        # CORRECT: From derivatives.md
        "Differentiate both sides with respect to x (using chain rule on y terms), then solve for dy/dx.",
        "Solve for y explicitly first, then differentiate.",
        "Differentiate with respect to y and invert the result.",
        "Use the formula dy/dx = -Fₓ/Fᵧ without differentiating.",
    ],
    "derivatives": [
        # Legacy coarse pattern
        "Identify the differentiation rule(s) needed and compute the derivative step by step.",
        "Set up a definite integral over the interval.",
        "Optimize by checking endpoints and interior points.",
        "Solve with partial fractions.",
    ],

    # -------------------------------------------------------------------------
    # RELATED RATES
    # -------------------------------------------------------------------------
    "related_rates": [
        # CORRECT: From related_rates.md
        "Write the geometric relationship, differentiate implicitly with respect to t, then substitute known values.",
        "Set up a Lagrange multiplier system with time as the constraint.",
        "Convert to polar coordinates and differentiate.",
        "Use the squeeze theorem on the rate equation.",
    ],

    # -------------------------------------------------------------------------
    # LIMITS
    # -------------------------------------------------------------------------
    "limits": [
        # CORRECT: From limits.md
        "Try direct substitution; if indeterminate, factor/simplify or apply L'Hôpital's Rule.",
        "Set the derivative equal to zero and solve.",
        "Use integration by parts on the limit expression.",
        "Write an implicit relation and differentiate.",
    ],
    "lhopitals_rule": [
        # CORRECT: From limits.md - must verify 0/0 or ∞/∞ first
        "Verify the form is 0/0 or ∞/∞, then differentiate numerator and denominator separately.",
        "Apply the quotient rule to the fraction inside the limit.",
        "Factor out the highest power and cancel before differentiating.",
        "Use L'Hôpital's Rule even for non-indeterminate forms.",
    ],

    # -------------------------------------------------------------------------
    # SERIES
    # -------------------------------------------------------------------------
    "taylor_series": [
        # CORRECT: Compute derivatives at center, use formula
        "Compute derivatives f(a), f'(a), f''(a), ... and use the Taylor formula Σ f⁽ⁿ⁾(a)/n! · (x-a)ⁿ.",
        "Integrate the function and expand the result.",
        "Use L'Hôpital's Rule to find each coefficient.",
        "Convert to polar coordinates before expanding.",
    ],
    "power_series": [
        # CORRECT: Use ratio test for radius
        "Use the Ratio Test: R = lim|aₙ/aₙ₊₁| to find the radius of convergence.",
        "Differentiate the series term by term to find convergence.",
        "Set the nth term equal to zero and solve for x.",
        "Compare to a geometric series regardless of form.",
    ],
    "convergence_tests": [
        # CORRECT: Choose appropriate test
        "Identify the series form, then apply the appropriate test (Ratio, Root, Comparison, Integral, or Alternating Series).",
        "Always use the Ratio Test regardless of series type.",
        "Check if the limit of aₙ is zero; if so, the series converges.",
        "Integrate the general term to determine convergence.",
    ],
}

FALLBACK_BANK = {
    "calc_i": [
        PlacementQuestion(
            prompt="What is $\\frac{d}{dx}\\bigl[x^3 - 4x + 7\\bigr]$?",
            choices=[
                "$3x^2 - 4$",
                "$3x^2 - 4x$",
                "$x^2 - 4$",
                "$3x^2 - 4 + C$",
            ],
            correct_index=0,
            explanation="Power rule: d/dx[xⁿ] = nxⁿ⁻¹. The constant 7 vanishes.",
            source="Calc I diagnostic",
            difficulty="easy",
            topic="derivatives",
        ),
        PlacementQuestion(
            prompt=(
                "At $x = a$ you find $f'(a) = 0$ and $f''(a) > 0$. "
                "What can you conclude about $x = a$?"
            ),
            choices=[
                "Local minimum at $x = a$",
                "Local maximum at $x = a$",
                "Inflection point at $x = a$",
                "The second derivative test is inconclusive",
            ],
            correct_index=0,
            explanation="Second derivative test: f''(a) > 0 means the curve is concave up → local minimum.",
            source="Calc I diagnostic",
            difficulty="medium",
            topic="optimization",
        ),
        PlacementQuestion(
            prompt="Evaluate $\\displaystyle\\lim_{x \\to 0} \\frac{\\sin(3x)}{x}$.",
            choices=["$3$", "$1$", "$0$", "Does not exist"],
            correct_index=0,
            explanation="Standard limit: lim(x→0) sin(kx)/x = k. Here k = 3.",
            source="Calc I diagnostic",
            difficulty="easy",
            topic="limits",
        ),
        PlacementQuestion(
            prompt="For $\\displaystyle\\int x e^x\\,dx$, which technique works best?",
            choices=[
                "Integration by parts ($u = x$, $dv = e^x\\,dx$)",
                "$u$-substitution with $u = xe^x$",
                "Partial fractions",
                "Trigonometric substitution",
            ],
            correct_index=0,
            explanation="x·eˣ is a polynomial × exponential — the classic integration-by-parts setup.",
            source="Calc I diagnostic",
            difficulty="medium",
            topic="integration_by_parts",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt=(
                "To find the **absolute maximum** of $f(x) = x^2 - 4x$ on $[0,\\,5]$, "
                "what do you need to check?"
            ),
            choices=[
                "Critical points inside $(0,5)$ **and** both endpoints $x=0$, $x=5$",
                "Only where $f'(x) = 0$",
                "Only the endpoints $x = 0$ and $x = 5$",
                "Where $f''(x) = 0$ (inflection points)",
            ],
            correct_index=0,
            explanation="Absolute extrema on a closed interval: check interior critical points AND endpoints (Closed Interval Method).",
            source="Calc I diagnostic",
            difficulty="medium",
            topic="optimization",
        ),
    ],
    "calc_ii": [
        PlacementQuestion(
            prompt="For $\\displaystyle\\int x\\ln(x)\\,dx$, which technique fits best?",
            choices=[
                "Integration by parts ($u = \\ln x$, $dv = x\\,dx$)",
                "$u$-substitution with $u = \\ln x$",
                "Partial fractions",
                "Trigonometric substitution",
            ],
            correct_index=0,
            explanation="ln(x) lacks a simple antiderivative on its own; integration by parts handles log × polynomial products.",
            source="Calc II diagnostic",
            difficulty="easy",
            topic="integration_by_parts",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt="Which test would you apply first to $\\displaystyle\\sum_{n=1}^{\\infty} \\frac{n}{2^n}$?",
            choices=[
                "Ratio Test: check $\\lim_{n\\to\\infty} |a_{n+1}/a_n|$",
                "Integral Test",
                "Divergence Test: check $\\lim_{n\\to\\infty} a_n$",
                "Alternating Series Test",
            ],
            correct_index=0,
            explanation="Exponential denominator — Ratio Test gives a clean limit less than 1, confirming convergence.",
            source="Calc II diagnostic",
            difficulty="medium",
            topic="convergence_tests",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt=(
                "Why is $\\displaystyle\\int_1^{\\infty}\\frac{1}{x^2}\\,dx$ called an improper integral, "
                "and how do you handle it?"
            ),
            choices=[
                "The upper limit is $\\infty$; replace it with $b$ and take $\\lim_{b\\to\\infty}$",
                "The integrand blows up at $x=0$; split there",
                "The function is not continuous, so you cannot integrate it",
                "Apply L'Hôpital's rule directly on $1/x^2$",
            ],
            correct_index=0,
            explanation="Infinite upper bound → improper integral. Evaluate as a limit.",
            source="Calc II diagnostic",
            difficulty="medium",
            topic="improper_integrals",
        ),
        PlacementQuestion(
            prompt=(
                "To find the volume when $y = \\sqrt{x}$ on $[0,4]$ is rotated around "
                "the $x$-axis, which formula applies?"
            ),
            choices=[
                "$V = \\pi\\displaystyle\\int_0^4 x\\,dx$ (disk method: $[\\sqrt{x}]^2 = x$)",
                "$V = 2\\pi\\displaystyle\\int_0^4 x\\sqrt{x}\\,dx$ (shells about $y$-axis)",
                "$V = \\displaystyle\\int_0^4 \\sqrt{x}\\,dx$",
                "$V = \\pi(\\sqrt{4})^2 \\cdot 4$",
            ],
            correct_index=0,
            explanation="Rotate around x-axis → disk method: V = π∫[f(x)]² dx.",
            source="Calc II diagnostic",
            difficulty="medium",
            topic="volume",
        ),
        PlacementQuestion(
            prompt=(
                "For $\\displaystyle\\sum_{n=0}^{\\infty}\\frac{x^n}{n!}$, "
                "what is the radius of convergence $R$?"
            ),
            choices=[
                "$R = \\infty$ (converges for all $x$)",
                "$R = 1$",
                "$R = 0$",
                "$R = e$",
            ],
            correct_index=0,
            explanation="This is the Taylor series for eˣ — it converges everywhere, so R = ∞.",
            source="Calc II diagnostic",
            difficulty="hard",
            topic="power_series",  # Fine-grained topic
        ),
    ],
    "calc_iii": [
        PlacementQuestion(
            prompt="Compute $\\dfrac{\\partial}{\\partial x}\\bigl[x^2 y + e^y\\bigr]$.",
            choices=[
                "$2xy$",
                "$2xy + e^y$",
                "$x^2 + ye^y$",
                "$2x + e^y$",
            ],
            correct_index=0,
            explanation="Treat y as constant: ∂/∂x[x²y] = 2xy, ∂/∂x[eʸ] = 0.",
            source="Calc III diagnostic",
            difficulty="easy",
            topic="partial_derivatives",
        ),
        PlacementQuestion(
            prompt=(
                "To maximize $f(x,y)$ subject to $g(x,y) = 0$, "
                "what is the standard Calc III method?"
            ),
            choices=[
                "Lagrange multipliers: solve $\\nabla f = \\lambda\\,\\nabla g$",
                "Set $f_x = 0$ and $f_y = 0$, ignoring the constraint",
                "Substitute the constraint and reduce to one variable only",
                "Apply the second derivative test to $f$ alone",
            ],
            correct_index=0,
            explanation="Equality constraints in Calc III signal Lagrange multipliers.",
            source="Calc III diagnostic",
            difficulty="medium",
            topic="lagrange_multipliers",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt=(
                "You need $\\iint_D f(x,y)\\,dA$ where $D: x^2+y^2\\le 4$. "
                "Which coordinate system is usually best?"
            ),
            choices=[
                "Polar coordinates ($x = r\\cos\\theta$, $y = r\\sin\\theta$, $dA = r\\,dr\\,d\\theta$)",
                "Cartesian — it always works fine",
                "Cylindrical (that's only for 3-D)",
                "Spherical coordinates",
            ],
            correct_index=0,
            explanation="Circular region → polar coordinates simplify both the boundary and the integrand.",
            source="Calc III diagnostic",
            difficulty="medium",
            topic="double_integrals",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt=(
                "The directional derivative of $f$ in direction $\\hat{u}$ equals "
                "$D_{\\hat{u}}f = \\nabla f \\cdot \\hat{u}$. What does this measure?"
            ),
            choices=[
                "The rate of change of $f$ as you move in direction $\\hat{u}$",
                "The maximum value of $f$ along $\\hat{u}$",
                "The surface area of $z = f(x,y)$ in direction $\\hat{u}$",
                "The curvature of $f$ along $\\hat{u}$",
            ],
            correct_index=0,
            explanation="Directional derivative = how fast f changes as you walk in direction û.",
            source="Calc III diagnostic",
            difficulty="medium",
            topic="directional_derivative",  # Fine-grained topic
        ),
        PlacementQuestion(
            prompt=(
                "Finding extrema of $f(x,y) = x^2+y^2-xy$ on the closed triangle "
                "$x\\ge 0,\\; y\\ge 0,\\; x+y\\le 2$. What must you check?"
            ),
            choices=[
                "Interior critical points ($f_x = f_y = 0$) **and** values on all three boundary edges",
                "Only where $f_x = 0$",
                "Only the three corner vertices",
                "Only the interior — boundaries don't matter for smooth functions",
            ],
            correct_index=0,
            explanation="Closed bounded region: check interior critical points AND all boundary segments.",
            source="Calc III diagnostic",
            difficulty="hard",
            topic="absolute_extrema",  # Fine-grained topic
        ),
    ],
}


def _difficulty_rank(label: str) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(label, 1)


def _is_readable_question(text: str) -> bool:
    """
    Return True if a question excerpt has enough readable English content
    to be used in the placement test.

    Filters out garbled PDF extractions where most of the text is raw
    LaTeX/symbols with very few actual words.
    """
    import re
    # Strip dollar-sign math, backslash commands, numbers, and punctuation
    clean = re.sub(r'\$[^$]*\$', ' ', text)            # inline math
    clean = re.sub(r'\$\$[^$]*\$\$', ' ', clean)       # display math
    clean = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', ' ', clean)  # \cmd{...}
    clean = re.sub(r'\\[a-zA-Z]+', ' ', clean)          # bare \cmd
    clean = re.sub(r'[^a-zA-Z\s]', ' ', clean)          # everything non-alpha
    words = [w for w in clean.split() if len(w) >= 3]
    return len(words) >= 8


def _clean_tf_artifacts(text: str) -> str:
    """
    Remove True/False formatting artifacts from question text.

    Cleans patterns like:
    - ".T True .F False"
    - "T / F"
    - "True or False"
    - "(T) (F)"
    """
    import re

    # Patterns to remove (order matters - longer patterns first)
    cleanup_patterns = [
        r'\.T\s+True\s+\.F\s+False\.?',  # .T True .F False
        r'\.T\s+True\s*\.F\s+False\.?',
        r'\.\s*T\s+True\s+\.\s*F\s+False\.?',
        r'\bTrue\s+or\s+False\b\.?',      # True or False
        r'\bT\s*/\s*F\b',                  # T / F
        r'\(T\)\s*\(F\)',                  # (T) (F)
        r'\bTrue\s+False\b',               # True False
    ]

    result = text
    for pat in cleanup_patterns:
        result = re.sub(pat, '', result, flags=re.IGNORECASE)

    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()
    # Remove trailing punctuation if it looks orphaned
    result = re.sub(r'\s+[.?]\s*$', '', result).strip()

    return result


def _extract_existing_choices(text: str) -> tuple[str, list[str], int | None]:
    """
    Detect if a question already has multiple choice options.
    Returns (question_stem, choices, correct_index or None).

    Handles:
    - True/False questions
    - (A) (B) (C) (D) style
    - a) b) c) d) style
    - A. B. C. D. style
    """
    import re

    # Check for True/False
    tf_patterns = [
        r'\.T\s+True\s+\.F\s+False',      # .T True .F False
        r'\b(True)\s+or\s+(False)\b',
        r'\b(T)\s*/\s*(F)\b',
        r'\b(True)\b.*\b(False)\b',
    ]
    for pat in tf_patterns:
        if re.search(pat, text, re.IGNORECASE):
            # It's a True/False question - clean the stem
            clean_stem = _clean_tf_artifacts(text)
            return clean_stem, ["True", "False"], None

    # Check for lettered choices: (A), (B), (C), (D) or A), B), C), D) or A. B. C. D.
    # Pattern to find choices
    choice_patterns = [
        # (A) text (B) text ...
        r'\(([A-Ea-e])\)\s*([^(]+?)(?=\([A-Ea-e]\)|$)',
        # A) text B) text ...
        r'([A-Ea-e])\)\s*([^A-E]+?)(?=[A-Ea-e]\)|$)',
        # A. text B. text ...
        r'([A-Ea-e])\.\s*([^A-E]+?)(?=[A-Ea-e]\.|$)',
    ]

    for pat in choice_patterns:
        matches = re.findall(pat, text, re.IGNORECASE | re.DOTALL)
        if len(matches) >= 2:
            # Found choices
            choices = [m[1].strip() for m in matches]
            # Clean up choices (remove trailing punctuation, limit length)
            choices = [c[:200].strip().rstrip('.') for c in choices if c.strip()]

            if len(choices) >= 2:
                # Find the question stem (text before first choice)
                first_match = re.search(pat, text, re.IGNORECASE)
                if first_match:
                    stem = text[:first_match.start()].strip()
                else:
                    stem = text
                return stem, choices[:5], None  # Max 5 choices

    return text, [], None


def _is_simple_mcq(text: str) -> bool:
    """Check if a question is a simple multiple choice or True/False."""
    stem, choices, _ = _extract_existing_choices(text)
    return len(choices) >= 2


def _resolve_correct_index(correct_answer: str | None, choices: list[str]) -> int | None:
    """
    Convert a correct_answer string to an index in the choices list.

    Handles:
    - Letter answers: "A", "B", "C", "D" -> 0, 1, 2, 3
    - True/False: "True", "False" -> 0, 1 (assuming ["True", "False"])
    - Exact match: "2x" matches the choice containing "2x"

    Returns None if cannot resolve.
    """
    if not correct_answer or not choices:
        return None

    answer = correct_answer.strip()

    # Handle letter answers (A, B, C, D)
    if len(answer) == 1 and answer.upper() in "ABCDE":
        idx = ord(answer.upper()) - ord('A')
        if 0 <= idx < len(choices):
            return idx

    # Handle True/False
    if answer.lower() in ("true", "false"):
        for i, choice in enumerate(choices):
            if choice.lower() == answer.lower():
                return i

    # Handle exact or partial match
    answer_lower = answer.lower()
    for i, choice in enumerate(choices):
        choice_lower = choice.lower().strip()
        # Exact match
        if choice_lower == answer_lower:
            return i
        # Answer is contained in choice
        if answer_lower in choice_lower:
            return i
        # Choice is contained in answer
        if choice_lower in answer_lower:
            return i

    return None


def _has_numeric_or_value_choices(text: str) -> bool:
    """
    Check if the question has answer choices that look like computed values.

    Returns True if choices are numeric values, math expressions, or True/False.
    These questions should NOT be converted to method-choice format.
    """
    import re

    stem, choices, _ = _extract_existing_choices(text)
    if not choices:
        return False

    # Check if choices look like numeric values or math expressions
    value_like_choices = 0
    for choice in choices:
        choice_clean = choice.strip()

        # True/False
        if choice_clean.lower() in ['true', 'false']:
            value_like_choices += 1
            continue

        # Pure numbers (including negatives, decimals)
        if re.match(r'^[\d\.\-\+]+$', choice_clean):
            value_like_choices += 1
            continue

        # Fractions: 1/2, 3/4, etc.
        if re.match(r'^\d+/\d+$', choice_clean):
            value_like_choices += 1
            continue

        # LaTeX math expressions (fractions, sqrt, pi, etc.)
        if re.search(r'\\frac|\\sqrt|\\pi|\\ln|\\int|\\sum', choice_clean):
            value_like_choices += 1
            continue

        # Short math-like expressions: $3$, $\pi$, $e^2$
        if re.match(r'^\$[^$]{1,20}\$$', choice_clean):
            value_like_choices += 1
            continue

        # Common constants
        if choice_clean.lower() in ['π', 'pi', 'e', '∞', 'infinity', '0', '1', '-1']:
            value_like_choices += 1
            continue

    # If majority of choices are value-like, it's a value question
    return value_like_choices >= len(choices) / 2


def _is_suitable_for_method_choice(text: str) -> bool:
    """
    Check if a question is suitable for conversion to a METHOD_CHOICES
    "best first approach" diagnostic question.

    A question is suitable if:
    - It describes a SINGLE-TASK problem scenario
    - It's long enough to be a substantial problem
    - It does NOT have value-based answer choices
    - It is NOT a multi-part problem (a), b), c) etc.)

    A question is NOT suitable if:
    - It has answer choices that are numeric values or math expressions
    - It's a True/False statement
    - It's too short (< 100 chars)
    - It's a multi-part problem with sub-questions
    - It asks to both "sketch" and "evaluate" (task chain, not method selection)
    """
    import re

    # Too short - probably just a direct computation request
    if len(text.strip()) < 100:
        return False

    # Has value-based choices - it's asking for a specific answer, not method
    if _has_numeric_or_value_choices(text):
        return False

    text_lower = text.lower()

    # Check for True/False patterns
    if re.search(r'\.t\s+true|true\s+or\s+false|true.*false', text_lower):
        return False

    # =================================================================
    # Multi-part problems are NOT suitable for method-choice
    # They test task chains, not generic method identification
    # =================================================================

    # Check for sub-parts: a), b), c) or (a), (b), (c)
    if re.search(r'\b[a-d]\)\s', text_lower):
        return False
    if re.search(r'\([a-d]\)\s', text_lower):
        return False

    # Check for A. B. C. or A) B) C) format (uppercase sub-parts)
    if re.search(r'\b[A-D]\.\s', text):  # Case-sensitive for A. B.
        return False

    # Check for numbered steps: 1. 2. 3. or 1) 2) 3)
    if re.search(r'\b[1-3]\)\s', text_lower):
        return False
    if re.search(r'\b[1-3]\.\s+[A-Z]', text):  # "1. Find..." "2. Compute..."
        return False

    # "Sketch the region" + "evaluate" = task chain, not method question
    if "sketch the region" in text_lower and "evaluate" in text_lower:
        return False
    if "sketch the region" in text_lower and "integral" in text_lower:
        return False
    if "sketch" in text_lower and "compute" in text_lower:
        return False

    # "Describe the region and compute" pattern
    if "describe" in text_lower and "compute" in text_lower:
        return False
    if "describe" in text_lower and "evaluate" in text_lower:
        return False

    # "Consider the following ... then ..." patterns are usually multi-step
    if "consider the following" in text_lower and re.search(r'\bthen\b', text_lower):
        return False

    # "First ... then ..." explicit multi-step
    if re.search(r'\bfirst\b.*\bthen\b', text_lower):
        return False

    return True


def build_questions_from_bank(bank, limit: int = 5) -> list[PlacementQuestion]:
    """
    DEPRECATED: Do NOT use uploaded materials for scored diagnostic questions.

    This function is kept for backwards compatibility but now returns empty.
    Use get_static_diagnostic_questions() instead.

    Reason: Uploaded past-paper questions may not have reliable answers.
    Diagnostic scoring requires deterministic, verified correct answers.
    """
    # Always return empty - diagnostic should use static bank only
    return []


def load_static_diagnostic_bank() -> dict:
    """
    Load the static diagnostic question bank from JSON.

    Returns the parsed JSON with all questions, or empty dict on error.
    """
    try:
        if DIAGNOSTIC_BANK_PATH.exists():
            with open(DIAGNOSTIC_BANK_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[diagnostic] Error loading static bank: {e}")
    return {"questions": []}


def get_static_diagnostic_questions(
    calc_track: str = "calc_i",
    topics: list[str] | None = None,
    limit: int = 10
) -> list[PlacementQuestion]:
    """
    Get diagnostic questions from the static JSON bank.

    This is the PRIMARY source of diagnostic questions.
    All questions have verified, hardcoded correct answers.

    Args:
        calc_track: Which calculus level ("calc_i", "calc_ii", "calc_iii")
        topics: Optional list of topics to filter by
        limit: Maximum number of questions to return

    Returns:
        List of PlacementQuestion objects
    """
    bank = load_static_diagnostic_bank()
    questions_data = bank.get("questions", [])

    if not questions_data:
        # Fall back to hardcoded FALLBACK_BANK if JSON fails to load
        return get_fallback_questions(calc_track)

    # Filter by track
    filtered = [q for q in questions_data if q.get("track") == calc_track]

    # If no questions for this track, include all
    if not filtered:
        filtered = questions_data

    # Filter by topics if specified
    if topics:
        topic_set = set(topics)
        filtered = [q for q in filtered if q.get("topic") in topic_set] or filtered

    # Sort by difficulty: easy first, then medium, then hard
    difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
    filtered.sort(key=lambda q: difficulty_order.get(q.get("difficulty", "medium"), 1))

    # Diversify topics
    seen_topics = set()
    selected = []
    remaining = []

    for q in filtered:
        topic = q.get("topic", "")
        if topic not in seen_topics:
            selected.append(q)
            seen_topics.add(topic)
        else:
            remaining.append(q)

        if len(selected) >= limit:
            break

    # Fill remaining slots
    while len(selected) < limit and remaining:
        selected.append(remaining.pop(0))

    # Convert to PlacementQuestion objects
    result = []
    for q in selected[:limit]:
        result.append(PlacementQuestion(
            prompt=q.get("prompt", ""),
            choices=q.get("choices", []),
            correct_index=q.get("correct_index", 0),
            explanation=q.get("explanation", ""),
            source="Static diagnostic bank",
            difficulty=q.get("difficulty", "medium"),
            topic=q.get("topic", ""),
            question_excerpt="",
            ask_text=""
        ))

    return result


def get_fallback_questions(calc_track: str) -> list[PlacementQuestion]:
    """Get fallback questions from hardcoded FALLBACK_BANK (legacy)."""
    return list(FALLBACK_BANK.get(calc_track, FALLBACK_BANK["calc_i"]))


def score_placement(questions: list[PlacementQuestion], answers: list[Optional[int]]) -> PlacementResult:
    total = len(questions)
    score = sum(1 for q, a in zip(questions, answers) if a == q.correct_index)

    # Track which topics were wrong vs. correct (preserve insertion order, deduplicate)
    seen_weak: dict[str, bool] = {}
    seen_strong: dict[str, bool] = {}
    for q, a in zip(questions, answers):
        topic = q.topic or ""
        if not topic:
            continue
        if a != q.correct_index:
            seen_weak[topic] = True
        else:
            seen_strong[topic] = True

    weak_topics = list(seen_weak.keys())
    # Strong = correct AND not also wrong on a different question of the same topic
    strong_topics = [t for t in seen_strong if t not in seen_weak]

    if total == 0:
        return PlacementResult(
            level="intermediate",
            title="Needs a baseline check",
            summary="No diagnostic data yet, so Claire will start in a balanced teaching mode.",
            score=0,
            total=0,
            weak_topics=[],
            strong_topics=[],
        )

    ratio = score / total
    if ratio <= 0.4:
        return PlacementResult(
            level="beginner",
            title="Foundations need rebuilding",
            summary="Claire should use simple language, emphasize intuition, define symbols, and slow down the step size.",
            score=score,
            total=total,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
        )
    if ratio <= 0.75:
        return PlacementResult(
            level="intermediate",
            title="Has basics, but the calculus is shaky",
            summary="Claire should reinforce method choice and common traps while still explaining why each step works.",
            score=score,
            total=total,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
        )
    return PlacementResult(
        level="advanced",
        title="Strong enough to focus on speed and pattern recognition",
        summary="Claire should be more concise, focus on strategy, and push the student toward timed practice and higher-yield drilling.",
        score=score,
        total=total,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
    )
