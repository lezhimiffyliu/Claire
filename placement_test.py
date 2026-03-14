"""Quick placement test generation and scoring for Claire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PlacementQuestion:
    prompt: str
    choices: list[str]
    correct_index: int
    explanation: str
    source: str
    difficulty: str


@dataclass
class PlacementResult:
    level: str
    title: str
    summary: str
    score: int
    total: int


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
            prompt="You are given f(x)=x^3-3x+1. What is the best first step if the goal is to find local maxima and minima?",
            choices=[
                "Differentiate f(x) and solve f'(x)=0.",
                "Take a definite integral from 0 to 1.",
                "Apply L'Hôpital's Rule.",
                "Use implicit differentiation with respect to time.",
            ],
            correct_index=0,
            explanation="Optimization in Calc I usually starts by differentiating and locating critical points.",
            source="Calc I quick check",
            difficulty="easy",
        ),
        PlacementQuestion(
            prompt="A ladder slides down a wall. Which idea should you use first?",
            choices=METHOD_CHOICES["related_rates"],
            correct_index=0,
            explanation="Related-rates problems start by expressing the geometry, then differentiating with respect to time.",
            source="Calc I quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="For ∫ x e^x dx, what is the most natural method?",
            choices=[
                "Integration by parts.",
                "Lagrange multipliers.",
                "Second derivative test.",
                "Squeeze theorem.",
            ],
            correct_index=0,
            explanation="This is a classic integration-by-parts setup.",
            source="Calc I quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="If lim(x→0) sin(x)/x appears, what should you recognize first?",
            choices=[
                "A standard limit / limit rule pattern.",
                "A constrained optimization problem.",
                "A related-rates setup.",
                "A partial fractions setup.",
            ],
            correct_index=0,
            explanation="Students should recognize this as a standard limit pattern before doing computation.",
            source="Calc I quick check",
            difficulty="easy",
        ),
        PlacementQuestion(
            prompt="A question asks for the absolute maximum on a closed interval. What must you check?",
            choices=[
                "Interior critical points and endpoints.",
                "Only the points where f'(x)=0.",
                "Only the endpoints.",
                "Only the antiderivative.",
            ],
            correct_index=0,
            explanation="Absolute extrema on a closed interval require both endpoints and interior critical points.",
            source="Calc I quick check",
            difficulty="medium",
        ),
    ],
    "calc_ii": [
        PlacementQuestion(
            prompt="For ∫ x ln(x) dx, which method is the best starting point?",
            choices=[
                "Integration by parts.",
                "L'Hôpital's Rule.",
                "Implicit differentiation.",
                "Lagrange multipliers.",
            ],
            correct_index=0,
            explanation="Integration by parts is the usual opening move for x·ln(x).",
            source="Calc II quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="When a series problem asks whether Σ a_n converges, what should you do first?",
            choices=[
                "Identify the series type or a likely convergence test.",
                "Take a derivative.",
                "Set up a Lagrange multiplier equation.",
                "Convert to polar coordinates.",
            ],
            correct_index=0,
            explanation="Series questions are largely about choosing the right convergence test.",
            source="Calc II quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="A volume problem gives a region and an axis of rotation. What is the first strategic step?",
            choices=[
                "Choose a volume method such as washers or shells and set up the radius carefully.",
                "Use L'Hôpital's Rule.",
                "Differentiate with respect to time.",
                "Check left- and right-hand limits.",
            ],
            correct_index=0,
            explanation="Volume questions hinge on choosing the right geometric setup.",
            source="Calc II quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="If a power series is given, what is often the most important thing to determine first?",
            choices=[
                "Its interval/radius of convergence.",
                "Its constrained maximum.",
                "A related-rates equation.",
                "A derivative using the quotient rule.",
            ],
            correct_index=0,
            explanation="For power series, convergence behavior is usually the first target.",
            source="Calc II quick check",
            difficulty="hard",
        ),
        PlacementQuestion(
            prompt="For an improper integral, what should you recognize before computing?",
            choices=[
                "Where the improper behavior comes from and whether a limit is required.",
                "That it must use shells.",
                "That it is automatically convergent.",
                "That it is a derivatives problem.",
            ],
            correct_index=0,
            explanation="Improper integrals are fundamentally limit problems wrapped inside integration.",
            source="Calc II quick check",
            difficulty="medium",
        ),
    ],
    "calc_iii": [
        PlacementQuestion(
            prompt="A problem asks for extrema of f(x,y) on a closed bounded region. What should you plan to check?",
            choices=[
                "Interior critical points and the boundary.",
                "Only a single partial derivative.",
                "Only a double integral.",
                "Only one-sided limits.",
            ],
            correct_index=0,
            explanation="Closed-region extrema in multivariable calculus require interior and boundary analysis.",
            source="Calc III quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="If the problem says maximize f(x,y) subject to g(x,y)=c, what method should you recognize?",
            choices=METHOD_CHOICES["constrained_optimization"],
            correct_index=0,
            explanation="Equality constraints in Calc III usually signal Lagrange multipliers.",
            source="Calc III quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="For a double integral over a circular region, what is often a smart strategic move?",
            choices=[
                "Consider polar coordinates if the geometry becomes simpler.",
                "Use related rates.",
                "Differentiate the integrand first.",
                "Apply the ratio test.",
            ],
            correct_index=0,
            explanation="Circular symmetry is a classic sign that polar coordinates may simplify the work.",
            source="Calc III quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="If a question asks for the directional derivative, what information do you need conceptually?",
            choices=[
                "The gradient and a direction vector.",
                "An interval of convergence.",
                "A shell radius.",
                "A time derivative relation.",
            ],
            correct_index=0,
            explanation="Directional derivatives come from projecting the gradient onto a direction.",
            source="Calc III quick check",
            difficulty="medium",
        ),
        PlacementQuestion(
            prompt="If a surface integral / vector-calculus question appears, what usually matters first?",
            choices=[
                "Choosing the right representation, orientation, or theorem before grinding algebra.",
                "Applying the quotient rule.",
                "Testing divergence of a series.",
                "Finding a single-variable antiderivative.",
            ],
            correct_index=0,
            explanation="In Calc III, setup decisions often matter more than raw algebra at the start.",
            source="Calc III quick check",
            difficulty="hard",
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

        prompt = (
            f"Source: {q.format_source()}\n\n"
            f"Question excerpt:\n{q.get_formatted_text()[:350]}\n\n"
            "What is the best first approach to this problem?"
        )
        selected.append(
            PlacementQuestion(
                prompt=prompt,
                choices=METHOD_CHOICES[pattern],
                correct_index=0,
                explanation=f"This problem was classified as {pattern.replace('_', ' ')}.",
                source=q.format_source(),
                difficulty=getattr(q, "difficulty", "medium"),
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

    if total == 0:
        return PlacementResult(
            level="intermediate",
            title="Needs a baseline check",
            summary="No diagnostic data yet, so Claire will start in a balanced teaching mode.",
            score=0,
            total=0,
        )

    ratio = score / total
    if ratio <= 0.4:
        return PlacementResult(
            level="beginner",
            title="Foundations need rebuilding",
            summary="Claire should use simple language, emphasize intuition, define symbols, and slow down the step size.",
            score=score,
            total=total,
        )
    if ratio <= 0.75:
        return PlacementResult(
            level="intermediate",
            title="Has basics, but the calculus is shaky",
            summary="Claire should reinforce method choice and common traps while still explaining why each step works.",
            score=score,
            total=total,
        )
    return PlacementResult(
        level="advanced",
        title="Strong enough to focus on speed and pattern recognition",
        summary="Claire should be more concise, focus on strategy, and push the student toward timed practice and higher-yield drilling.",
        score=score,
        total=total,
    )
