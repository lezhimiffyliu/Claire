"""
Plan Mode Calculator - Rule-based plan mode determination.

NO LLM involved. Uses exam date, prep level, and goals to determine
the appropriate study plan mode.

Plan Modes:
- CRAM: <= 3 days, focus on high-impact topics only
- CRASH_COURSE: 4-7 days or unprepared, systematic sweep
- CRAM_TARGETED: 4-7 days but somewhat prepared, targeted practice
- TARGETED_REVIEW: > 7 days, tier 3 (attended but weak)
- TARGETED_PRACTICE: > 7 days, tier 4 (confident, need practice)
- SWEEP: fallback for no data - go through all topics
- FOCUS: fallback with attempts - focus on weak areas
"""

from enum import Enum
from typing import Optional


class PlanMode(str, Enum):
    """Study plan modes based on time and preparation level."""
    CRAM = "cram"
    CRASH_COURSE = "crash_course"
    CRAM_TARGETED = "cram_targeted"
    TARGETED_REVIEW = "targeted_review"
    TARGETED_PRACTICE = "targeted_practice"
    SWEEP = "sweep"
    FOCUS = "focus"


# Prep level to tier mapping
# Lower tier = less prepared
PREP_LEVEL_TIER = {
    "no_class_no_homework": 1,      # Missed most classes/homework
    "some_class_some_homework": 2,  # Sporadic attendance
    "attended_but_weak": 3,         # Attended but feel weak
    "confident_need_practice": 4,   # Confident, need practice
}


def determine_plan_mode(
    course: str,
    days_until_exam: Optional[int],
    prep_level: Optional[str],
    target_goal: Optional[str],
    has_recent_attempts: bool
) -> PlanMode:
    """
    Rule-based plan mode determination. NO LLM.

    Args:
        course: Course code (e.g., "126")
        days_until_exam: Days until the exam (None if not set)
        prep_level: Student's self-reported prep level
        target_goal: Target grade goal ("pass", "good", "mastery")
        has_recent_attempts: Whether student has recent practice attempts

    Returns:
        PlanMode enum value
    """
    # Fallback if missing required data
    if days_until_exam is None or prep_level is None:
        return PlanMode.SWEEP if not has_recent_attempts else PlanMode.FOCUS

    tier = PREP_LEVEL_TIER.get(prep_level, 2)

    # CRAM: 3 days or less - high-impact topics only
    if days_until_exam <= 3:
        return PlanMode.CRAM

    # 4-7 days: depends on prep level
    if days_until_exam <= 7:
        if tier <= 2:
            # Unprepared - need systematic coverage
            return PlanMode.CRASH_COURSE
        else:
            # Somewhat prepared - targeted practice
            return PlanMode.CRAM_TARGETED

    # > 7 days: more time for targeted work
    if tier <= 2:
        # Still need systematic coverage
        return PlanMode.CRASH_COURSE
    elif tier == 3:
        # Attended but weak - review concepts
        return PlanMode.TARGETED_REVIEW
    else:
        # Confident - just need practice
        return PlanMode.TARGETED_PRACTICE


def get_plan_mode_description(mode: PlanMode) -> dict:
    """
    Get human-readable description of a plan mode.

    Returns:
        Dict with title, description, and icon
    """
    descriptions = {
        PlanMode.CRAM: {
            "title": "Cram Mode",
            "description": "Focus on highest-impact topics. Skip low-priority areas.",
            "icon": "fire",
            "urgency": "critical",
        },
        PlanMode.CRASH_COURSE: {
            "title": "Crash Course",
            "description": "Systematic coverage of all major topics with prioritization.",
            "icon": "rocket",
            "urgency": "high",
        },
        PlanMode.CRAM_TARGETED: {
            "title": "Targeted Cram",
            "description": "Focus on weak areas and high-frequency exam topics.",
            "icon": "target",
            "urgency": "high",
        },
        PlanMode.TARGETED_REVIEW: {
            "title": "Targeted Review",
            "description": "Reinforce concepts you've learned but don't feel solid on.",
            "icon": "book",
            "urgency": "moderate",
        },
        PlanMode.TARGETED_PRACTICE: {
            "title": "Practice Mode",
            "description": "Build fluency through problem practice.",
            "icon": "pencil",
            "urgency": "low",
        },
        PlanMode.SWEEP: {
            "title": "Full Sweep",
            "description": "Explore all topics systematically.",
            "icon": "compass",
            "urgency": "low",
        },
        PlanMode.FOCUS: {
            "title": "Smart Focus",
            "description": "Focus on your weak areas based on past practice.",
            "icon": "crosshair",
            "urgency": "moderate",
        },
    }
    return descriptions.get(mode, {
        "title": mode.value.replace("_", " ").title(),
        "description": "Study plan",
        "icon": "book",
        "urgency": "moderate",
    })


def get_countdown_text(days_until_exam: Optional[int]) -> Optional[str]:
    """
    Generate countdown text for UI display.

    Args:
        days_until_exam: Days until exam (None if not set)

    Returns:
        Formatted countdown text or None
    """
    if days_until_exam is None:
        return None

    if days_until_exam <= 0:
        return "Exam day - you've got this!"
    elif days_until_exam == 1:
        return "Exam tomorrow - focus on what you know!"
    elif days_until_exam <= 3:
        return f"{days_until_exam} days left - high-impact topics only"
    elif days_until_exam <= 7:
        return f"{days_until_exam} days left - stay focused"
    else:
        return f"{days_until_exam} days until exam"
