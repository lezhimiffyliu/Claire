"""
Calculus Topics Module

Provides fine-grained topic detection and classification.
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

__all__ = [
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
]
