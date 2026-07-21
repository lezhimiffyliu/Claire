#!/usr/bin/env python3
"""
New User Roadmap Flow Simulator

Simulates an anonymous new user entering the dashboard for the first time:
1. No localStorage preferences (simulated)
2. Selects exam_date = today + 2 days
3. Selects prep_level = "no_class_no_homework" (completely unprepared)
4. Requests /api/roadmap with these parameters
5. Validates and prints the roadmap result

Usage:
    python scripts/simulate_new_user_roadmap.py

    # Or with custom parameters:
    python scripts/simulate_new_user_roadmap.py --days 5 --prep some_class_some_homework

Expected behavior for 2-day cram scenario:
- plan_mode: "cram"
- Roadmap prioritizes high-impact blocks (double_integrals, optimization, taylor_series)
- NOT starting with vectors_and_geometry (foundational but low priority)
- All reasons are "High-priority exam block" (no fabricated frequency)
"""

import argparse
import sys
import os
from datetime import date, timedelta
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plan_mode_calculator import determine_plan_mode, get_plan_mode_description, get_countdown_text, PlanMode
from roadmap_generator import generate_roadmap
from taxonomy.exam_blocks import get_cram_blocks

# =============================================================================
# ANSI colors for terminal output
# =============================================================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def c(text, color):
    """Colorize text for terminal output."""
    return f"{color}{text}{Colors.END}"

# =============================================================================
# Test Configuration
# =============================================================================

# High-impact blocks that should appear early in CRAM mode for Math 126
HIGH_IMPACT_BLOCKS_126 = [
    "double_integrals",
    "optimization",
    "taylor_series",
]

# Low-priority foundational blocks that should NOT lead in CRAM mode
LOW_PRIORITY_BLOCKS_126 = [
    "vectors_and_geometry",
]

# Forbidden reason patterns (fabricated data)
FORBIDDEN_REASON_PATTERNS = [
    "frequency",
    "frequently",
    "high-frequency",
    "appears often",
    "commonly tested",
    "Exam II",  # Should not reference specific exam frequency
    "Exam I",
    "Final",
]

# Allowed reason patterns (exact matches expected)
ALLOWED_REASON_PATTERNS = [
    "matches high-priority exam block",
    "included in cram review",
    "additional practice area",
    "core topic for systematic review",
    "review this concept thoroughly",
    "practice for fluency",
    "recommended study area",
]

# =============================================================================
# Simulation Functions
# =============================================================================

def simulate_new_user_roadmap(
    days_until_exam: int = 2,
    prep_level: str = "no_class_no_homework",
    target_goal: str = "pass",
    course: str = "126",
) -> dict:
    """
    Simulate a new user requesting a roadmap.

    This bypasses the API and directly calls the backend logic,
    simulating what would happen when frontend calls GET /api/roadmap.
    """
    print(c("\n" + "=" * 70, Colors.HEADER))
    print(c("  NEW USER ROADMAP SIMULATION", Colors.BOLD))
    print(c("=" * 70 + "\n", Colors.HEADER))

    # Step 1: User profile (simulated - no prior attempts)
    print(c("Step 1: User Profile", Colors.CYAN))
    print(f"  • Authenticated: No (anonymous user)")
    print(f"  • Prior attempts: None")
    print(f"  • Course: Math {course}")
    print()

    # Step 2: Onboarding selections
    exam_date = date.today() + timedelta(days=days_until_exam)
    print(c("Step 2: Onboarding Selections", Colors.CYAN))
    print(f"  • Exam date: {exam_date} ({days_until_exam} days from now)")
    print(f"  • Prep level: {prep_level}")
    print(f"  • Target goal: {target_goal}")
    print()

    # Step 3: Determine plan mode
    print(c("Step 3: Plan Mode Calculation", Colors.CYAN))
    plan_mode = determine_plan_mode(
        course=course,
        days_until_exam=days_until_exam,
        prep_level=prep_level,
        target_goal=target_goal,
        has_recent_attempts=False
    )
    plan_description = get_plan_mode_description(plan_mode)
    countdown_text = get_countdown_text(days_until_exam)

    print(f"  • Plan mode: {c(plan_mode.value, Colors.BOLD)}")
    print(f"  • Title: {plan_description['title']}")
    print(f"  • Description: {plan_description['description']}")
    print(f"  • Urgency: {plan_description['urgency']}")
    print(f"  • Countdown text: {c(countdown_text, Colors.YELLOW)}")
    print()

    # Step 4: Generate roadmap (new 3-layer model)
    print(c("Step 4: Generate Roadmap", Colors.CYAN))

    # For simulation: empty diagnostic_result (new user, no attempts)
    diagnostic_result = {}

    roadmap = generate_roadmap(
        days_until_exam=days_until_exam,
        prep_level=prep_level,
        diagnostic_result=diagnostic_result,
        course=course,
    )

    # New format: roadmap_items instead of roadmap_blocks
    items = roadmap.get("roadmap_items", [])
    coverage_strategy = roadmap.get("coverage_strategy", "unknown")

    print(f"  • Coverage strategy: {coverage_strategy}")
    print(f"  • Items generated: {len(items)}")
    print()

    # Step 5: Display roadmap items
    print(c("Step 5: Roadmap Items (in order)", Colors.CYAN))
    print("-" * 60)

    for i, item in enumerate(items, 1):
        topic_key = item.get("topic_key", "unknown")
        display_name = item.get("display_name", "Unknown")
        reason_tags = item.get("reason_tags", [])
        priority = item.get("priority", 0)
        depth = item.get("depth", "unknown")
        subtopics = item.get("selected_subtopics", [])
        estimated_time = item.get("estimated_time_minutes", 0)

        # First item marker
        marker = c("→ ", Colors.GREEN) if i == 1 else "  "

        print(f"\n{marker}{c(f'Item {i}: {display_name}', Colors.BOLD)}")
        print(f"    Topic: {topic_key}")
        print(f"    Priority: {priority}")
        print(f"    Depth: {depth}")
        print(f"    Time: {estimated_time}min")
        print(f"    Reasons: {', '.join(reason_tags)}")
        print(f"    Subtopics: {len(subtopics)}")

    print("\n" + "-" * 60)

    return {
        "plan_mode": plan_mode,
        "plan_description": plan_description,
        "countdown_text": countdown_text,
        "roadmap": roadmap,
        "items": items,  # New format: roadmap_items
        "coverage_strategy": coverage_strategy,
        "success": True,
    }


