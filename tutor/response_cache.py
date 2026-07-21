"""
Response-Level Cache

Caches complete tutor responses to avoid repeated LLM calls for
the same (session, problem, part, intent) combination.

Only caches low-risk intents where response can be safely reused.
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Low-risk intents that can be safely cached
# ONLY "cold start" intents where response is independent of conversation history
CACHEABLE_INTENTS = {
    "cant_start",      # "I don't know where to start" - first message only
    "how_to_start",    # "How do I begin?" - first message only
    "student_stuck",   # "I'm stuck" button - first step of current part
    "student_hint",    # "Give me a hint" button - first hint for current part
    # NOTE: first_hint removed because even first hint depends on what was just explained
    # NOTE: acknowledgment removed because follow-up depends on what Claire just said
}

# High-risk intents that should NOT be cached
# These require fresh responses based on conversation context
NON_CACHEABLE_INTENTS = {
    "acknowledgment",  # Follow-up depends on what Claire just said
    "first_hint",      # Even first hint depends on what was just explained
    "ask_hint",        # Hints are context-dependent
    "confused",        # Needs fresh explanation
    "still_confused",  # Previous explanation failed, need different approach
    "next_step",       # Depends on where student is
    "check_answer",    # Needs verification
    "attempt_answer",  # Needs evaluation
    "image_analysis",  # Unique each time
    "strategy_change", # Teaching pivot
    "ask_why",         # Context-dependent
}

# In-memory cache (simple dict, replace with Redis/SQLite for production)
_response_cache: Dict[str, Dict[str, Any]] = {}

# Cache expiry (not implemented in Phase 1, but structure supports it)
CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class CachedResponse:
    """A cached tutor response."""
    events: List[Dict[str, Any]]
    intent: str
    concept: Optional[str]
    model_used: str
    retrieval_score: float
    chunks_used: List[str]


def build_cache_key(
    session_id: str,
    problem_id: str,
    part_id: str,
    step_index: int,
    intent_or_action: str,
) -> str:
    """
    Build a deterministic cache key.

    Args:
        session_id: Session identifier
        problem_id: Problem identifier
        part_id: Part identifier (e.g., "a", "b", "0", "1")
        step_index: Current step within the part (0 = just started, 1 = after first hint, etc.)
        intent_or_action: Normalized intent or action type

    Returns:
        Cache key string
    """
    # Normalize
    session_id = str(session_id or "anon")
    problem_id = str(problem_id or "unknown")
    part_id = str(part_id or "0")
    step_index = int(step_index) if step_index is not None else 0
    intent_or_action = str(intent_or_action or "").lower().strip()

    # Build key: includes step_index to differentiate stages within same part
    raw_key = f"{session_id}:{problem_id}:{part_id}:{step_index}:{intent_or_action}"

    # Hash for consistent length
    return hashlib.sha256(raw_key.encode()).hexdigest()[:32]


def is_cacheable_intent(intent: str) -> bool:
    """Check if an intent can be cached."""
    if not intent:
        return False
    intent_lower = intent.lower().strip()

    # Explicit non-cacheable check first
    if intent_lower in NON_CACHEABLE_INTENTS:
        return False

    # Check cacheable list
    return intent_lower in CACHEABLE_INTENTS


def get_cached_response(cache_key: str) -> Optional[CachedResponse]:
    """
    Get a cached response if it exists.

    Args:
        cache_key: The cache key

    Returns:
        CachedResponse if found, None otherwise
    """
    if cache_key not in _response_cache:
        return None

    data = _response_cache[cache_key]
    return CachedResponse(
        events=data.get("events", []),
        intent=data.get("intent", ""),
        concept=data.get("concept"),
        model_used=data.get("model_used", "cache"),
        retrieval_score=data.get("retrieval_score", 0.0),
        chunks_used=data.get("chunks_used", []),
    )


def set_cached_response(
    cache_key: str,
    events: List[Dict[str, Any]],
    intent: str,
    concept: Optional[str],
    model_used: str,
    retrieval_score: float,
    chunks_used: List[str],
) -> None:
    """
    Cache a response.

    Args:
        cache_key: The cache key
        events: Response events to cache
        intent: The classified intent
        concept: The classified concept
        model_used: Which model generated this
        retrieval_score: Retrieval score
        chunks_used: Which chunks were used
    """
    _response_cache[cache_key] = {
        "events": events,
        "intent": intent,
        "concept": concept,
        "model_used": model_used,
        "retrieval_score": retrieval_score,
        "chunks_used": chunks_used,
    }


def clear_session_cache(session_id: str) -> int:
    """
    Clear all cached responses for a session.

    Args:
        session_id: Session to clear

    Returns:
        Number of entries cleared
    """
    # This is O(n) but fine for Phase 1
    keys_to_delete = [
        k for k in _response_cache.keys()
        if k.startswith(hashlib.sha256(f"{session_id}:".encode()).hexdigest()[:8])
    ]
    for k in keys_to_delete:
        del _response_cache[k]
    return len(keys_to_delete)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for debugging."""
    return {
        "total_entries": len(_response_cache),
        "cacheable_intents": list(CACHEABLE_INTENTS),
        "non_cacheable_intents": list(NON_CACHEABLE_INTENTS),
    }
