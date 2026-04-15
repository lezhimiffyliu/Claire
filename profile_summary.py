"""
Profile Summary Builder - generates compact context for LLM.

The LLM should NOT read full history.
Instead, it reads a structured summary of the student state.
"""

from student_state import StudentState


def build_profile_summary(state: StudentState) -> str:
    """
    Build a compact text summary of student state for LLM context.

    This is what the agent reads - not raw history.
    Keep it concise but informative.
    """
    lines = []

    # Course
    course_names = {"124": "Math 124 (Calc I)", "125": "Math 125 (Calc II)", "126": "Math 126 (Calc III)"}
    lines.append(f"Course: {course_names.get(state.course, state.course)}")

    # Overall stats
    total = state.total_correct + state.total_incorrect
    if total > 0:
        lines.append(f"Overall: {state.total_correct}/{total} correct ({state.overall_accuracy:.0%})")

    # Weak topics
    weak = state.get_weak_topics(limit=3)
    if weak:
        weak_str = ", ".join(t.replace("_", " ") for t in weak)
        lines.append(f"Weak topics: {weak_str}")

    # Strong topics
    strong = state.get_strong_topics(limit=3)
    if strong:
        strong_str = ", ".join(t.replace("_", " ") for t in strong)
        lines.append(f"Stronger areas: {strong_str}")

    # Weak concepts
    weak_concepts = state.get_weak_concepts(limit=3)
    if weak_concepts:
        concept_str = ", ".join(c.replace("_", " ") for c in weak_concepts)
        lines.append(f"Weak concepts: {concept_str}")

    # Error pattern
    dominant = state.get_dominant_error_type()
    if dominant:
        error_desc = {
            "concept": "conceptual misunderstanding",
            "algebra": "algebraic mistakes",
            "logic": "logical errors",
            "careless": "careless slips",
        }
        lines.append(f"Common error type: {error_desc.get(dominant, dominant)}")

    # Orthogonal weaknesses
    ortho_weak = state.orthogonal.get_weaknesses()
    if ortho_weak.get("skill_type"):
        lines.append(f"Struggles with: {', '.join(ortho_weak['skill_type'])} problems")
    if ortho_weak.get("representation"):
        lines.append(f"Weak on: {', '.join(ortho_weak['representation'])} format")
    if ortho_weak.get("difficulty"):
        diff_map = {"routine": "basic", "standard": "medium", "challenging": "hard"}
        diff_str = ", ".join(diff_map.get(d, d) for d in ortho_weak["difficulty"])
        lines.append(f"Difficulty gap: {diff_str} problems")

    # Foundation flag
    if state.needs_foundation_work:
        if state.foundation_topics:
            topics = ", ".join(t.replace("_", " ") for t in state.foundation_topics[:2])
            lines.append(f"Needs foundation review: {topics}")
        else:
            lines.append("Needs foundation review")

    # Preferences
    feedback_style = state.preferences.get("feedback_style", "hint_first")
    if feedback_style == "hint_first":
        lines.append("Prefers: hints before full solutions")
    elif feedback_style == "direct":
        lines.append("Prefers: direct explanations")
    elif feedback_style == "socratic":
        lines.append("Prefers: guided questions")

    return "\n".join(lines)


def build_teaching_context(state: StudentState, current_topic: str) -> str:
    """
    Build context specifically for teaching/feedback generation.
    More focused on how to help this student.
    """
    lines = []

    # Topic-specific state
    if current_topic:
        topic_ms = state.get_topic_mastery(current_topic)
        topic_name = current_topic.replace("_", " ")

        if topic_ms.attempts > 0:
            lines.append(f"On {topic_name}: {topic_ms.correct}/{topic_ms.attempts} correct")
            lines.append(f"Current level: {topic_ms.mastery_level}")
            lines.append(f"Recent trend: {topic_ms.recent_trend}")

            if topic_ms.streak <= -2:
                lines.append(f"⚠️ Struggling: {abs(topic_ms.streak)} wrong in a row")
            elif topic_ms.streak >= 3:
                lines.append(f"✓ On a roll: {topic_ms.streak} correct in a row")

    # Dominant error pattern affects teaching style
    dominant = state.get_dominant_error_type()
    if dominant == "concept":
        lines.append("Teaching note: Focus on conceptual understanding, not just procedure")
    elif dominant == "algebra":
        lines.append("Teaching note: Emphasize careful computation, show intermediate steps")
    elif dominant == "logic":
        lines.append("Teaching note: Break down reasoning, explain WHY each step")
    elif dominant == "careless":
        lines.append("Teaching note: Encourage double-checking, student knows the material")

    # Foundation context
    if state.needs_foundation_work and current_topic in state.foundation_topics:
        lines.append("⚠️ This is a foundation topic - may need prerequisite review")

    return "\n".join(lines)


def build_recommendation_context(state: StudentState) -> dict:
    """
    Build structured data for the recommender system.
    Returns a dict, not text.
    """
    return {
        "weak_topics": state.get_weak_topics(limit=5),
        "weak_concepts": state.get_weak_concepts(limit=5),
        "foundation_topics": state.foundation_topics if state.needs_foundation_work else [],
        "needs_foundation": state.needs_foundation_work,
        "overall_accuracy": state.overall_accuracy,
        "orthogonal_weaknesses": state.orthogonal.get_weaknesses(),
        "diagnostic_weak": state.diagnostic_weak_topics,
    }
