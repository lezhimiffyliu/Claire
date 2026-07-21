"""
claire_core — the canonical, tested agent spine for Claire.

Public API. Import from here rather than reaching into submodules:

    from claire_core import (
        Problem, StudentAttempt, TutorAgent, run_tutor_turn,
        InMemoryAttemptStore, InMemoryProfileStore,
    )

See claire_core/README.md for the architecture, state machine, and roadmap.
"""
from .agent import StubTutorAgent, TutorAgent, TutorAgentProtocol
from .loop import TutorTurnResult, run_tutor_turn
from .persistence import (
    AttemptStore,
    InMemoryAttemptStore,
    InMemoryProfileStore,
    ProfileStore,
)
from .state import (
    Grade,
    Problem,
    SessionPhase,
    StudentAttempt,
    TeachingDecision,
    TutorAction,
    allowed_actions,
    default_decision_for,
    enforce,
    phase_after,
)

__all__ = [
    # state
    "Problem",
    "StudentAttempt",
    "Grade",
    "TeachingDecision",
    "TutorAction",
    "SessionPhase",
    "allowed_actions",
    "enforce",
    "default_decision_for",
    "phase_after",
    # agent
    "TutorAgent",
    "StubTutorAgent",
    "TutorAgentProtocol",
    # persistence
    "AttemptStore",
    "ProfileStore",
    "InMemoryAttemptStore",
    "InMemoryProfileStore",
    # loop
    "run_tutor_turn",
    "TutorTurnResult",
]
