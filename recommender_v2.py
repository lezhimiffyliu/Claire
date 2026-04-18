"""
Problem Recommender V2 - Uses hierarchical topic/subtopic tracking.

Key improvements over V1:
- Recommends based on SUBTOPIC weaknesses, not just topics
- Matches problem subtopics to student's weakest areas
- More targeted practice recommendations
"""

from typing import Optional
from student_profile_v2 import StudentProfileV2, get_profile_v2
from problem_loader import Problem, ProblemPart
from taxonomy import (
    normalize_to_topic,
    get_topic_for_subtopic,
    FOUNDATION_TOPICS,
    get_topic_display_name,
    get_subtopics
)

# Difficulty order for progression
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def recommend_next_problem_v2(
    parts_list: list[tuple[Problem, int]],
    current_idx: int,
    profile: Optional[StudentProfileV2] = None,
    seen_indices: Optional[set] = None,
) -> int:
    """
    Recommend the next problem index based on V2 profile.

    Enhanced to consider subtopic-level mastery.

    Returns the index into parts_list.

    Args:
        seen_indices: Set of problem indices already seen this session.
                      If provided, these get a penalty to encourage variety.
    """
    import random

    if not parts_list:
        return 0

    if profile is None:
        profile = get_profile_v2()

    if profile is None:
        # No profile, just go to next
        return (current_idx + 1) % len(parts_list)

    if seen_indices is None:
        seen_indices = set()

    # Get course from profile or first problem
    course = profile.course if profile else "124"
    if not course and parts_list:
        first_problem = parts_list[0][0]
        course = first_problem.course.replace("math_", "") if hasattr(first_problem, 'course') else "124"

    # Get foundation topics for this course
    foundation_topics = FOUNDATION_TOPICS.get(course, FOUNDATION_TOPICS.get("124", []))

    # Get priority subtopics from profile (weakest across all topics)
    priority_subtopics = profile.get_all_priority_subtopics(limit=15)
    priority_subtopic_set = {sub for (topic, sub) in priority_subtopics}

    # Get priority topics
    priority_topics = profile.get_priority_topics()

    # Get initial focus from diagnostic
    initial_focus = profile.initial_focus_topics

    # Build candidate list (exclude current)
    candidates = []
    for i, (problem, part_idx) in enumerate(parts_list):
        if i == current_idx:
            continue

        # Normalize the problem's topic to canonical form
        raw_topic = problem.topic
        canonical_topic = normalize_to_topic(raw_topic, course)

        # Get concepts/subtopics if available
        concepts = getattr(problem, 'concepts', [])
        # Also check if problem has 'subtopics' field
        problem_subtopics = getattr(problem, 'subtopics', [])

        candidates.append({
            "index": i,
            "problem": problem,
            "part_idx": part_idx,
            "topic": canonical_topic,
            "raw_topic": raw_topic,
            "concepts": concepts,
            "subtopics": problem_subtopics,
            "difficulty": problem.difficulty if hasattr(problem, 'difficulty') else "medium",
        })

    if not candidates:
        return current_idx

    # Score each candidate
    scored = []
    for c in candidates:
        score = 0
        topic = c["topic"]
        concepts = c["concepts"]
        problem_subtopics = c["subtopics"]
        difficulty = c["difficulty"]
        idx = c["index"]

        # ===== Priority 1: SUBTOPIC match (0-120 points) =====
        # If problem has subtopics tagged, check if they match weak subtopics
        subtopic_match_score = 0
        if problem_subtopics:
            for prob_subtopic in problem_subtopics:
                if prob_subtopic in priority_subtopic_set:
                    # High bonus for matching weak subtopics
                    rank = next((i for i, (t, s) in enumerate(priority_subtopics) if s == prob_subtopic), 15)
                    subtopic_match_score += max(0, 60 - rank * 4)  # Top priority = +60

        score += subtopic_match_score

        # ===== Priority 1.5: ERROR TYPE urgency boost (0-30 points) =====
        # Boost score if problem matches subtopics with specific error patterns
        # Concept errors = high priority, careless errors = low priority
        error_urgency_boost = 0
        if topic in profile.topic_estimates and problem_subtopics:
            topic_est = profile.topic_estimates[topic]
            for prob_subtopic in problem_subtopics:
                if prob_subtopic in topic_est.subtopics:
                    sub_est = topic_est.subtopics[prob_subtopic]
                    error_urgency_boost += sub_est.get_error_urgency_boost()

        score += error_urgency_boost

        # ===== Priority 1.7: RECENT PERFORMANCE boost (0-40 points) ⭐ NEW! =====
        # Immediate response to current struggles
        # If student is failing THIS subtopic RIGHT NOW → high priority
        recent_performance_boost = 0
        if topic in profile.topic_estimates and problem_subtopics:
            topic_est = profile.topic_estimates[topic]
            for prob_subtopic in problem_subtopics:
                if prob_subtopic in topic_est.subtopics:
                    sub_est = topic_est.subtopics[prob_subtopic]
                    recent_performance_boost += sub_est.get_recent_performance_boost()

        score += recent_performance_boost

        # ===== Priority 2: Topic-level priority (0-100 points) =====
        # Use topic's priority_score from profile
        if topic in profile.topic_estimates:
            topic_priority = profile.topic_estimates[topic].priority_score
            score += topic_priority * 100  # Scale to 0-100

        # Also check if topic is in priority list (rank bonus)
        if topic in priority_topics:
            rank = priority_topics.index(topic)
            score += max(0, 50 - rank * 10)  # Top priority = +50

        # ===== Priority 3: Foundation topics (0-30 points) =====
        if profile.suggest_foundation_review and topic in foundation_topics:
            foundation_rank = foundation_topics.index(topic)
            score += 30 - (foundation_rank * 10)

        # ===== Priority 4: Initial focus from diagnostic (0-20 points) =====
        if topic in initial_focus:
            score += 20

        # ===== Priority 5: Difficulty progression (0-15 points) =====
        diff_value = DIFFICULTY_ORDER.get(difficulty, 1)
        if profile.overall_accuracy < 0.5:
            score += (2 - diff_value) * 5  # Prefer easier
        elif profile.overall_accuracy > 0.7:
            score += diff_value * 5  # Prefer harder
        else:
            score += 5 if diff_value == 1 else 3

        # ===== PENALTY for already-seen problems (-50 points) =====
        if idx in seen_indices:
            score -= 50  # Heavy penalty for seen problems

        # Add small random factor to break ties (0-5 points)
        score += random.random() * 5

        scored.append((idx, score, topic, problem_subtopics))

    # Sort by score descending
    scored.sort(key=lambda x: -x[1])

    # Return highest scored
    return scored[0][0] if scored else (current_idx + 1) % len(parts_list)


