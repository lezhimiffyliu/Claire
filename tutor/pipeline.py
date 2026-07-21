"""
Tutor Response Pipeline

Main orchestration module that coordinates:
1. Response cache check (FIRST - before any LLM calls)
2. Classification (only if cache miss)
3. Retrieval
4. Strategy decision
5. Response generation (Sonnet adapter or Opus agent)

Entry points:
- tutor_respond() - for chat-based responses
- route_tutor_request() - unified entry that routes to teaching_action or chat
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from tutor.classifier import classify_intent_and_concept, Classification
from tutor.retrieval import search_teaching_chunks, RetrievalResult
from tutor.adapter import generate_adapted_response, events_to_dict, AdaptedResponse
from tutor.strategist import should_use_opus, StrategyDecision
from tutor.response_cache import (
    build_cache_key,
    is_cacheable_intent,
    get_cached_response,
    set_cached_response,
)

# Teaching action intents that should be routed to teaching_planner
TEACHING_ACTION_INTENTS = {"student_stuck", "student_hint", "student_check", "followup"}

logger = logging.getLogger(__name__)


def route_tutor_request(
    message: str,
    session_id: str,
    problem_context: Optional[Dict[str, Any]] = None,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    part_id: Optional[str] = None,
    step_index: Optional[int] = None,
    student_message: Optional[str] = None,
    force_opus: bool = False,
) -> "TutorResponse":
    """
    Unified entry point - routes to teaching_action or full pipeline.

    If action_type is a teaching action intent (student_stuck, student_hint, etc.),
    routes to _handle_teaching_action which uses the teaching_planner.

    Otherwise, routes to tutor_respond for the full retrieval-based pipeline.

    Args:
        message: Student message
        session_id: Session ID for tracking
        problem_context: Current problem info
        recent_thread: Recent conversation history
        user_id: User ID for personalization
        action_type: Explicit intent from frontend (e.g., "student_stuck", "cant_start")
        part_id: Current part identifier for cache key
        step_index: Current step within part
        student_message: Optional student message for followup intent
        force_opus: Force Opus usage

    Returns:
        TutorResponse with events and metadata
    """
    # Route teaching actions to specialized handler
    if action_type and action_type.lower() in TEACHING_ACTION_INTENTS:
        return _handle_teaching_action(
            action_type=action_type,
            message=message,
            session_id=session_id,
            problem_context=problem_context,
            recent_thread=recent_thread,
            part_id=part_id,
            step_index=step_index,
            student_message=student_message or message,
        )

    # Otherwise use the full retrieval-based pipeline
    return tutor_respond(
        message=message,
        session_id=session_id,
        problem_context=problem_context,
        recent_thread=recent_thread,
        user_id=user_id,
        action_type=action_type,
        part_id=part_id,
        step_index=step_index,
        force_opus=force_opus,
    )


def _is_cold_start(recent_thread: Optional[List[Dict[str, Any]]]) -> bool:
    """Check if this is a cold start (beginning of problem thread)."""
    if not recent_thread:
        return True
    # Count assistant messages (teaching steps)
    assistant_count = sum(1 for msg in recent_thread if msg.get('role') in ('assistant', 'claire'))
    # Cold start = no prior teaching has happened
    return assistant_count == 0


def _handle_teaching_action(
    action_type: str,
    message: str,
    session_id: str,
    problem_context: Optional[Dict[str, Any]],
    recent_thread: Optional[List[Dict[str, Any]]],
    part_id: Optional[str],
    step_index: Optional[int],
    student_message: Optional[str] = None,
) -> "TutorResponse":
    """
    Handle teaching action intents (student_stuck, student_hint, etc.) with caching.

    This routes to the teaching_planner module and converts responses to unified event schema.
    Caching is applied for cold-start cacheable intents.
    """
    from tutor.teaching_planner import execute_teaching_action

    # Extract problem_id from context
    problem_id = problem_context.get("id", "unknown") if problem_context else "unknown"
    if part_id is None:
        part_id = str(problem_context.get("current_part_index", 0)) if problem_context else "0"
    if step_index is None:
        step_index = problem_context.get("step_index", 0) if problem_context else 0

    current_part_index = int(part_id) if part_id.isdigit() else 0

    logger.info(f"[tutor] Teaching action: {action_type} | part={part_id} | step={step_index}")

    # Step 1: Check cache (only for cacheable intents at cold start)
    is_cold = _is_cold_start(recent_thread)
    action_lower = action_type.lower()

    if is_cacheable_intent(action_lower) and is_cold:
        cache_key = build_cache_key(session_id, problem_id, part_id, step_index, action_lower)
        cached = get_cached_response(cache_key)

        if cached:
            logger.info(f"[tutor] TEACHING ACTION CACHE HIT: key={cache_key[:16]}..., action={action_lower}")
            return TutorResponse(
                events=cached.events,
                intent=cached.intent,
                concept=cached.concept,
                model_used="response_cache",
                response_cache_hit=True,
                retrieval_cache_hit=False,
                retrieval_score=cached.retrieval_score,
                strategy_decision="response_cache_hit",
                chunks_used=cached.chunks_used,
            )
        else:
            logger.info(f"[tutor] Teaching action cache miss for {action_lower}")
    elif is_cacheable_intent(action_lower) and not is_cold:
        logger.info(f"[tutor] Skipping teaching action cache: not cold start")

    # Step 2: Call teaching_planner
    try:
        result = execute_teaching_action(
            intent=action_lower,
            problem_context=problem_context,
            current_part_index=current_part_index,
            student_message=student_message,
            recent_thread=recent_thread,
        )
    except Exception as e:
        logger.error(f"[tutor] Teaching planner error: {e}")
        result = {
            "concept_bridge": "Let's work through this step by step.",
            "next_micro_step": "Start by identifying what the problem is asking for.",
            "quick_replies": [],
        }

    # Step 3: Convert to unified event schema (teaching_card event type)
    events = [{
        "event": "teaching_card",
        "concept_bridge": result.get("concept_bridge", ""),
        "next_micro_step": result.get("next_micro_step", ""),
        "quick_replies": result.get("quick_replies", []),
    }]

    # Step 4: Cache response (only for cold-start cacheable intents)
    if is_cacheable_intent(action_lower) and is_cold:
        cache_key = build_cache_key(session_id, problem_id, part_id, step_index, action_lower)
        set_cached_response(
            cache_key=cache_key,
            events=events,
            intent=action_lower,
            concept=None,
            model_used="teaching_planner",
            retrieval_score=0.0,
            chunks_used=[],
        )
        logger.info(f"[tutor] Cached teaching action: key={cache_key[:16]}..., action={action_lower}")

    return TutorResponse(
        events=events,
        intent=action_lower,
        concept=None,
        model_used="teaching_planner",
        response_cache_hit=False,
        retrieval_cache_hit=False,
        retrieval_score=0.0,
        strategy_decision="teaching_action",
        chunks_used=[],
    )


@dataclass
class TutorResponse:
    """Full response from tutor pipeline."""
    events: List[Dict[str, Any]]
    intent: str
    concept: Optional[str]
    model_used: str
    response_cache_hit: bool   # True if returned from response cache
    retrieval_cache_hit: bool  # True if high retrieval score (chunks reused)
    retrieval_score: float
    strategy_decision: str
    chunks_used: List[str]


def tutor_respond(
    message: str,
    session_id: str,
    problem_context: Optional[Dict[str, Any]] = None,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,  # Explicit intent from frontend button
    part_id: Optional[str] = None,      # Current part identifier
    step_index: Optional[int] = None,   # Current step within part (0=start, 1=after first hint, etc.)
    force_opus: bool = False,
) -> TutorResponse:
    """
    Main entry point for tutor response generation.

    Pipeline:
    1. Check response cache (if action_type provided, skip classification)
    2. Classify intent/concept (only if needed)
    3. Search teaching chunks
    4. Decide if Opus needed
    5. Generate response (Sonnet adapter or Opus agent)
    6. Cache response (if cacheable intent)

    Args:
        message: Student message
        session_id: Session ID for tracking
        problem_context: Current problem info
        recent_thread: Recent conversation history
        user_id: User ID for personalization (future)
        action_type: Explicit intent from frontend (e.g., "cant_start", "how_to_start")
        part_id: Current part identifier for cache key
        step_index: Current step within part (differentiates solving stages)
        force_opus: Force Opus usage (bypass strategy)

    Returns:
        TutorResponse with events and metadata
    """
    logger.info(f"[tutor] Processing: {message[:50]}... | action_type={action_type} | step={step_index}")

    # Extract problem_id, part_id, step_index from context
    problem_id = problem_context.get("id", "unknown") if problem_context else "unknown"
    if part_id is None:
        part_id = str(problem_context.get("current_part_index", 0)) if problem_context else "0"
    if step_index is None:
        step_index = problem_context.get("step_index", 0) if problem_context else 0

    # =========================================================
    # Step 0: Response Cache Check (BEFORE any LLM calls)
    # Only for cold start intents at the beginning of conversation
    # =========================================================
    intent_for_cache = action_type  # Use explicit action if provided

    # Check if this is truly a cold start (beginning of problem thread)
    def is_cold_start() -> bool:
        """Response cache only applies at the very beginning of a problem."""
        if not recent_thread:
            return True
        # Count assistant messages (teaching steps)
        assistant_count = sum(1 for msg in recent_thread if msg.get('role') in ('assistant', 'claire'))
        # Cold start = no prior teaching has happened
        return assistant_count == 0

    if intent_for_cache and is_cacheable_intent(intent_for_cache) and is_cold_start():
        cache_key = build_cache_key(session_id, problem_id, part_id, step_index, intent_for_cache)
        cached = get_cached_response(cache_key)

        if cached:
            logger.info(f"[tutor] RESPONSE CACHE HIT: key={cache_key[:16]}..., intent={cached.intent}, step={step_index}")
            return TutorResponse(
                events=cached.events,
                intent=cached.intent,
                concept=cached.concept,
                model_used="response_cache",
                response_cache_hit=True,
                retrieval_cache_hit=False,
                retrieval_score=cached.retrieval_score,
                strategy_decision="response_cache_hit",
                chunks_used=cached.chunks_used,
            )
        else:
            logger.info(f"[tutor] Response cache miss for action_type={action_type}, step={step_index}")
    elif intent_for_cache and is_cacheable_intent(intent_for_cache) and not is_cold_start():
        logger.info(f"[tutor] Skipping response cache: not cold start (thread has prior teaching)")

    # =========================================================
    # Step 1: Classify (skip if action_type already provided)
    # =========================================================
    if action_type and is_cacheable_intent(action_type):
        # Use provided action_type as intent (skip Haiku call)
        classification = Classification(
            intent=action_type,
            concept=None,
            misconception=None,
            confidence=1.0,
            language="en",
            requires_strategy=False,
            raw_analysis={"source": "action_type"},
        )
        logger.info(f"[tutor] Using action_type as intent: {action_type} (skipped Haiku)")
    else:
        # Need to classify with Haiku
        classification = classify_intent_and_concept(
            message=message,
            problem_context=problem_context,
            recent_thread=recent_thread,
        )
        logger.info(f"[tutor] Classification: intent={classification.intent}, "
                    f"concept={classification.concept}, "
                    f"requires_strategy={classification.requires_strategy}")

        # Check cache again with classified intent (if cacheable AND cold start)
        if is_cacheable_intent(classification.intent) and is_cold_start():
            cache_key = build_cache_key(session_id, problem_id, part_id, step_index, classification.intent)
            cached = get_cached_response(cache_key)

            if cached:
                logger.info(f"[tutor] RESPONSE CACHE HIT (post-classify): intent={cached.intent}, step={step_index}")
                return TutorResponse(
                    events=cached.events,
                    intent=cached.intent,
                    concept=cached.concept,
                    model_used="response_cache",
                    response_cache_hit=True,
                    retrieval_cache_hit=False,
                    retrieval_score=cached.retrieval_score,
                    strategy_decision="response_cache_hit",
                    chunks_used=cached.chunks_used,
                )

    # =========================================================
    # Step 2: Retrieve teaching chunks
    # =========================================================
    retrieval_result = search_teaching_chunks(
        intent=classification.intent,
        concept=classification.concept,
        message=message,
        problem_context=problem_context,
        top_k=3,
    )
    logger.info(f"[tutor] Retrieval: {len(retrieval_result.chunks)} chunks, "
                f"top_score={retrieval_result.top_score:.2f}")

    retrieval_cache_hit = retrieval_result.top_score >= 0.7

    # =========================================================
    # Step 3: Strategy decision
    # =========================================================
    strategy = should_use_opus(
        classification=classification,
        retrieval_result=retrieval_result,
        recent_thread=recent_thread,
    )
    logger.info(f"[tutor] Strategy: use_opus={strategy.use_opus}, reason={strategy.reason}")

    # =========================================================
    # Step 4: Generate response
    # =========================================================
    if force_opus or strategy.use_opus:
        # Use Opus agent
        response = _call_opus_agent(
            message=message,
            session_id=session_id,
            problem_context=problem_context,
            recent_thread=recent_thread,
            classification=classification,
        )
        model_used = "opus"
        chunks_used = []
    else:
        # Use Sonnet adapter with retrieved chunks
        adapted = generate_adapted_response(
            retrieved_chunks=retrieval_result.chunks,
            classification=classification,
            message=message,
            problem_context=problem_context,
            recent_thread=recent_thread,
        )
        response = events_to_dict(adapted.events)
        model_used = adapted.model_used
        chunks_used = adapted.chunks_used

    # =========================================================
    # Step 5: Cache response (only for cold start cacheable intents)
    # =========================================================
    if is_cacheable_intent(classification.intent) and is_cold_start():
        cache_key = build_cache_key(session_id, problem_id, part_id, step_index, classification.intent)
        set_cached_response(
            cache_key=cache_key,
            events=response,
            intent=classification.intent,
            concept=classification.concept,
            model_used=model_used,
            retrieval_score=retrieval_result.top_score,
            chunks_used=chunks_used,
        )
        logger.info(f"[tutor] Cached response: key={cache_key[:16]}..., intent={classification.intent}")

    return TutorResponse(
        events=response,
        intent=classification.intent,
        concept=classification.concept,
        model_used=model_used,
        response_cache_hit=False,
        retrieval_cache_hit=retrieval_cache_hit,
        retrieval_score=retrieval_result.top_score,
        strategy_decision=strategy.reason,
        chunks_used=chunks_used,
    )


def _call_opus_agent(
    message: str,
    session_id: str,
    problem_context: Optional[Dict[str, Any]],
    recent_thread: Optional[List[Dict[str, Any]]],
    classification: Classification,
) -> List[Dict[str, Any]]:
    """
    Call the full Claire agent (Opus orchestration).
    This is the expensive path - only used when truly needed.
    """
    try:
        from agent.claire_agent import ClaireAgent

        agent = ClaireAgent()
        agent.set_model_tier("premium")

        if problem_context:
            class MinimalContext:
                def has_context(self):
                    return bool(problem_context)
                def has_questions(self):
                    return False
                material_names = []
                detected_patterns = []

            agent.exam_context = MinimalContext()

        result = agent.process_query(message)
        events = result.get("events", [])

        formatted = []
        for evt in events:
            if isinstance(evt, dict):
                formatted.append(evt)
            else:
                formatted.append({"event": "say", "text": str(evt), "tone": "neutral"})

        return formatted

    except Exception as e:
        logger.error(f"[tutor] Opus agent error: {e}")
        return [{
            "event": "say",
            "text": "Let me help you with that. Could you tell me more about where you're stuck?",
            "tone": "encouraging",
        }]
