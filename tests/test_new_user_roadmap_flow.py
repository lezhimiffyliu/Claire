"""
Test: New User Roadmap Flow

Pytest tests for the personalized roadmap system.
Tests various scenarios for different exam timelines and prep levels.

Run with:
    pytest tests/test_new_user_roadmap_flow.py -v
"""

import pytest
import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plan_mode_calculator import (
    determine_plan_mode,
    get_plan_mode_description,
    get_countdown_text,
    PlanMode,
    PREP_LEVEL_TIER,
)
from roadmap_generator import generate_roadmap
from taxonomy.exam_blocks import get_blocks_for_course, get_cram_order


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def course():
    return "126"


@pytest.fixture
def high_impact_blocks():
    """Blocks that should be prioritized in CRAM mode."""
    return ["double_integrals", "optimization", "taylor_series"]


@pytest.fixture
def low_priority_blocks():
    """Blocks that should be deprioritized in CRAM mode."""
    return ["vectors_and_geometry"]


@pytest.fixture
def forbidden_reason_patterns():
    """Patterns that should NOT appear in reason text (fabricated data)."""
    return [
        "frequency",
        "frequently",
        "high-frequency",
        "appears often",
        "commonly tested",
        "Exam II",
        "Exam I",
        "Final",
    ]


# =============================================================================
# Plan Mode Tests
# =============================================================================

class TestPlanModeCalculation:
    """Tests for plan mode determination."""

    def test_cram_mode_2_days_unprepared(self, course):
        """2 days until exam, completely unprepared → CRAM mode."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=2,
            prep_level="no_class_no_homework",
            target_goal="pass",
            has_recent_attempts=False
        )
        assert mode == PlanMode.CRAM

    def test_cram_mode_3_days(self, course):
        """3 days until exam → CRAM mode regardless of prep level."""
        for prep_level in PREP_LEVEL_TIER.keys():
            mode = determine_plan_mode(
                course=course,
                days_until_exam=3,
                prep_level=prep_level,
                target_goal="pass",
                has_recent_attempts=False
            )
            assert mode == PlanMode.CRAM, f"Expected CRAM for 3 days with {prep_level}"

    def test_crash_course_5_days_unprepared(self, course):
        """5 days, unprepared → CRASH_COURSE."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=5,
            prep_level="no_class_no_homework",
            target_goal="pass",
            has_recent_attempts=False
        )
        assert mode == PlanMode.CRASH_COURSE

    def test_cram_targeted_5_days_prepared(self, course):
        """5 days, somewhat prepared → CRAM_TARGETED."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=5,
            prep_level="attended_but_weak",
            target_goal="pass",
            has_recent_attempts=False
        )
        assert mode == PlanMode.CRAM_TARGETED

    def test_targeted_practice_10_days_confident(self, course):
        """10 days, confident → TARGETED_PRACTICE."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=10,
            prep_level="confident_need_practice",
            target_goal="mastery",
            has_recent_attempts=True
        )
        assert mode == PlanMode.TARGETED_PRACTICE

    def test_sweep_no_data(self, course):
        """No exam date or prep level → SWEEP (default)."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=None,
            prep_level=None,
            target_goal=None,
            has_recent_attempts=False
        )
        assert mode == PlanMode.SWEEP

    def test_focus_no_data_with_attempts(self, course):
        """No exam date but has attempts → FOCUS."""
        mode = determine_plan_mode(
            course=course,
            days_until_exam=None,
            prep_level=None,
            target_goal=None,
            has_recent_attempts=True
        )
        assert mode == PlanMode.FOCUS


# =============================================================================
# Roadmap Generation Tests
# =============================================================================

class TestRoadmapGeneration:
    """Tests for roadmap block generation."""

    def test_cram_mode_generates_blocks(self, course):
        """CRAM mode should generate non-empty roadmap."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        assert not roadmap.get("fallback"), "Roadmap should not fallback"
        assert len(roadmap.get("roadmap_blocks", [])) > 0, "Should have blocks"

    def test_cram_mode_excludes_low_priority(self, course, low_priority_blocks):
        """CRAM mode should exclude low-priority blocks."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        block_ids = [b.get("block_id") for b in roadmap.get("roadmap_blocks", [])]

        for low_priority in low_priority_blocks:
            assert low_priority not in block_ids, \
                f"Low-priority block '{low_priority}' should not be in CRAM roadmap"

    def test_cram_mode_includes_high_impact(self, course, high_impact_blocks):
        """CRAM mode should include high-impact blocks."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        block_ids = [b.get("block_id") for b in roadmap.get("roadmap_blocks", [])]

        for high_impact in high_impact_blocks:
            assert high_impact in block_ids, \
                f"High-impact block '{high_impact}' should be in CRAM roadmap"

    def test_cram_mode_first_block_is_high_impact(self, course, high_impact_blocks, low_priority_blocks):
        """First block in CRAM mode should NOT be low-priority."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        blocks = roadmap.get("roadmap_blocks", [])
        assert len(blocks) > 0

        first_block_id = blocks[0].get("block_id")
        assert first_block_id not in low_priority_blocks, \
            f"First block should not be low-priority, got: {first_block_id}"

    def test_blocks_ordered_by_priority(self, course):
        """Blocks should be ordered by cram_priority (ascending)."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        blocks = roadmap.get("roadmap_blocks", [])
        priorities = [b.get("priority", 99) for b in blocks]

        for i in range(len(priorities) - 1):
            assert priorities[i] <= priorities[i + 1], \
                f"Blocks not sorted by priority: {priorities}"

    def test_each_block_has_problems(self, course):
        """Each block should have representative problems."""
        roadmap = generate_roadmap(
            plan_mode=PlanMode.CRAM,
            course=course,
        )
        for block in roadmap.get("roadmap_blocks", []):
            items = block.get("items", [])
            assert len(items) > 0, \
                f"Block '{block.get('title')}' should have problems"

    def test_no_fabricated_reasons(self, course, forbidden_reason_patterns):
        """Reason text should not contain fabricated frequency claims."""
        for mode in [PlanMode.CRAM, PlanMode.CRASH_COURSE, PlanMode.CRAM_TARGETED]:
            roadmap = generate_roadmap(plan_mode=mode, course=course)

            for block in roadmap.get("roadmap_blocks", []):
                reason = block.get("reason", "")
                for pattern in forbidden_reason_patterns:
                    assert pattern.lower() not in reason.lower(), \
                        f"Block '{block.get('title')}' has fabricated reason: '{reason}' contains '{pattern}'"


