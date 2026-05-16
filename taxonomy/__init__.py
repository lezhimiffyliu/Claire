"""
Unified taxonomy for Claire - UW Math 124/125/126

Structure:
- Each course has TOPICS and SUBTOPICS
- Topic names directly correspond to heuristic filenames
- Heuristics are markdown files in taxonomy/heuristics/

Usage:
    from taxonomy import get_topics, get_subtopics, load_heuristic

    topics = get_topics("126")
    subtopics = get_subtopics("126", "double_integrals")
    heuristic_md = load_heuristic("double_integrals")

    # NEW: Metadata access
    topic_meta = get_topic_metadata("126", "double_integrals")
    subtopic_meta = get_subtopic_metadata("126", "iterated_integrals")
"""

from pathlib import Path
from typing import Optional

# Import course taxonomies
from .math124 import TOPICS as TOPICS_124, SUBTOPICS as SUBTOPICS_124
from .math125 import TOPICS as TOPICS_125, SUBTOPICS as SUBTOPICS_125
from .math126 import TOPICS as TOPICS_126, SUBTOPICS as SUBTOPICS_126

# Import metadata
from .math124 import TOPIC_METADATA as TOPIC_META_124, SUBTOPIC_METADATA as SUBTOPIC_META_124
from .math125 import TOPIC_METADATA as TOPIC_META_125, SUBTOPIC_METADATA as SUBTOPIC_META_125
from .math126 import TOPIC_METADATA as TOPIC_META_126, SUBTOPIC_METADATA as SUBTOPIC_META_126

HEURISTICS_DIR = Path(__file__).parent / "heuristics"

# Course -> taxonomy mapping
_COURSE_TOPICS = {
    "124": TOPICS_124,
    "125": TOPICS_125,
    "126": TOPICS_126,
}

_COURSE_SUBTOPICS = {
    "124": SUBTOPICS_124,
    "125": SUBTOPICS_125,
    "126": SUBTOPICS_126,
}

# Course -> metadata mapping
_COURSE_TOPIC_METADATA = {
    "124": TOPIC_META_124,
    "125": TOPIC_META_125,
    "126": TOPIC_META_126,
}

_COURSE_SUBTOPIC_METADATA = {
    "124": SUBTOPIC_META_124,
    "125": SUBTOPIC_META_125,
    "126": SUBTOPIC_META_126,
}


def get_topics(course: str) -> list[str]:
    """Get all topics for a course (124, 125, or 126)."""
    return _COURSE_TOPICS.get(course, [])


def get_subtopics(course: str, topic: str) -> list[str]:
    """Get subtopics for a specific topic in a course."""
    subtopics = _COURSE_SUBTOPICS.get(course, {})
    return subtopics.get(topic, [])


def get_all_subtopics(course: str) -> dict[str, list[str]]:
    """Get all subtopics for a course."""
    return _COURSE_SUBTOPICS.get(course, {})


def is_valid_topic(course: str, topic: str) -> bool:
    """Check if topic is valid for the given course."""
    return topic in _COURSE_TOPICS.get(course, [])


def is_valid_subtopic(course: str, subtopic: str) -> bool:
    """Check if subtopic exists in any topic for the course."""
    subtopics = _COURSE_SUBTOPICS.get(course, {})
    for topic_subtopics in subtopics.values():
        if subtopic in topic_subtopics:
            return True
    return False


def get_topic_for_subtopic(course: str, subtopic: str) -> Optional[str]:
    """Find which topic a subtopic belongs to."""
    subtopics = _COURSE_SUBTOPICS.get(course, {})
    for topic, topic_subtopics in subtopics.items():
        if subtopic in topic_subtopics:
            return topic
    return None


def load_heuristic(topic: str) -> Optional[str]:
    """
    Load heuristic markdown content for a topic.

    Args:
        topic: Topic name (must match a file in heuristics/)

    Returns:
        Markdown content as string, or None if not found
    """
    heuristic_path = HEURISTICS_DIR / f"{topic}.md"
    if heuristic_path.exists():
        return heuristic_path.read_text(encoding="utf-8")
    return None


def list_available_heuristics() -> list[str]:
    """List all topics that have heuristic files."""
    if not HEURISTICS_DIR.exists():
        return []
    return [p.stem for p in HEURISTICS_DIR.glob("*.md")]


def get_topic_display_name(topic: str, course: str = None) -> str:
    """
    Human-readable topic name.
    If course is provided, uses display_name from metadata if available.
    """
    if course:
        meta = _COURSE_TOPIC_METADATA.get(course, {}).get(topic, {})
        if "display_name" in meta:
            return meta["display_name"]
    return topic.replace("_", " ").title()


def get_topic_metadata(course: str, topic: str) -> dict:
    """
    Get metadata for a topic.

    Returns dict with:
    - difficulty: 1-5
    - frequency: "high" | "medium" | "low"
    - order: int (pedagogical order)
    - color_family: str (color hue name)
    - display_name: str (human-readable name)
    """
    meta = _COURSE_TOPIC_METADATA.get(course, {})
    return meta.get(topic, {})


def get_subtopic_metadata(course: str, subtopic: str) -> dict:
    """
    Get metadata for a subtopic.

    Returns dict with:
    - difficulty: 1-5
    - frequent: boolean
    - order: int (order within parent topic)
    """
    meta = _COURSE_SUBTOPIC_METADATA.get(course, {})
    return meta.get(subtopic, {})


def get_all_topic_metadata(course: str) -> dict:
    """Get all topic metadata for a course."""
    return _COURSE_TOPIC_METADATA.get(course, {})


def get_all_subtopic_metadata(course: str) -> dict:
    """Get all subtopic metadata for a course."""
    return _COURSE_SUBTOPIC_METADATA.get(course, {})


# Build reverse lookup: subtopic -> topic (for all courses)
_SUBTOPIC_TO_TOPIC = {}
for course_subtopics in _COURSE_SUBTOPICS.values():
    for topic, subtopics in course_subtopics.items():
        for subtopic in subtopics:
            _SUBTOPIC_TO_TOPIC[subtopic] = topic


def normalize_to_topic(name: str, course: str = "124") -> str:
    """
    Normalize any name (topic or subtopic) to a canonical topic.
    Returns original if not found.
    """
    topics = _COURSE_TOPICS.get(course, [])

    # If it's already a topic, return it
    if name in topics:
        return name

    # If it's a subtopic, return its parent topic
    if name in _SUBTOPIC_TO_TOPIC:
        return _SUBTOPIC_TO_TOPIC[name]

    # Not found, return original
    return name


# Foundation topics per course (prerequisites, core skills)
FOUNDATION_TOPICS = {
    "124": [
        "limits",
        "continuity",
        "derivative_definition",
        "derivative_rules",
    ],
    "125": [
        "antiderivatives_and_riemann_sums",
        "fundamental_theorem_of_calculus",
        "substitution",
    ],
    "126": [
        "vectors_and_geometry",
        "partial_derivatives",
        "double_integrals",
    ],
}
