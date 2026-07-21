"""
Tutor Response Pipeline

A semantic-first approach to generating Claire's teaching responses.
Uses intent classification + vector retrieval + adaptive generation.

Modules:
- classifier: Classify message intent and concept
- retrieval: Search teaching chunks via vector similarity
- adapter: Generate adapted response from retrieved chunks
- strategist: Decide when to escalate to Opus
- response_cache: Cache complete responses for low-risk intents
- pipeline: Main orchestration
"""

from tutor.pipeline import tutor_respond
from tutor.classifier import classify_intent_and_concept
from tutor.retrieval import search_teaching_chunks
from tutor.adapter import generate_adapted_response
from tutor.strategist import should_use_opus
from tutor.response_cache import (
    is_cacheable_intent,
    get_cached_response,
    set_cached_response,
    build_cache_key,
)

__all__ = [
    'tutor_respond',
    'classify_intent_and_concept',
    'search_teaching_chunks',
    'generate_adapted_response',
    'should_use_opus',
    'is_cacheable_intent',
    'get_cached_response',
    'set_cached_response',
    'build_cache_key',
]
