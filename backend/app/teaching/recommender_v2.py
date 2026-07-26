"""
Problem Recommender V2 - Uses hierarchical topic/subtopic tracking.

Key improvements over V1:
- Recommends based on SUBTOPIC weaknesses, not just topics
- Matches problem subtopics to student's weakest areas
- More targeted practice recommendations
"""

from typing import Optional
from app.teaching.student_profile_v2 import StudentProfileV2, get_profile_v2
from app.content.problem_loader import Problem, ProblemPart
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
    session_questions: Optional[list] = None,
) -> int:
    """
    Recommend the next problem index based on V2 profile.

    Enhanced with:
    - Subtopic-level mastery
    - Question-level history tracking
    - Short-term suppression + long-term revisit

    Returns the index into parts_list.

    Args:
        session_questions: List of question_ids attempted this session (for short-term suppression)
    """
    import random

    if not parts_list:
        return 0

    if profile is None:
        profile = get_profile_v2()

    if profile is None:
        # No profile, just go to next
        return (current_idx + 1) % len(parts_list)

    if session_questions is None:
        session_questions = []

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

        # Get question_id (unique identifier from problem)
        question_id = getattr(problem, 'id', None) or getattr(problem, 'question_id', None)

        candidates.append({
            "index": i,
            "problem": problem,
            "part_idx": part_idx,
            "topic": canonical_topic,
            "raw_topic": raw_topic,
            "concepts": concepts,
            "subtopics": problem_subtopics,
            "difficulty": problem.difficulty if hasattr(problem, 'difficulty') else "medium",
            "question_id": question_id,
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
        question_id = c["question_id"]

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

        # ===== Priority 6: QUESTION-LEVEL history (-40 to +30 points) ⭐ NEW! =====
        # Smart question memory: short-term suppression + long-term revisit
        # - Last wrong: +25 (reinforce error correction)
        # - Last correct: -15 (reduce short-term repetition)
        # - In recent session: -40 (short-term suppression)
        # - Time decay: Gradually restore weight after 1+ days
        question_boost = 0
        if question_id:
            question_boost = profile.get_question_boost(question_id, session_questions)

        score += question_boost

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


# ============================================================
# API-SPECIFIC FUNCTIONS
# ============================================================

import logging

logger = logging.getLogger(__name__)


def _is_new_user(profile: Optional[StudentProfileV2], recent_attempts: Optional[list]) -> bool:
    """
    Detect if user is a new user (no practice history).

    A user is considered "new" if:
    - No profile, OR
    - profile.total_attempts == 0 (no topic estimates), AND
    - No recent_attempts with is_correct != None (ungraded attempts don't count)
    """
    if profile is None:
        return True

    # Check if profile has any practice data
    total_attempts = profile.total_correct + profile.total_incorrect
    if total_attempts > 0:
        return False

    # Check if there are any graded attempts
    if recent_attempts:
        graded_attempts = [a for a in recent_attempts if a.get("is_correct") is not None]
        if len(graded_attempts) > 0:
            return False

    return True


def generate_sweep_recommendations(
    course: str,
    profile: Optional[StudentProfileV2] = None,
    recent_attempts: Optional[list] = None,
    limit: int = 5
) -> list[dict]:
    """
    Generate SWEEP-phase recommendations for new users.

    Sweep phase = cover all topics in pedagogical order, starting from Chapter 1.
    Each topic gets 2-3 problems before moving to the next.

    Args:
        course: Course code ("124", "125", "126")
        profile: StudentProfileV2 (may be empty)
        recent_attempts: Recent attempts (may be empty or all ungraded)
        limit: Max recommendations to return

    Returns:
        List of checkpoint-style recommendation dicts
    """
    from app.content.problem_loader import load_problems
    from taxonomy import (
        get_topics,
        get_subtopics,
        get_topic_metadata,
        get_subtopic_metadata,
        get_topic_display_name,
    )
    import random

    logger.info(f"[SWEEP] Generating sweep recommendations for course={course}")

    # Get topics in pedagogical order (TOPICS list is already ordered by 'order' field)
    topics_ordered = get_topics(course)

    if not topics_ordered:
        logger.warning(f"[SWEEP] No topics found for course={course}")
        return []

    # Load all problems
    all_problems = load_problems(course)

    # Group problems by topic
    topic_problems = {}
    for p in all_problems:
        if not p.topic:
            continue
        if p.topic not in topic_problems:
            topic_problems[p.topic] = []
        topic_problems[p.topic].append(p)

    # Find topics user has already practiced (from profile.topic_estimates)
    practiced_topics = set()
    if profile and profile.topic_estimates:
        for topic, est in profile.topic_estimates.items():
            if est.total_attempts > 0:
                practiced_topics.add(topic)

    # Also check recent_attempts for practiced topics
    if recent_attempts:
        for a in recent_attempts:
            topic = a.get("topic")
            if topic and a.get("is_correct") is not None:
                practiced_topics.add(topic)

    logger.info(f"[SWEEP] Practiced topics: {practiced_topics}")

    # Find next topics to recommend (first unpracticed topics in order)
    recommendations = []

    for topic in topics_ordered:
        if len(recommendations) >= limit:
            break

        # Skip topics with no problems
        if topic not in topic_problems or len(topic_problems[topic]) == 0:
            continue

        problems = topic_problems[topic]
        topic_meta = get_topic_metadata(course, topic)
        display_name = get_topic_display_name(topic, course)

        # Get subtopics and filter for frequent ones
        subtopics = get_subtopics(course, topic)
        frequent_subtopics = []
        for sub in subtopics:
            sub_meta = get_subtopic_metadata(course, sub)
            if sub_meta.get("frequent", True):  # Default to True if not specified
                frequent_subtopics.append(sub)

        # Filter problems: prefer medium difficulty (2-3) and frequent subtopics
        def problem_score(p):
            diff = getattr(p, 'difficulty', 'medium')
            diff_score = 0 if diff == 'medium' else (1 if diff == 'easy' else 2)

            # Bonus for matching frequent subtopics
            subtopic_bonus = 0
            p_subtopics = getattr(p, 'subtopics', [])
            for ps in p_subtopics:
                if ps in frequent_subtopics:
                    subtopic_bonus = -1  # Lower score = higher priority
                    break

            return (diff_score + subtopic_bonus, random.random())

        sorted_problems = sorted(problems, key=problem_score)

        # Select 3 problems for this topic
        selected_problems = sorted_problems[:3]

        # Determine if this is the "next" topic or just "upcoming"
        is_next = topic not in practiced_topics and len(recommendations) == 0

        rec_type = "core_skill"  # Sweep = systematic coverage
        reason = f"Chapter {topics_ordered.index(topic) + 1}: Start here" if is_next else f"Chapter {topics_ordered.index(topic) + 1}"

        recommendations.append({
            "id": f"sweep_{topic}",
            "type": rec_type,
            "title": display_name,
            "subtitle": f"{len(selected_problems)} problems to start",
            "status": "recommended" if is_next else "available",
            "reason": reason,
            "topic": topic,
            "problemIds": [p.id for p in selected_problems],
            "problemCount": len(problems),
            "weight": 100 - topics_ordered.index(topic),  # Earlier topics = higher weight
            "isSweep": True,  # Flag for frontend to know this is sweep mode
        })

    logger.info(f"[SWEEP] Generated {len(recommendations)} sweep recommendations")
    return recommendations


def recommend_problems_for_api(
    course: str,
    profile: Optional[StudentProfileV2] = None,
    recent_attempts: Optional[list] = None,
    limit: int = 5
) -> list[dict]:
    """
    Generate problem recommendations for API endpoint.

    Returns a list of checkpoint-style recommendations that can be
    directly used by the frontend Dashboard.

    Args:
        course: Course code ("124", "125", "126")
        profile: StudentProfileV2 from workspace context (optional)
        recent_attempts: List of recent attempt dicts from DB (optional)
        limit: Max recommendations to return

    Returns:
        List of recommendation dicts with structure:
        {
            "id": "rec_<topic>",
            "type": "prerequisite" | "core_skill" | "exam_pattern",
            "title": "Topic Display Name",
            "subtitle": "N problems · X pts on exams",
            "status": "recommended" | "available",
            "reason": "Why this is recommended",
            "topic": "topic_slug",
            "problemIds": ["id1", "id2", ...],
            "problemCount": N,
            "weight": float,
        }
    """
    # ============================================================
    # SWEEP vs FOCUS phase detection
    # ============================================================
    if _is_new_user(profile, recent_attempts):
        logger.info(f"[RECOMMENDER] User is NEW → SWEEP phase (course={course})")
        return generate_sweep_recommendations(course, profile, recent_attempts, limit)

    logger.info(f"[RECOMMENDER] User has history → FOCUS phase (course={course})")

    # ============================================================
    # FOCUS phase: existing logic (prioritize weak topics)
    # ============================================================
    from app.content.problem_loader import load_problems
    import random

    # Load all problems for the course
    all_problems = load_problems(course)

    # Group problems by topic
    topic_problems = {}
    for p in all_problems:
        if not p.topic:
            continue
        if p.topic not in topic_problems:
            topic_problems[p.topic] = []
        topic_problems[p.topic].append(p)

    recommendations = []

    # Get priority topics from profile (if available)
    priority_topics = []
    weak_subtopics = []
    if profile:
        priority_topics = profile.get_priority_topics()
        weak_subtopics = profile.get_all_priority_subtopics(limit=10)

    # Build topic scores
    topic_scores = {}
    for topic, problems in topic_problems.items():
        score = 0.0

        # Base score from problem count (more problems = more exam weight)
        score += len(problems) * 2

        # Priority boost from profile
        if topic in priority_topics:
            rank = priority_topics.index(topic)
            score += max(0, 50 - rank * 10)

        # Weak subtopic boost
        for (t, sub) in weak_subtopics:
            if t == topic:
                score += 30

        # Recent failure boost
        if recent_attempts:
            recent_topic_attempts = [
                a for a in recent_attempts
                if a.get("topic") == topic
            ]
            recent_failures = sum(
                1 for a in recent_topic_attempts[:5]
                if not a.get("is_correct")
            )
            score += recent_failures * 15

        topic_scores[topic] = score

    # Sort topics by score
    sorted_topics = sorted(
        topic_scores.items(),
        key=lambda x: -x[1]
    )

    # Generate recommendations
    for i, (topic, score) in enumerate(sorted_topics[:limit]):
        problems = topic_problems[topic]
        display_name = get_topic_display_name(topic)

        # Determine recommendation type and status
        is_priority = topic in priority_topics[:3] if profile else False
        is_weak = any(t == topic for (t, _) in weak_subtopics[:5])

        if is_weak:
            rec_type = "prerequisite"
            reason = f"Diagnostic showed weakness in this area"
        elif is_priority:
            rec_type = "core_skill"
            reason = f"Priority topic based on your performance"
        else:
            rec_type = "exam_pattern"
            reason = f"High-frequency exam topic ({len(problems)} problems)"

        # Select problems to recommend
        # Prefer medium difficulty, then shuffle
        problem_pool = sorted(
            problems,
            key=lambda p: (
                0 if getattr(p, 'difficulty', 'medium') == 'medium' else
                1 if getattr(p, 'difficulty', 'medium') == 'easy' else 2
            )
        )

        # Add some randomness
        if len(problem_pool) > 5:
            problem_pool = random.sample(problem_pool[:10], min(5, len(problem_pool)))

        recommendations.append({
            "id": f"rec_{topic}",
            "type": rec_type,
            "title": display_name,
            "subtitle": f"{len(problems)} problems available",
            "status": "recommended" if i == 0 else "available",
            "reason": reason,
            "topic": topic,
            "problemIds": [p.id for p in problem_pool[:5]],
            "problemCount": len(problems),
            "weight": score,
        })

    return recommendations