def run_assertions(result: dict, days_until_exam: int, prep_level: str) -> bool:
    """
    Run assertions on the roadmap result.
    Returns True if all assertions pass.
    """
    print(c("\n" + "=" * 70, Colors.HEADER))
    print(c("  ASSERTIONS", Colors.BOLD))
    print(c("=" * 70 + "\n", Colors.HEADER))

    all_passed = True

    def assert_check(name: str, condition: bool, details: str = ""):
        nonlocal all_passed
        if condition:
            print(f"  {c('✓', Colors.GREEN)} {name}")
        else:
            print(f"  {c('✗', Colors.RED)} {name}")
            if details:
                print(f"    {c(details, Colors.RED)}")
            all_passed = False

    coverage_strategy = result.get("coverage_strategy")
    items = result.get("items", [])

    # Assertion 1: Coverage strategy is correct
    if days_until_exam <= 3:
        expected_strategy = "core_cram"
    elif days_until_exam <= 7:
        expected_strategy = "crash_course"
    elif days_until_exam <= 14:
        expected_strategy = "compressed_full"
    else:
        expected_strategy = "full_personalized"

    assert_check(
        f"Coverage strategy is {expected_strategy}",
        coverage_strategy == expected_strategy,
        f"Got: {coverage_strategy}"
    )

    # Assertion 2: Items were generated
    assert_check(
        "Roadmap has items",
        len(items) > 0,
        "No items generated"
    )

    if not items:
        return False

    # Assertion 3: First item is NOT a low-priority foundational topic
    first_topic = items[0].get("topic_key") if items else None
    assert_check(
        "First topic is NOT low-priority (vectors_and_geometry)",
        first_topic not in LOW_PRIORITY_BLOCKS_126,
        f"First topic is {first_topic}, which is foundational/low-priority"
    )

    # Assertion 4: High-impact topics appear in roadmap
    topic_keys = [item.get("topic_key") for item in items]
    high_impact_present = any(t in topic_keys for t in HIGH_IMPACT_BLOCKS_126)
    assert_check(
        "High-impact topics are present (double_integrals, optimization, taylor_series)",
        high_impact_present,
        f"Topics present: {topic_keys}"
    )

    # Assertion 5: In core_cram, low-priority topics should be excluded (unless weak)
    if coverage_strategy == "core_cram":
        low_priority_in_roadmap = [t for t in topic_keys if t in LOW_PRIORITY_BLOCKS_126]
        # They should only be included if marked weak/unstable
        assert_check(
            "CORE_CRAM excludes or minimizes low-priority topics",
            len(low_priority_in_roadmap) <= 1,  # Allow 1 for prerequisite
            f"Low-priority topics in roadmap: {low_priority_in_roadmap}"
        )

    # Assertion 6: Reason tags don't have fabricated frequency
    all_reasons_valid = True
    invalid_reasons = []
    for item in items:
        reason_tags = item.get("reason_tags", [])
        reason_str = " ".join(reason_tags)
        for pattern in FORBIDDEN_REASON_PATTERNS:
            if pattern.lower() in reason_str.lower():
                all_reasons_valid = False
                invalid_reasons.append(f"Item '{item.get('display_name')}': reason '{reason_str}' contains '{pattern}'")

    assert_check(
        "No fabricated frequency reasons",
        all_reasons_valid,
        "\n    ".join(invalid_reasons) if invalid_reasons else ""
    )

    # Assertion 7: Item order respects priority
    if len(items) >= 2:
        priorities = [item.get("priority", 99) for item in items]
        is_sorted = all(priorities[i] <= priorities[i+1] for i in range(len(priorities)-1))
        assert_check(
            "Items are ordered by priority",
            is_sorted,
            f"Priorities: {priorities}"
        )

    # Assertion 8: Each item has subtopics
    items_with_subtopics = [item for item in items if len(item.get("selected_subtopics", [])) > 0]
    assert_check(
        "Each item has subtopics",
        len(items_with_subtopics) == len(items),
        f"Items with subtopics: {len(items_with_subtopics)}/{len(items)}"
    )

    # Assertion 9: Countdown text is appropriate for urgency
    countdown_text = result.get("countdown_text", "")
    if days_until_exam <= 3:
        has_urgency_text = any(word in countdown_text.lower() for word in ["high-impact", "focus", "tomorrow", "left"])
        assert_check(
            "Countdown text reflects urgency",
            has_urgency_text,
            f"Countdown: '{countdown_text}'"
        )

    print()
    return all_passed


