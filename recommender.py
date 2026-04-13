"""
Problem Recommender - selects next problem based on student profile.

Priority order:
1. Topic weaknesses (highest)
2. Foundation/baseline remediation (second)
3. Difficulty progression (third)

Error patterns are used for feedback style, not selection.
"""

from typing import Optional
from student_profile import StudentProfile, get_profile
from problem_loader import Problem, ProblemPart
from math124_taxonomy import normalize_to_topic, FOUNDATION_TOPICS, get_topic_display_name

# Difficulty order for progression
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def recommend_next_problem(
    parts_list: list[tuple[Problem, int]],
    current_idx: int,
    profile: Optional[StudentProfile] = None,
    seen_indices: Optional[set] = None,
) -> int:
    """
    Recommend the next problem index based on profile.

    Returns the index into parts_list.

    Args:
        seen_indices: Set of problem indices already seen this session.
                      If provided, these get a penalty to encourage variety.
    """
    import random

    if not parts_list:
        return 0

    if profile is None:
        profile = get_profile()

    if profile is None:
        # No profile, just go to next
        return (current_idx + 1) % len(parts_list)

    if seen_indices is None:
        seen_indices = set()

    # Build candidate list (exclude current)
    candidates = []
    for i, (problem, part_idx) in enumerate(parts_list):
        if i == current_idx:
            continue

        # Normalize the problem's topic to canonical form
        raw_topic = problem.topic
        canonical_topic = normalize_to_topic(raw_topic)

        # Also get concepts if available
        concepts = getattr(problem, 'concepts', [])

        candidates.append({
            "index": i,
            "problem": problem,
            "part_idx": part_idx,
            "topic": canonical_topic,
            "raw_topic": raw_topic,
            "concepts": concepts,
            "difficulty": problem.difficulty if hasattr(problem, 'difficulty') else "medium",
        })

    if not candidates:
        return current_idx

    # Get priority topics from profile (sorted by urgency)
    priority_topics = profile.get_priority_topics()

    # Get initial focus from diagnostic
    initial_focus = profile.initial_focus_topics

    # Score each candidate
    scored = []
    for c in candidates:
        score = 0
        topic = c["topic"]
        concepts = c["concepts"]
        difficulty = c["difficulty"]
        idx = c["index"]

        # Priority 1: Use topic's priority_score from profile (0-100 points)
        # Higher priority_score = more urgent = higher recommendation score
        if topic in profile.topic_estimates:
            topic_priority = profile.topic_estimates[topic].priority_score
            score += topic_priority * 100  # Scale to 0-100

        # Also check if topic is in priority list (rank bonus)
        if topic in priority_topics:
            rank = priority_topics.index(topic)
            score += max(0, 50 - rank * 10)  # Top priority = +50

        # Priority 2: Foundation topics if suggested (0-30 points)
        if profile.suggest_foundation_review and topic in FOUNDATION_TOPICS:
            foundation_rank = FOUNDATION_TOPICS.index(topic)
            score += 30 - (foundation_rank * 10)

        # Priority 3: Initial focus from diagnostic (0-20 points)
        if topic in initial_focus:
            score += 20

        # Priority 4: Difficulty progression (0-15 points)
        diff_value = DIFFICULTY_ORDER.get(difficulty, 1)
        if profile.overall_accuracy < 0.5:
            score += (2 - diff_value) * 5  # Prefer easier
        elif profile.overall_accuracy > 0.7:
            score += diff_value * 5  # Prefer harder
        else:
            score += 5 if diff_value == 1 else 3

        # PENALTY for already-seen problems (encourage variety)
        if idx in seen_indices:
            score -= 50  # Heavy penalty for seen problems

        # Add small random factor to break ties (0-5 points)
        score += random.random() * 5

        scored.append((idx, score, topic))

    # Sort by score descending
    scored.sort(key=lambda x: -x[1])

    # Return highest scored
    return scored[0][0] if scored else (current_idx + 1) % len(parts_list)


def get_feedback_style(profile: Optional[StudentProfile] = None) -> dict:
    """
    Get feedback style hints based on error patterns.

    Returns hints for how to adjust feedback, not problem selection.
    """
    if profile is None:
        profile = get_profile()

    style = {
        "emphasis": None,  # What to emphasize in feedback
        "show_steps": True,  # Whether to show step-by-step
        "extra_hints": False,  # Whether to give extra hints
    }

    if profile is None:
        return style

    dominant_error = profile.get_dominant_error_type()

    if dominant_error == "concept":
        # Emphasize conceptual understanding
        style["emphasis"] = "concept"
        style["show_steps"] = True
        style["extra_hints"] = True

    elif dominant_error == "algebra":
        # Emphasize careful computation
        style["emphasis"] = "algebra"
        style["show_steps"] = True

    elif dominant_error == "logic":
        # Emphasize reasoning steps
        style["emphasis"] = "logic"
        style["show_steps"] = True

    elif dominant_error == "careless":
        # Emphasize double-checking
        style["emphasis"] = "careless"
        style["show_steps"] = False  # They know the steps, just careless

    return style


def get_recommendation_reason(
    problem: Problem,
    profile: Optional[StudentProfile] = None,
) -> Optional[str]:
    """
    Get a short explanation of why this problem was recommended.
    Uses non-judgmental language (not "weak", "poor", etc.)
    """
    if profile is None:
        profile = get_profile()

    if profile is None:
        return None

    # Normalize problem topic
    topic = normalize_to_topic(problem.topic)
    display = get_topic_display_name(topic)

    # Check if we have an estimate for this topic
    if topic in profile.topic_estimates:
        estimate = profile.topic_estimates[topic]

        # High priority = needs attention
        if estimate.priority_score > 0.5:
            if estimate.confidence < 0.4:
                return f"{display} — gathering more signal"
            else:
                return f"{display} — recommended review"

    # Check initial focus from diagnostic
    if topic in profile.initial_focus_topics:
        return f"{display} — from diagnostic"

    # Check foundation
    if profile.suggest_foundation_review and topic in FOUNDATION_TOPICS:
        return f"{display} — foundation topic"

    return None
