"""
Calculus Topics Module

Provides:
- Fine-grained topic detection and classification
- Topic → heuristic mapping for solving templates
"""

from .topic_detector import (
    VALID_TOPICS,
    TOPIC_DISPLAY_NAMES,
    TOPIC_COURSE,
    get_topic_display,
    get_topic_course,
    detect_topics_llm,
    detect_topics_keyword,
    detect_topics_batch,
    aggregate_topics,
    get_top_topics,
)

from .heuristic_loader import (
    get_heuristic_file,
    load_heuristic,
    get_solving_approach,
    format_approach_for_display,
    get_approaches_for_questions,
)

__all__ = [
    # Topic detection
    "VALID_TOPICS",
    "TOPIC_DISPLAY_NAMES",
    "TOPIC_COURSE",
    "get_topic_display",
    "get_topic_course",
    "detect_topics_llm",
    "detect_topics_keyword",
    "detect_topics_batch",
    "aggregate_topics",
    "get_top_topics",
    # Heuristic loading
    "get_heuristic_file",
    "load_heuristic",
    "get_solving_approach",
    "format_approach_for_display",
    "get_approaches_for_questions",
]
