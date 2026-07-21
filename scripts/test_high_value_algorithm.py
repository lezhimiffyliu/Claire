#!/usr/bin/env python3
"""
Test the new high_value_sections algorithm with actual exam data.

Shows top 3 with:
- topic / section id
- count
- avg_points (computed)
- expected_loss
- diagnostic status
- color_family
- why included / excluded
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roadmap_generator import generate_high_value_sections

# ANSI colors
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def run_test():
    print(f"\n{C.BOLD}{'='*70}{C.END}")
    print(f"{C.BOLD}HIGH VALUE SECTIONS - Expected Loss Algorithm Test{C.END}")
    print(f"{C.BOLD}{'='*70}{C.END}\n")

    # Simulate a typical user scenario: 3 days until exam, no diagnostic data
    days_until_exam = 3
    diagnostic_result = {}  # New user, no diagnostic data

    print(f"Test parameters:")
    print(f"  days_until_exam: {days_until_exam}")
    print(f"  diagnostic_result: {diagnostic_result} (new user)")
    print(f"  course: 126")
    print(f"  num_recent_exams: 5")
    print()

    result = generate_high_value_sections(
        days_until_exam=days_until_exam,
        diagnostic_result=diagnostic_result,
        course="126",
        num_recent_exams=5,
    )

    high_value_topics = result["high_value_topics"]
    debug_report = result["debug_report"]

    print(f"{C.BOLD}Algorithm Parameters:{C.END}")
    print(f"  num_recent_exams: {debug_report['num_recent_exams']}")
    print(f"  top_k (from days_until_exam): {debug_report['top_k']}")
    print()

    # Show all topics with their stats
    print(f"{C.BOLD}All Topics Analysis (sorted by expected_loss):{C.END}")
    print("-" * 90)
    print(f"{'Topic':<35} {'Count':>5} {'AvgPts':>7} {'ExpLoss':>8} {'Diag':>8} {'Color':>8} {'Status'}")
    print("-" * 90)

    for t in debug_report["all_topics"]:
        topic = t["topic"][:33]
        count = t["count"]
        avg_pts = t["avg_points"]
        exp_loss = t["expected_loss"]
        diag = t["diagnostic"]
        color = t["color_family"]
        reason = t["reason"]

        # Color code the status
        if "✓ 入选" in reason:
            status_color = C.GREEN
        elif "已有" in reason or "ok" in reason:
            status_color = C.YELLOW
        elif "count" in reason.lower() or "avg_points" in reason.lower():
            status_color = C.RED
        else:
            status_color = ""

        print(f"{topic:<35} {count:>5} {avg_pts:>7.1f} {exp_loss:>8.2f} {diag:>8} {color:>8} {status_color}{reason}{C.END}")

    print("-" * 90)
    print()

    # Show selected high-value topics
    print(f"{C.BOLD}{C.GREEN}Selected High Value Topics (top {debug_report['top_k']}):{C.END}")
    print("=" * 70)

    for i, item in enumerate(high_value_topics, 1):
        print(f"\n{C.BOLD}#{i}: {item['display_name']}{C.END}")
        print(f"    topic: {item['topic']}")
        print(f"    expected_loss: {item['expected_loss']}")
        print(f"    count: {item['count']} (出现次数)")
        print(f"    avg_points: {item['avg_points']} (平均分值)")
        print(f"    diagnostic: {item['diagnostic']}")
        print(f"    color_family: {item['color_family']}")
        print(f"    is_weak: {item['is_weak']}")
        print(f"    sections:")
        for sec in item["sections"]:
            print(f"      - {sec['section_id']}: {sec['display_name']}")

    print("\n" + "=" * 70)

    # Additional test: with diagnostic data
    print(f"\n{C.BOLD}{'='*70}{C.END}")
    print(f"{C.BOLD}Test with diagnostic data (taylor=ok, optimization=weak):{C.END}")
    print(f"{C.BOLD}{'='*70}{C.END}\n")

    diagnostic_result_2 = {
        "taylor_polynomials_and_series": "ok",
        "multivariable_optimization": "weak",
    }

    result2 = generate_high_value_sections(
        days_until_exam=days_until_exam,
        diagnostic_result=diagnostic_result_2,
        course="126",
        num_recent_exams=5,
    )

    for i, item in enumerate(result2["high_value_topics"], 1):
        print(f"#{i}: {item['display_name']} (expected_loss={item['expected_loss']}, diag={item['diagnostic']})")

    # Show what changed
    print("\n" + "-" * 70)
    print("Changes from diagnostic filtering:")
    for t in result2["debug_report"]["all_topics"]:
        if t["topic"] == "taylor_polynomials_and_series":
            print(f"  taylor_polynomials_and_series: {t['reason']}")
        if t["topic"] == "multivariable_optimization":
            print(f"  multivariable_optimization: {t['reason']}")


if __name__ == "__main__":
    run_test()
