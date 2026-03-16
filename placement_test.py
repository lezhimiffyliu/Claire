"""Quick placement test generation and scoring for Claire."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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


METHOD_CHOICES = {
    "optimization": [
        "Set up an objective function, find critical points, and compare candidates.",
        "Use implicit differentiation with respect to time.",
        "Apply L'Hôpital's Rule immediately.",
        "Find an antiderivative and add +C.",
    ],
    "constrained_optimization": [
        "Use Lagrange multipliers and/or compare values on the feasible region boundary.",
        "Take a basic derivative and stop after solving f'(x)=0.",
        "Use a u-substitution integral setup.",
        "Compute a one-sided limit from the left and right.",
    ],
    "related_rates": [
        "Write the geometric relationship, differentiate with respect to time, then substitute values.",
        "Set up a Lagrange multiplier system.",
        "Convert to polar coordinates and integrate.",
        "Use the squeeze theorem.",
    ],
    "derivatives": [
        "Identify the differentiation rule(s) and compute the derivative step by step.",
        "Set up a definite integral over the interval.",
        "Optimize by checking endpoints and interior points.",
        "Solve with partial fractions.",
    ],
    "integration": [
        "Choose an integration technique such as substitution, parts, or partial fractions.",
        "Differentiate both sides with respect to time.",
        "Set up a constrained optimization system.",
        "Compare one-sided limits.",
    ],
    "limits": [
        "Classify the limit form, simplify if possible, then choose a limit rule or theorem.",
        "Set the derivative equal to zero and solve.",
        "Use integration by parts.",
        "Write an implicit relation in time and differentiate.",
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
            topic="integration",
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
            topic="integration",
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
            topic="series",
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
            topic="series",
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
            topic="constrained_optimization",
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
            topic="multivariable_integration",
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
            topic="gradient",
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
            topic="multivariable_optimization",
        ),
    ],
}


def _difficulty_rank(label: str) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(label, 1)


def build_questions_from_bank(bank, limit: int = 5) -> list[PlacementQuestion]:
    if not bank or not getattr(bank, "questions", None):
        return []

    seen_patterns = set()
    selected = []
    sorted_questions = sorted(
        bank.questions,
        key=lambda q: (_difficulty_rank(getattr(q, "difficulty", "medium")), len(q.text)),
    )

    for q in sorted_questions:
        pattern = getattr(q, "pattern", None)
        if pattern not in METHOD_CHOICES:
            continue
        if pattern in seen_patterns and len(selected) < 3:
            continue

        excerpt = q.get_formatted_text()[:400] if hasattr(q, "get_formatted_text") else q.text[:400]
        ask = "What is the best first approach to this problem?"

        selected.append(
            PlacementQuestion(
                # prompt kept as fallback plain text
                prompt=(
                    f"**{q.format_source()}**\n\n"
                    f"{excerpt}\n\n"
                    f"*{ask}*"
                ),
                choices=METHOD_CHOICES[pattern],
                correct_index=0,
                explanation=f"This problem was classified as {pattern.replace('_', ' ')}.",
                source=q.format_source(),
                difficulty=getattr(q, "difficulty", "medium"),
                topic=pattern,
                question_excerpt=excerpt,
                ask_text=ask,
            )
        )
        seen_patterns.add(pattern)

        if len(selected) >= limit:
            break

    return selected


def get_fallback_questions(calc_track: str) -> list[PlacementQuestion]:
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
