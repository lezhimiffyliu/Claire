"""
Math 126 Roadmap Generator

三层决策模型：
1. days_until_exam → coverage strategy
2. prep_level → depth
3. diagnostic_result → priority/depth调整（不接管roadmap）

核心原则：1-3天不是narrow weak-topic remediation，而是core-first cram。
Diagnostic只调权重，不接管roadmap。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Coverage Strategy (基于 days_until_exam)
# =============================================================================

class CoverageStrategy(str, Enum):
    CORE_CRAM = "core_cram"           # 1-3 days
    CRASH_COURSE = "crash_course"     # 4-7 days
    COMPRESSED_FULL = "compressed_full"  # 8-14 days
    FULL_PERSONALIZED = "full_personalized"  # 15+ days


def get_coverage_strategy(days_until_exam: int) -> CoverageStrategy:
    if days_until_exam <= 3:
        return CoverageStrategy.CORE_CRAM
    elif days_until_exam <= 7:
        return CoverageStrategy.CRASH_COURSE
    elif days_until_exam <= 14:
        return CoverageStrategy.COMPRESSED_FULL
    else:
        return CoverageStrategy.FULL_PERSONALIZED


# =============================================================================
# Prep Level → Depth
# =============================================================================

class PrepLevel(str, Enum):
    L1_ALMOST_NOTHING = "no_class_no_homework"
    L2_FRAGMENTED = "some_class_some_homework"
    L3_FOLLOWED_NOT_CONFIDENT = "attended_but_weak"
    L4_CONFIDENT = "confident_need_practice"


class Depth(str, Enum):
    FULL_REVIEW = "full_review"
    QUICK_REVIEW = "quick_review"
    TARGETED_REVIEW = "targeted_review"
    EXAM_DRILL = "exam_drill"
    MOCK_EXAM = "mock_exam"
    COMPRESSED = "compressed"
    SKIP = "skip"


def get_base_depth(prep_level: str, diagnostic_status: str) -> Depth:
    """根据prep_level和diagnostic_status决定基础depth"""

    if prep_level == PrepLevel.L1_ALMOST_NOTHING.value:
        if diagnostic_status == "weak":
            return Depth.FULL_REVIEW
        elif diagnostic_status == "unstable":
            return Depth.FULL_REVIEW
        elif diagnostic_status == "ok":
            return Depth.QUICK_REVIEW
        else:  # unknown
            return Depth.QUICK_REVIEW

    elif prep_level == PrepLevel.L2_FRAGMENTED.value:
        if diagnostic_status == "weak":
            return Depth.FULL_REVIEW
        elif diagnostic_status == "unstable":
            return Depth.QUICK_REVIEW
        elif diagnostic_status == "ok":
            return Depth.TARGETED_REVIEW
        else:
            return Depth.QUICK_REVIEW

    elif prep_level == PrepLevel.L3_FOLLOWED_NOT_CONFIDENT.value:
        if diagnostic_status == "weak":
            return Depth.TARGETED_REVIEW
        elif diagnostic_status == "unstable":
            return Depth.TARGETED_REVIEW
        elif diagnostic_status == "ok":
            return Depth.EXAM_DRILL
        else:
            return Depth.EXAM_DRILL

    else:  # L4_CONFIDENT
        if diagnostic_status == "weak":
            return Depth.TARGETED_REVIEW
        elif diagnostic_status == "unstable":
            return Depth.EXAM_DRILL
        elif diagnostic_status == "ok":
            return Depth.EXAM_DRILL
        else:
            return Depth.EXAM_DRILL


# =============================================================================
# Math 126 Topic Classification
# =============================================================================

# Course-specific topic configurations
# Based on exam frequency analysis for each course

COURSE_TOPICS = {
    "124": {
        # Math 124: curve_analysis 22.8%, derivative_rules 13.2%, related_rates 13.2%, optimization 12.5%
        "core": [
            "curve_analysis",
            "derivative_rules",
            "related_rates",
            "optimization",
            "lhopitals_rule",
        ],
        "non_core": [
            "limits",
            "continuity",
            "derivative_definition",
            "implicit_differentiation",
            "parametric_equations",
            "linear_approximation",
        ],
    },
    "125": {
        # Math 125: differential_equations 21.4%, applications 19.4%, substitution 11%, volumes 10.7%
        "core": [
            "differential_equations",
            "applications_of_integration",
            "substitution",
            "volumes",
            "fundamental_theorem_of_calculus",
            "work",
            "improper_integrals",
        ],
        "non_core": [
            "antiderivatives_and_riemann_sums",
            "area_between_curves",
            "integration_by_parts",
            "trigonometric_integrals",
            "trigonometric_substitution",
            "partial_fractions",
            "arc_length",
        ],
    },
    "126": {
        # Math 126: double_integrals, taylor_series, optimization (high frequency)
        "core": [
            "partial_derivatives",
            "tangent_planes_and_differentials",
            "multivariable_optimization",
            "double_integrals",
            "polar_coordinates",
            "applications_of_double_integrals",
            "taylor_polynomials_and_series",
        ],
        "non_core": [
            "vectors_and_geometry",
            "lines_and_planes",
            "quadric_surfaces",
            "vector_valued_functions",
            "motion_in_space",
            "multivariable_functions",
        ],
    },
}

# Legacy compatibility
CORE_TOPICS = COURSE_TOPICS["126"]["core"]
NON_CORE_TOPICS = COURSE_TOPICS["126"]["non_core"]

# Topic章节顺序（来自taxonomy/math126.py的SECTIONS week/order）
TOPIC_SECTION_ORDER = {
    "vectors_and_geometry": 11,      # week 1
    "lines_and_planes": 21,          # week 2
    "quadric_surfaces": 23,          # week 2
    "vector_valued_functions": 31,   # week 3
    "motion_in_space": 41,           # week 4
    "multivariable_functions": 51,   # week 5
    "partial_derivatives": 52,       # week 5
    "tangent_planes_and_differentials": 53,  # week 5
    "multivariable_optimization": 61,  # week 6
    "double_integrals": 62,          # week 6
    "polar_coordinates": 71,         # week 7
    "applications_of_double_integrals": 73,  # week 7
    "taylor_polynomials_and_series": 81,  # week 8-10
}


# =============================================================================
# Roadmap Item
# =============================================================================

@dataclass
class RoadmapItem:
    topic_key: str
    display_name: str
    selected_subtopics: list[str]
    priority: int  # 1 = highest
    depth: str
    reason_tags: list[str]
    estimated_time_minutes: int
    source: str = "taxonomy"

    def to_dict(self) -> dict:
        return {
            "topic_key": self.topic_key,
            "display_name": self.display_name,
            "selected_subtopics": self.selected_subtopics,
            "priority": self.priority,
            "depth": self.depth,
            "reason_tags": self.reason_tags,
            "estimated_time_minutes": self.estimated_time_minutes,
            "source": self.source,
        }


# =============================================================================
# Roadmap Generator
# =============================================================================

def generate_roadmap(
    days_until_exam: int,
    prep_level: str,
    diagnostic_result: dict,  # {topic_key: "weak"|"unstable"|"ok"|"unknown"}
    course: str = "126",
) -> dict:
    """
    生成个性化roadmap。

    Args:
        days_until_exam: 距离考试天数
        prep_level: 准备程度 (no_class_no_homework, etc.)
        diagnostic_result: 诊断结果 {topic: status}
        course: 课程代码

    Returns:
        {
            "roadmap_items": [...],
            "coverage_strategy": str,
            "debug_report": {...}
        }
    """
    # Dynamic taxonomy loading based on course
    if course == "124":
        from taxonomy.math124 import TOPIC_METADATA, SUBTOPICS
    elif course == "125":
        from taxonomy.math125 import TOPIC_METADATA, SUBTOPICS
    else:
        from taxonomy.math126 import TOPIC_METADATA, SUBTOPICS

    # Get course-specific topic lists
    course_config = COURSE_TOPICS.get(course, COURSE_TOPICS["126"])
    core_topics = course_config["core"]
    non_core_topics = course_config["non_core"]

    logger.info(f"[generate_roadmap] course={course}, core={len(core_topics)}, non_core={len(non_core_topics)}")

    # 第一层：确定coverage strategy
    strategy = get_coverage_strategy(days_until_exam)

    # Debug report
    debug = {
        "days_bucket": strategy.value,
        "days_until_exam": days_until_exam,
        "prep_level": prep_level,
        "course": course,
        "core_topics_included": [],
        "non_core_topics_included": [],
        "non_core_topics_skipped": [],
        "topic_decisions": [],
    }

    roadmap_items = []

    # 处理core topics
    for topic_key in core_topics:
        diag_status = diagnostic_result.get(topic_key, "unknown")
        meta = TOPIC_METADATA.get(topic_key, {})
        subtopics = SUBTOPICS.get(topic_key, [])

        # Core topic总是包含，只调整priority和depth
        item = _build_core_topic_item(
            topic_key=topic_key,
            meta=meta,
            subtopics=subtopics,
            diag_status=diag_status,
            prep_level=prep_level,
            strategy=strategy,
        )

        roadmap_items.append(item)
        debug["core_topics_included"].append(topic_key)
        debug["topic_decisions"].append({
            "topic": topic_key,
            "is_core": True,
            "diagnostic_status": diag_status,
            "decision": "include",
            "depth": item.depth,
            "reason_tags": item.reason_tags,
        })

    # 处理non-core topics
    for topic_key in non_core_topics:
        diag_status = diagnostic_result.get(topic_key, "unknown")
        meta = TOPIC_METADATA.get(topic_key, {})
        subtopics = SUBTOPICS.get(topic_key, [])

        include, item = _decide_non_core_topic(
            topic_key=topic_key,
            meta=meta,
            subtopics=subtopics,
            diag_status=diag_status,
            prep_level=prep_level,
            strategy=strategy,
        )

        if include:
            roadmap_items.append(item)
            debug["non_core_topics_included"].append(topic_key)
        else:
            debug["non_core_topics_skipped"].append(topic_key)

        debug["topic_decisions"].append({
            "topic": topic_key,
            "is_core": False,
            "diagnostic_status": diag_status,
            "decision": "include" if include else "skip",
            "depth": item.depth if include else "skip",
            "reason_tags": item.reason_tags if include else [],
        })

    # 按priority和章节顺序排序
    roadmap_items.sort(key=lambda x: (x.priority, TOPIC_SECTION_ORDER.get(x.topic_key, 99)))

    return {
        "roadmap_items": [item.to_dict() for item in roadmap_items],
        "coverage_strategy": strategy.value,
        "prep_level": prep_level,
        "debug_report": debug,
    }


def _build_core_topic_item(
    topic_key: str,
    meta: dict,
    subtopics: list,
    diag_status: str,
    prep_level: str,
    strategy: CoverageStrategy,
) -> RoadmapItem:
    """构建core topic的roadmap item"""

    reason_tags = ["core_topic"]

    # 根据diagnostic调整priority
    if diag_status == "weak":
        priority = 1
        reason_tags.append("diagnostic_weak")
    elif diag_status == "unstable":
        priority = 2
        reason_tags.append("diagnostic_unstable")
    elif diag_status == "ok":
        priority = 3
        reason_tags.append("diagnostic_ok")
    else:  # unknown
        priority = 2
        reason_tags.append("unknown_but_high_value")

    # 根据prep_level和diagnostic决定depth
    depth = get_base_depth(prep_level, diag_status)

    # CORE_CRAM时，ok的topic只做exam_drill
    if strategy == CoverageStrategy.CORE_CRAM:
        reason_tags.append("time_sensitive")
        if diag_status == "ok":
            depth = Depth.EXAM_DRILL
        elif diag_status == "unknown":
            depth = Depth.EXAM_DRILL  # unknown core topic: 少讲多做

    # 选择subtopics
    if diag_status == "weak":
        selected_subtopics = subtopics  # 全部
    elif diag_status == "unstable":
        selected_subtopics = subtopics[:len(subtopics)//2 + 2]  # 前半+2
    else:
        selected_subtopics = subtopics[:3]  # 只要关键的

    # 估算时间
    time_map = {
        Depth.FULL_REVIEW: 45,
        Depth.QUICK_REVIEW: 25,
        Depth.TARGETED_REVIEW: 30,
        Depth.EXAM_DRILL: 20,
        Depth.MOCK_EXAM: 15,
        Depth.COMPRESSED: 15,
    }
    estimated_time = time_map.get(depth, 20)

    return RoadmapItem(
        topic_key=topic_key,
        display_name=meta.get("display_name", topic_key.replace("_", " ").title()),
        selected_subtopics=selected_subtopics,
        priority=priority,
        depth=depth.value,
        reason_tags=reason_tags,
        estimated_time_minutes=estimated_time,
    )


def _decide_non_core_topic(
    topic_key: str,
    meta: dict,
    subtopics: list,
    diag_status: str,
    prep_level: str,
    strategy: CoverageStrategy,
) -> tuple[bool, Optional[RoadmapItem]]:
    """决定是否包含non-core topic"""

    reason_tags = []

    # CORE_CRAM: 只在weak/unstable或prerequisite时包含
    if strategy == CoverageStrategy.CORE_CRAM:
        if diag_status in ("weak", "unstable"):
            include = True
            reason_tags.append("diagnostic_weak" if diag_status == "weak" else "diagnostic_unstable")
        elif topic_key == "lines_and_planes":
            # lines_and_planes是prerequisite
            include = True
            reason_tags.append("prerequisite")
        else:
            include = False
            reason_tags.append("compressed_low_value")

    # CRASH_COURSE: weak/unstable包含，ok压缩
    elif strategy == CoverageStrategy.CRASH_COURSE:
        if diag_status in ("weak", "unstable"):
            include = True
            reason_tags.append("diagnostic_weak" if diag_status == "weak" else "diagnostic_unstable")
        elif topic_key in ("lines_and_planes", "vectors_and_geometry"):
            include = True
            reason_tags.append("prerequisite")
        else:
            include = False
            reason_tags.append("compressed_low_value")

    # COMPRESSED_FULL: 全部包含，调整depth
    elif strategy == CoverageStrategy.COMPRESSED_FULL:
        include = True
        if diag_status == "weak":
            reason_tags.append("diagnostic_weak")
        elif diag_status == "unstable":
            reason_tags.append("diagnostic_unstable")
        elif diag_status == "ok":
            reason_tags.append("diagnostic_ok")
        else:
            reason_tags.append("medium_frequency")

    # FULL_PERSONALIZED: 全部包含
    else:
        include = True
        if diag_status == "weak":
            reason_tags.append("diagnostic_weak")
        elif diag_status == "unstable":
            reason_tags.append("diagnostic_unstable")
        else:
            reason_tags.append("diagnostic_ok" if diag_status == "ok" else "medium_frequency")

    if not include:
        return False, None

    # 构建item
    depth = get_base_depth(prep_level, diag_status)

    # Non-core在CORE_CRAM时压缩
    if strategy == CoverageStrategy.CORE_CRAM:
        depth = Depth.COMPRESSED
        reason_tags.append("time_sensitive")

    # 选择subtopics
    if diag_status == "weak":
        selected_subtopics = subtopics[:len(subtopics)//2 + 1]
    else:
        selected_subtopics = subtopics[:2]

    # Priority: non-core比core低
    if diag_status == "weak":
        priority = 4
    elif diag_status == "unstable":
        priority = 5
    else:
        priority = 6

    # 估算时间
    time_map = {
        Depth.FULL_REVIEW: 35,
        Depth.QUICK_REVIEW: 20,
        Depth.TARGETED_REVIEW: 25,
        Depth.EXAM_DRILL: 15,
        Depth.COMPRESSED: 10,
    }
    estimated_time = time_map.get(depth, 15)

    item = RoadmapItem(
        topic_key=topic_key,
        display_name=meta.get("display_name", topic_key.replace("_", " ").title()),
        selected_subtopics=selected_subtopics,
        priority=priority,
        depth=depth.value,
        reason_tags=reason_tags,
        estimated_time_minutes=estimated_time,
    )

    return True, item


# =============================================================================
# High Value Sections (分数杠杆，不是学习顺序)
# =============================================================================

def generate_high_value_sections(
    days_until_exam: int,
    diagnostic_result: dict,
    course: str = "126",
    num_recent_exams: int = 5,
) -> list[dict]:
    """
    生成高价值topics列表，用于HighValueCard。

    算法：Expected Loss Model
    Step 1: 候选池 - topic级别 (count >= 3 OR count >= 2 AND avg_points >= 10)
    Step 2: 过滤 diagnostic "ok" (已掌握的不需要补)
    Step 3: expected_loss = (count / num_recent_exams) * avg_points
    Step 4: 映射到sections，取max不是sum
    Step 5: color_family多样性 (同family最多1个)
    Step 6: 数量由days_until_exam决定 (>7→3, 4-7→3, 2-3→2, ≤1→1)

    Returns:
        List of topic-level dicts with nested sections
    """
    from taxonomy.exam_blocks import analyze_exam_frequency
    from taxonomy.math126 import SECTIONS, SUBTOPICS, TOPIC_METADATA

    # 获取真题频率数据
    exam_stats = analyze_exam_frequency(course, num_recent_exams=num_recent_exams)

    # 固定返回3个高价值topic
    top_k = 3

    # 建立 concept -> section 映射
    concept_to_section = {}
    for section in SECTIONS:
        for concept in section.get('concepts', []):
            concept_to_section[concept] = section

    # 建立 topic -> sections 映射
    topic_to_sections = {}
    for topic, concepts in SUBTOPICS.items():
        for concept in concepts:
            if concept in concept_to_section:
                section = concept_to_section[concept]
                if topic not in topic_to_sections:
                    topic_to_sections[topic] = []
                if section not in topic_to_sections[topic]:
                    topic_to_sections[topic].append(section)

    # Step 1 + 2 + 3: 筛选候选 + 过滤ok + 计算expected_loss
    candidates = []
    debug_all_topics = []  # 用于调试输出

    for topic, stats in exam_stats.items():
        count = stats["count"]
        total_points = stats["points"]
        avg_points = total_points / count if count > 0 else 0
        diag_status = diagnostic_result.get(topic, "unknown")
        color_family = TOPIC_METADATA.get(topic, {}).get("color_family", "gray")

        # Step 1: 候选池条件
        in_candidate_pool = (count >= 3) or (count >= 2 and avg_points >= 10)

        # Step 2: 过滤掉已掌握的
        filtered_out_ok = (diag_status == "ok")

        # Step 3: 计算 expected_loss
        expected_loss = (count / num_recent_exams) * avg_points if num_recent_exams > 0 else 0

        # 记录调试信息
        topic_debug = {
            "topic": topic,
            "count": count,
            "total_points": total_points,
            "avg_points": round(avg_points, 2),
            "expected_loss": round(expected_loss, 2),
            "diagnostic": diag_status,
            "color_family": color_family,
            "in_pool": in_candidate_pool,
            "filtered_ok": filtered_out_ok,
            "reason": "",
        }

        if not in_candidate_pool:
            topic_debug["reason"] = f"count={count} < 3 AND (count < 2 OR avg_points={avg_points:.1f} < 10)"
        elif filtered_out_ok:
            topic_debug["reason"] = "diagnostic=ok (已掌握)"
        else:
            topic_debug["reason"] = "进入候选池"
            # 获取对应的sections
            sections = topic_to_sections.get(topic, [])
            candidates.append({
                "topic": topic,
                "count": count,
                "avg_points": avg_points,
                "expected_loss": expected_loss,
                "diagnostic": diag_status,
                "color_family": color_family,
                "sections": sections,
            })

        debug_all_topics.append(topic_debug)

    # Step 4: 按expected_loss排序 (映射到sections时取max，这里已经是topic级别)
    candidates.sort(key=lambda x: x["expected_loss"], reverse=True)

    # Step 5: color_family多样性去重
    selected = []
    used_color_families = set()

    for c in candidates:
        if len(selected) >= top_k:
            break
        if c["color_family"] in used_color_families:
            # 找到这个topic的debug记录，更新reason
            for d in debug_all_topics:
                if d["topic"] == c["topic"] and d["reason"] == "进入候选池":
                    d["reason"] = f"color_family={c['color_family']} 已有"
            continue
        selected.append(c)
        used_color_families.add(c["color_family"])
        # 更新debug记录
        for d in debug_all_topics:
            if d["topic"] == c["topic"]:
                d["reason"] = f"✓ 入选 (rank #{len(selected)})"

    # 构建返回结果 (topic级别，包含nested sections)
    result = []
    for item in selected:
        # Step 4: 对于sections，取max expected_loss (这里所有sections共享topic的loss)
        sections_data = []
        for section in item["sections"]:
            sections_data.append({
                "section_id": section["id"],
                "display_name": section["display_name"],
            })

        result.append({
            "topic": item["topic"],
            "display_name": TOPIC_METADATA.get(item["topic"], {}).get("display_name", item["topic"]),
            "expected_loss": round(item["expected_loss"], 2),
            "count": item["count"],
            "avg_points": round(item["avg_points"], 2),
            "diagnostic": item["diagnostic"],
            "color_family": item["color_family"],
            "sections": sections_data,
            "is_weak": item["diagnostic"] in ["weak", "unstable"],
        })

    # 附加调试报告
    debug_report = {
        "num_recent_exams": num_recent_exams,
        "days_until_exam": days_until_exam,
        "top_k": top_k,
        "all_topics": sorted(debug_all_topics, key=lambda x: x.get("expected_loss", 0), reverse=True),
    }

    return {
        "high_value_topics": result,
        "debug_report": debug_report,
    }


# =============================================================================
# Debug Helper
# =============================================================================

def print_roadmap(result: dict):
    """打印roadmap用于调试"""
    print("\n" + "=" * 60)
    print("ROADMAP DEBUG REPORT")
    print("=" * 60)

    debug = result.get("debug_report", {})
    print(f"\nDays bucket: {debug.get('days_bucket')}")
    print(f"Days until exam: {debug.get('days_until_exam')}")
    print(f"Prep level: {debug.get('prep_level')}")

    print(f"\nCore topics included: {debug.get('core_topics_included')}")
    print(f"Non-core included: {debug.get('non_core_topics_included')}")
    print(f"Non-core skipped: {debug.get('non_core_topics_skipped')}")

    print("\n" + "-" * 60)
    print("TOPIC DECISIONS:")
    print("-" * 60)
    for td in debug.get("topic_decisions", []):
        core_str = "CORE" if td["is_core"] else "non-core"
        print(f"  [{core_str}] {td['topic']}")
        print(f"      diagnostic: {td['diagnostic_status']}")
        print(f"      decision: {td['decision']}")
        print(f"      depth: {td['depth']}")
        print(f"      reasons: {td['reason_tags']}")

    print("\n" + "-" * 60)
    print("FINAL ROADMAP (sorted by priority):")
    print("-" * 60)
    for i, item in enumerate(result.get("roadmap_items", []), 1):
        print(f"  {i}. {item['display_name']} (priority {item['priority']})")
        print(f"     depth: {item['depth']}")
        print(f"     subtopics: {len(item['selected_subtopics'])}")
        print(f"     time: {item['estimated_time_minutes']}min")
        print(f"     reasons: {item['reason_tags']}")


if __name__ == "__main__":
    # 测试：3天后考试，完全没准备，diagnostic显示optimization weak
    result = generate_roadmap(
        days_until_exam=3,
        prep_level="no_class_no_homework",
        diagnostic_result={
            "multivariable_optimization": "weak",
            "taylor_polynomials_and_series": "unstable",
            "double_integrals": "ok",
        },
    )
    print_roadmap(result)