def get_recommendation_reason_v2(
    problem: Problem,
    profile: Optional[StudentProfileV2] = None,
) -> Optional[str]:
    """
    Get a short explanation of why this problem was recommended.
    Enhanced to include subtopic-level reasoning.
    """
    if profile is None:
        profile = get_profile_v2()

    if profile is None:
        return None

    # Get course for foundation topics lookup
    course = profile.course if profile.course else "124"
    foundation_topics = FOUNDATION_TOPICS.get(course, FOUNDATION_TOPICS.get("124", []))

    # Normalize problem topic
    topic = normalize_to_topic(problem.topic, course)
    display = get_topic_display_name(topic)

    # Check if problem has subtopics
    problem_subtopics = getattr(problem, 'subtopics', [])

    # Get priority subtopics from profile
    priority_subtopics = profile.get_all_priority_subtopics(limit=10)
    priority_subtopic_set = {sub for (t, sub) in priority_subtopics}

    # Check for subtopic match
    if problem_subtopics:
        matching_subtopics = [s for s in problem_subtopics if s in priority_subtopic_set]
        if matching_subtopics:
            # Show first matching subtopic
            subtopic_display = matching_subtopics[0].replace("_", " ").title()
            return f"{display} — {subtopic_display} needs practice"

    # Fallback to topic-level reasoning
    if topic in profile.topic_estimates:
        estimate = profile.topic_estimates[topic]

        # High priority = needs attention
        if estimate.priority_score > 0.5:
            # Check if we have subtopic data
            weak_subtopics = estimate.get_weakest_subtopics(limit=1)
            if weak_subtopics:
                subtopic_display = weak_subtopics[0].replace("_", " ").title()
                return f"{display} — {subtopic_display} recommended"
            else:
                if estimate.confidence < 0.4:
                    return f"{display} — gathering more signal"
                else:
                    return f"{display} — recommended review"

    # Check initial focus from diagnostic
    if topic in profile.initial_focus_topics:
        return f"{display} — from diagnostic"

    # Check foundation
    if profile.suggest_foundation_review and topic in foundation_topics:
        return f"{display} — foundation topic"

    return None


def get_topic_breakdown(
    profile: Optional[StudentProfileV2] = None,
    topic: Optional[str] = None
) -> dict:
    """
    Get detailed breakdown of subtopic mastery within a topic.

    Returns:
        Dict with subtopic scores, priorities, and status
    """
    if profile is None:
        profile = get_profile_v2()

    if profile is None or topic is None:
        return {}

    if topic not in profile.topic_estimates:
        # Return empty subtopics from taxonomy
        course = profile.course if profile else "124"
        subtopics = get_subtopics(course, topic)
        return {
            "topic": topic,
            "score": 0.5,
            "status": "not yet tested",
            "subtopics": [
                {
                    "name": sub,
                    "display_name": sub.replace("_", " ").title(),
                    "score": 0.5,
                    "status": "not yet tested",
                    "priority": 0.5,
                }
                for sub in subtopics
            ]
        }

    topic_est = profile.topic_estimates[topic]

    # Build subtopic list
    subtopic_list = []
    for sub_name, sub_est in topic_est.subtopics.items():
        subtopic_list.append({
            "name": sub_name,
            "display_name": sub_name.replace("_", " ").title(),
            "score": sub_est.score,
            "status": sub_est.status_label,
            "priority": sub_est.priority_score,
            "attempts": sub_est.attempts,
            "correct": sub_est.correct,
            "incorrect": sub_est.incorrect,
        })

    # Sort by priority descending
    subtopic_list.sort(key=lambda x: -x["priority"])

    return {
        "topic": topic,
        "score": topic_est.score,
        "status": topic_est.status_label,
        "confidence": topic_est.confidence,
        "total_attempts": topic_est.total_attempts,
        "subtopics": subtopic_list,
    }


# Backward compatibility with V1
def get_feedback_style(profile: Optional[StudentProfileV2] = None) -> dict:
    """
    Get feedback style hints based on error patterns.
    (Unchanged from V1)
    """
    if profile is None:
        profile = get_profile_v2()

    style = {
        "emphasis": None,
        "show_steps": True,
        "extra_hints": False,
    }

    if profile is None:
        return style

    dominant_error = profile.get_dominant_error_type()

    if dominant_error == "concept":
        style["emphasis"] = "concept"
        style["show_steps"] = True
        style["extra_hints"] = True

    elif dominant_error == "algebra":
        style["emphasis"] = "algebra"
        style["show_steps"] = True

    elif dominant_error == "logic":
        style["emphasis"] = "logic"
        style["show_steps"] = True

    elif dominant_error == "careless":
        style["emphasis"] = "careless"
        style["show_steps"] = False

    return style