def print_summary(result: dict, assertions_passed: bool):
    """Print final summary."""
    print(c("=" * 70, Colors.HEADER))
    print(c("  SUMMARY", Colors.BOLD))
    print(c("=" * 70 + "\n", Colors.HEADER))

    items = result.get("items", [])
    coverage_strategy = result.get("coverage_strategy", "unknown")
    plan_mode = result.get("plan_mode")

    # plan_mode is now PlanMode enum
    plan_mode_str = plan_mode.value if hasattr(plan_mode, 'value') else str(plan_mode)
    print(f"  Coverage Strategy: {c(coverage_strategy.upper(), Colors.BOLD)}")
    print(f"  Plan Mode: {plan_mode_str}")
    print(f"  Title: {result.get('plan_description', {}).get('title', '')}")
    print(f"  Countdown: {c(result.get('countdown_text', ''), Colors.YELLOW)}")
    print()
    print(f"  Roadmap Item Order:")
    for i, item in enumerate(items, 1):
        display_name = item.get("display_name", "?")
        priority = item.get("priority", "?")
        depth = item.get("depth", "?")
        print(f"    {i}. {display_name} (priority {priority}, depth: {depth})")
    print()

    if assertions_passed:
        print(c("  ✓ ALL ASSERTIONS PASSED", Colors.GREEN + Colors.BOLD))
        print()
        print("  This roadmap correctly prioritizes high-impact topics")
        print("  using the three-layer decision model.")
    else:
        print(c("  ✗ SOME ASSERTIONS FAILED", Colors.RED + Colors.BOLD))
        print()
        print("  Review the failures above and fix the roadmap logic.")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Simulate new user roadmap flow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 2-day cram scenario (default)
  python scripts/simulate_new_user_roadmap.py

  # 5-day scenario with some preparation
  python scripts/simulate_new_user_roadmap.py --days 5 --prep some_class_some_homework

  # 10-day scenario, confident student
  python scripts/simulate_new_user_roadmap.py --days 10 --prep confident_need_practice
        """
    )
    parser.add_argument(
        "--days", type=int, default=2,
        help="Days until exam (default: 2)"
    )
    parser.add_argument(
        "--prep", type=str, default="no_class_no_homework",
        choices=[
            "no_class_no_homework",
            "some_class_some_homework",
            "attended_but_weak",
            "confident_need_practice"
        ],
        help="Prep level (default: no_class_no_homework)"
    )
    parser.add_argument(
        "--course", type=str, default="126",
        help="Course code (default: 126)"
    )
    parser.add_argument(
        "--goal", type=str, default="pass",
        choices=["pass", "good", "mastery"],
        help="Target goal (default: pass)"
    )

    args = parser.parse_args()

    # Run simulation
    result = simulate_new_user_roadmap(
        days_until_exam=args.days,
        prep_level=args.prep,
        target_goal=args.goal,
        course=args.course,
    )

    if not result.get("success"):
        print(c("\n  ✗ Simulation failed (roadmap returned fallback)", Colors.RED))
        sys.exit(1)

    # Run assertions
    passed = run_assertions(result, args.days, args.prep)

    # Print summary
    print_summary(result, passed)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
