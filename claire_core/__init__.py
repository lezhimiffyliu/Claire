"""
claire_core — the canonical, tested agent spine for Claire.

Public API. Import from here rather than reaching into submodules:

    from claire_core import (
        Problem, StudentAttempt, TutorAgent, run_tutor_turn,
        InMemoryAttemptStore, InMemoryProfileStore, InMemoryTeachingStateStore,
    )

See claire_core/README.md for the architecture, state machine, and roadmap.
"""
from .agent import StubTutorAgent, TutorAgent, TutorAgentProtocol
from .classify import classify_math_error, coarse_bucket
from .loop import (
    TeachingTurnResult,
    TutorTurnResult,
    run_teaching_turn,
    run_tutor_turn,
)
from .persistence import (
    AttemptStore,
    InMemoryAttemptStore,
    InMemoryProfileStore,
    InMemoryTeachingStateStore,
    NullAttemptStore,
    NullProfileStore,
    NullTeachingStateStore,
    ProfileStore,
    TeachingStateStore,
)
from .state import (
    EvidenceRecord,
    Grade,
    GradeStatus,
    HintLevel,
    MisconceptionType,
    Problem,
    ProblemPhase,
    StudentAttempt,
    TeachingDecision,
    TeachingState,
    ToolName,
    ToolRequest,
    TranscriptEntry,
    TutorAction,
    allowed_actions,
    default_decision_for,
    enforce,
    next_hint_level,
)

__all__ = [
    # state
    "Problem",
    "StudentAttempt",
    "Grade",
    "GradeStatus",
    "TeachingDecision",
    "TeachingState",
    "ToolName",
    "ToolRequest",
    "EvidenceRecord",
    "TranscriptEntry",
    "TutorAction",
    "ProblemPhase",
    "HintLevel",
    "MisconceptionType",
    "allowed_actions",
    "enforce",
    "default_decision_for",
    "next_hint_level",
    # classify
    "classify_math_error",
    "coarse_bucket",
    # agent
    "TutorAgent",
    "StubTutorAgent",
    "TutorAgentProtocol",
    # persistence
    "AttemptStore",
    "ProfileStore",
    "TeachingStateStore",
    "InMemoryAttemptStore",
    "InMemoryProfileStore",
    "InMemoryTeachingStateStore",
    "NullAttemptStore",
    "NullProfileStore",
    "NullTeachingStateStore",
    # loop
    "run_tutor_turn",
    "TutorTurnResult",
    "run_teaching_turn",
    "TeachingTurnResult",
]
