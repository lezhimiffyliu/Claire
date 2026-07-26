"""
Exam Block Definitions - 基于真题数据动态计算高频topics

核心逻辑：
1. 从最新N套真题中统计topic频率（次数+分值）
2. 找出高频top K topics
3. 按SECTIONS章节顺序排列（不是按频率）
4. CRAM模式只显示这些高频topics，按章节顺序

不hardcode优先级，而是从真题数据中计算。
"""

import json
import os
from collections import defaultdict
from typing import Optional
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def analyze_exam_frequency(course: str = "126", num_recent_exams: int = 3) -> dict:
    """
    分析最新N套真题的topic频率。

    Returns:
        Dict mapping topic -> {"count": int, "points": int}
    """
    problems_dir = PROJECT_ROOT / "problems"

    # 找到该课程的所有真题文件，按名称排序（最新的在前）
    exam_files = sorted(
        [f for f in problems_dir.glob(f"math{course}_*.json")],
        key=lambda x: x.name,
        reverse=True
    )[:num_recent_exams]

    topic_stats = defaultdict(lambda: {"count": 0, "points": 0})

    for exam_file in exam_files:
        try:
            with open(exam_file) as f:
                data = json.load(f)
                problems = data if isinstance(data, list) else data.get("problems", [])

                for p in problems:
                    topic = p.get("topic", "unknown")
                    if topic == "unknown":
                        continue
                    topic_stats[topic]["count"] += 1
                    topic_stats[topic]["points"] += p.get("points", 0)
        except Exception:
            continue

    return dict(topic_stats)


def get_high_frequency_topics(course: str = "126", top_k: int = 5) -> list[str]:
    """
    获取高频topics（按出现次数+分值排序）。

    Returns:
        List of topic names, sorted by frequency (highest first)
    """
    stats = analyze_exam_frequency(course)

    # 按 count * 10 + points 综合排序
    sorted_topics = sorted(
        stats.items(),
        key=lambda x: x[1]["count"] * 10 + x[1]["points"],
        reverse=True
    )

    return [t[0] for t in sorted_topics[:top_k]]


def get_section_order(course: str = "126") -> dict[str, int]:
    """
    获取topic的章节顺序（基于SECTIONS的week/order）。

    Returns:
        Dict mapping topic -> order_index (smaller = earlier in syllabus)
    """
    if course == "126":
        from taxonomy.math126 import SECTIONS, SUBTOPICS

        # 建立 concept -> topic 的反向映射
        concept_to_topic = {}
        for topic, concepts in SUBTOPICS.items():
            for concept in concepts:
                concept_to_topic[concept] = topic

        # 计算每个topic最早出现的章节顺序
        topic_order = {}
        for idx, section in enumerate(SECTIONS):
            week = section.get("week", 99)
            order = section.get("order", 99)
            section_order = week * 10 + order

            for concept in section.get("concepts", []):
                topic = concept_to_topic.get(concept)
                if topic and topic not in topic_order:
                    topic_order[topic] = section_order

        return topic_order

    return {}


def get_cram_blocks(course: str = "126", top_k: int = 5) -> list[dict]:
    """
    获取CRAM模式的blocks：高频topics按章节顺序排列。

    Returns:
        List of block dicts with title, topics, reason
    """
    # 1. 获取高频topics
    high_freq_topics = get_high_frequency_topics(course, top_k)

    # 2. 获取章节顺序
    section_order = get_section_order(course)

    # 3. 按章节顺序排列高频topics
    sorted_topics = sorted(
        high_freq_topics,
        key=lambda t: section_order.get(t, 999)
    )

    # 4. 获取topic metadata
    if course == "126":
        from taxonomy.math126 import TOPIC_METADATA, SUBTOPICS

        blocks = []
        for topic in sorted_topics:
            meta = TOPIC_METADATA.get(topic, {})
            blocks.append({
                "block_id": topic,
                "title": meta.get("display_name", topic.replace("_", " ").title()),
                "topics": [topic],
                "concepts": SUBTOPICS.get(topic, []),
                "reason": "matches high-priority exam block",
                "section_order": section_order.get(topic, 999),
            })

        return blocks

    return []


def get_blocks_for_course(course: str) -> dict:
    """
    获取课程的所有exam blocks（兼容旧接口）。
    """
    blocks = get_cram_blocks(course)
    return {b["block_id"]: b for b in blocks}


def get_cram_order(course: str) -> list[str]:
    """
    获取CRAM模式的block顺序（按章节顺序）。
    """
    blocks = get_cram_blocks(course)
    return [b["block_id"] for b in blocks]


# 便捷函数：打印分析结果
def print_analysis(course: str = "126"):
    """打印真题分析结果，用于调试。"""
    print(f"\n{'='*50}")
    print(f"Math {course} 真题频率分析")
    print(f"{'='*50}\n")

    stats = analyze_exam_frequency(course)
    print("Topic频率（按出现次数排序）:")
    for topic, s in sorted(stats.items(), key=lambda x: -x[1]["count"]):
        print(f"  {topic}: {s['count']}题, {s['points']}分")

    print(f"\n高频Top 5:")
    for t in get_high_frequency_topics(course, 5):
        print(f"  - {t}")

    print(f"\nCRAM模式blocks（按章节顺序）:")
    for b in get_cram_blocks(course):
        print(f"  {b['section_order']}: {b['title']}")


if __name__ == "__main__":
    print_analysis("126")