# =============================================================================
# Countdown Text Tests
# =============================================================================

class TestCountdownText:
    """Tests for countdown text generation."""

    def test_countdown_2_days(self):
        """2 days should show high-impact focus."""
        text = get_countdown_text(2)
        assert "high-impact" in text.lower() or "days left" in text.lower()

    def test_countdown_1_day(self):
        """1 day should show tomorrow urgency."""
        text = get_countdown_text(1)
        assert "tomorrow" in text.lower()

    def test_countdown_0_days(self):
        """0 days (exam day) should show encouragement."""
        text = get_countdown_text(0)
        assert "exam" in text.lower() or "got this" in text.lower()

    def test_countdown_14_days(self):
        """14 days should show normal countdown."""
        text = get_countdown_text(14)
        assert "14" in text

    def test_countdown_none(self):
        """None days should return None."""
        text = get_countdown_text(None)
        assert text is None


# =============================================================================
# Integration Test: Full New User Flow
# =============================================================================

class TestNewUserFlow:
    """Integration test simulating complete new user experience."""

    def test_2_day_cram_scenario(self, course, high_impact_blocks):
        """
        Complete flow: 2 days until exam, completely unprepared.

        Expected:
        - Plan mode: CRAM
        - High-impact blocks prioritized
        - Low-priority blocks excluded
        - No fabricated reasons
        """
        # Step 1: Determine plan mode
        plan_mode = determine_plan_mode(
            course=course,
            days_until_exam=2,
            prep_level="no_class_no_homework",
            target_goal="pass",
            has_recent_attempts=False
        )
        assert plan_mode == PlanMode.CRAM

        # Step 2: Get plan description
        description = get_plan_mode_description(plan_mode)
        assert description["urgency"] == "critical"
        assert "highest-impact" in description["description"].lower() or "high-impact" in description["description"].lower()

        # Step 3: Get countdown text
        countdown = get_countdown_text(2)
        assert countdown is not None
        assert "2" in countdown

        # Step 4: Generate roadmap
        roadmap = generate_roadmap(plan_mode=plan_mode, course=course)
        blocks = roadmap.get("roadmap_blocks", [])

        # Step 5: Validate roadmap structure
        assert len(blocks) > 0, "Roadmap should have blocks"
        assert roadmap.get("current_block") is not None, "Should have current block"

        # Step 6: Validate block priorities
        block_ids = [b.get("block_id") for b in blocks]
        for high_impact in high_impact_blocks:
            assert high_impact in block_ids, \
                f"High-impact block {high_impact} missing"

        # Step 7: Validate no low-priority blocks in CRAM
        assert "vectors_and_geometry" not in block_ids

        # Step 8: Each block has problems
        for block in blocks:
            assert len(block.get("items", [])) > 0

    def test_10_day_targeted_scenario(self, course):
        """
        Complete flow: 10 days until exam, confident student.

        Expected:
        - Plan mode: TARGETED_PRACTICE
        - All blocks included
        - Focus on practice
        """
        plan_mode = determine_plan_mode(
            course=course,
            days_until_exam=10,
            prep_level="confident_need_practice",
            target_goal="mastery",
            has_recent_attempts=True
        )
        assert plan_mode == PlanMode.TARGETED_PRACTICE

        roadmap = generate_roadmap(plan_mode=plan_mode, course=course)
        blocks = roadmap.get("roadmap_blocks", [])

        # Should include more blocks than CRAM mode
        cram_roadmap = generate_roadmap(plan_mode=PlanMode.CRAM, course=course)
        cram_blocks = cram_roadmap.get("roadmap_blocks", [])

        assert len(blocks) >= len(cram_blocks), \
            "TARGETED_PRACTICE should include at least as many blocks as CRAM"


# =============================================================================
# Run tests directly
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
