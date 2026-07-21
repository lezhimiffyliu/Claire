"""
Offline demo of the closed adaptive loop. No API key required.

    python -m claire_core.demo

Runs two graded turns (one wrong, then correct) for the same student and prints
how the attempt is graded, how the action is enforced, and how the mastery
profile accumulates across turns.
"""
from __future__ import annotations

from claire_core import (
    InMemoryAttemptStore,
    InMemoryProfileStore,
    Problem,
    StubTutorAgent,
    StudentAttempt,
    run_tutor_turn,
)

PROBLEM = Problem(
    id="q_deriv_1",
    text="Find the derivative of x^3.",
    official_answer="3x^2",
    topic="derivatives",
    subtopic="power_rule",
    problem_type="derivative",
    course="124",
)


def _turn(label: str, answer: str, agent, attempts, profiles) -> None:
    result = run_tutor_turn(
        problem=PROBLEM,
        attempt=StudentAttempt(problem_id=PROBLEM.id, answer=answer),
        user_id="demo_user",
        workspace_id="demo_ws",
        agent=agent,
        attempt_store=attempts,
        profile_store=profiles,
    )
    profile = profiles.load("demo_user", "124")
    print(f"\n=== {label}: student answered '{answer}' ===")
    print(f"  grade      : correct={result.grade.is_correct} "
          f"uncertain={result.grade.is_uncertain} ({result.grade.verifier_type})")
    print(f"  action     : {result.decision.action.value}")
    print(f"  message    : {result.decision.message}")
    print(f"  phase      : {result.phase.value}")
    print(f"  persisted  : attempt_id={result.attempt_id[:8]}... "
          f"total_correct={profile.total_correct} total_incorrect={profile.total_incorrect}")
    print(f"  next up    : {[r.get('title') for r in result.recommendations] or '(recommender needs course data)'}")


def main() -> None:
    agent = StubTutorAgent()  # deterministic, no LLM
    attempts = InMemoryAttemptStore()
    profiles = InMemoryProfileStore()

    print("Claire agent-core demo — the loop is CLOSED (attempt -> grade -> persist -> profile -> recommend)")
    _turn("Turn 1", "2*x", agent, attempts, profiles)      # wrong
    _turn("Turn 2", "3*x**2", agent, attempts, profiles)   # correct

    print(f"\nTotal attempts persisted for demo_user: {len(attempts.all_for('demo_user'))}")


if __name__ == "__main__":
    main()
