# 分层用户画像设计 (V2)

## 🎯 核心改进

从扁平的 topic tracking 升级到**层级化的 topic → subtopic tracking**：

```python
# V1 (旧版): 扁平结构
topic_estimates = {
  "Double Integrals": TopicEstimate(score=0.45, attempts=5),
  "Polar Coordinates": TopicEstimate(score=0.6, attempts=3),
}

# V2 (新版): 层级结构
topic_estimates = {
  "double_integrals": TopicEstimateV2(
    topic="double_integrals",
    score=0.47,  # 自动聚合自 subtopics
    subtopics={
      "integration_bounds_setup": SubtopicEstimate(score=0.3, priority=0.58),
      "iterated_integrals": SubtopicEstimate(score=0.5, priority=0.42),
      "changing_order_of_integration": SubtopicEstimate(score=0.4, priority=0.50),
    }
  )
}
```

---

## 📊 数据结构

### 1. SubtopicEstimate（子话题评估）

```python
@dataclass
class SubtopicEstimate:
    subtopic: str           # 如 "integration_bounds_setup"
    score: float = 0.5      # 掌握度 (0-1)
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0

    @property
    def confidence(self) -> float:
        return min(1.0, self.attempts / 3)  # ~3次尝试达到高置信

    @property
    def priority_score(self) -> float:
        # 优先级公式：薄弱 + 不确定 = 高优先级
        return (1 - self.score) * (1 - self.confidence * 0.5)
```

**示例**：
| Subtopic | Score | Attempts | Confidence | Priority | 解释 |
|----------|-------|----------|------------|----------|------|
| `integration_bounds_setup` | 0.3 | 1 | 0.33 | **0.58** | 低分+低信心 = 最高优先级 |
| `iterated_integrals` | 0.5 | 1 | 0.33 | **0.42** | 中等分数 = 中优先级 |
| `changing_order` | 0.8 | 4 | 1.0 | **0.10** | 高分+高信心 = 低优先级 |

---

### 2. TopicEstimateV2（话题评估 - 层级化）

```python
@dataclass
class TopicEstimateV2:
    topic: str
    subtopics: Dict[str, SubtopicEstimate]  # 子话题字典
    total_attempts: int = 0                  # 总尝试次数

    @property
    def score(self) -> float:
        # 话题分数 = 子话题分数的加权平均
        # 权重 = 尝试次数（更多尝试 = 更高权重）
        total_weighted = sum(sub.score * sub.attempts
                             for sub in self.subtopics.values())
        total_weight = sum(sub.attempts for sub in self.subtopics.values())
        return total_weighted / total_weight if total_weight > 0 else 0.5

    @property
    def priority_score(self) -> float:
        # 话题优先级 = 最薄弱子话题的优先级
        return max(sub.priority_score for sub in self.subtopics.values())
```

**关键特性**：
- ✅ **自动聚合**：话题分数自动从子话题计算
- ✅ **优先级传递**：话题优先级 = 最弱子话题的优先级
- ✅ **细粒度追踪**：每个子话题独立追踪

---

### 3. StudentProfileV2（学生画像）

```python
@dataclass
class StudentProfileV2:
    course: str  # "124", "125", "126"
    topic_estimates: Dict[str, TopicEstimateV2]  # 话题字典

    # 方法
    def record_attempt(topic, subtopic, correct, error_type):
        """记录学生在特定子话题的尝试"""

    def get_priority_topics() -> list[str]:
        """获取优先话题（按优先级排序）"""

    def get_priority_subtopics(topic) -> list[str]:
        """获取某话题内的优先子话题"""

    def get_all_priority_subtopics() -> list[(topic, subtopic)]:
        """获取跨话题的优先子话题（全局最优先）"""
```

---

## 🎯 推荐算法升级

### V1 推荐（仅基于话题）

```python
# 只能推荐 "练习 Double Integrals"，无法细化到具体子话题
recommend("double_integrals") → 返回任意 double integral 题目
```

### V2 推荐（基于子话题）

```python
# 可以精确推荐 "练习 integration_bounds_setup"
recommend_next_problem_v2() → 匹配题目的 subtopics 字段

# 打分逻辑
for problem in problems:
    score = 0

    # Priority 1: 子话题匹配 (0-120分) ⭐ 新增！
    if problem.subtopics ∈ student_weak_subtopics:
        score += 60  # 精确匹配薄弱子话题

    # Priority 2: 话题优先级 (0-100分)
    score += topic.priority_score * 100

    # Priority 3: 基础话题 (0-30分)
    # Priority 4: 诊断关注 (0-20分)
    # Priority 5: 难度递进 (0-15分)

    return highest_scored_problem
```

---

## 🔄 实际使用流程

### 场景：学生做诊断测试

**Step 1: 诊断初始化**

```python
profile = StudentProfileV2(course="126")
profile.record_diagnostic(
    score=0.45,
    focus_topics=["double_integrals", "multivariable_optimization"]
)

# 自动初始化子话题（从 taxonomy）
# double_integrals:
#   - integration_bounds_setup: score=0.4
#   - iterated_integrals: score=0.4
#   - changing_order_of_integration: score=0.4
#   - ...
```

---

**Step 2: 学生练习**

```python
# 练习 1: 设置积分边界 - 错误
profile.record_attempt(
    topic="double_integrals",
    subtopic="integration_bounds_setup",
    correct=False,
    error_type="concept"
)
# → integration_bounds_setup: score=0.3, priority=0.58 ⬆️

# 练习 2: 迭代积分 - 正确
profile.record_attempt(
    topic="double_integrals",
    subtopic="iterated_integrals",
    correct=True
)
# → iterated_integrals: score=0.5, priority=0.42 ⬇️
```

---

**Step 3: 获取推荐**

```python
# 方法 1: 获取最弱子话题（全局）
weak_subs = profile.get_all_priority_subtopics(limit=5)
# 结果:
# [
#   ("double_integrals", "integration_bounds_setup", priority=0.58),
#   ("double_integrals", "changing_order_of_integration", priority=0.50),
#   ("multivariable_optimization", "lagrange_multipliers", priority=0.50),
#   ...
# ]

# 方法 2: 获取某话题内的弱子话题
weak_in_topic = profile.get_priority_subtopics("double_integrals", limit=3)
# 结果:
# ["integration_bounds_setup", "changing_order_of_integration", ...]

# 方法 3: 话题细分报告
breakdown = get_topic_breakdown(profile, "double_integrals")
# 结果:
# {
#   "topic": "double_integrals",
#   "score": 0.40,
#   "status": "mixed results",
#   "subtopics": [
#     {"name": "integration_bounds_setup", "score": 0.3, "priority": 0.58},
#     {"name": "iterated_integrals", "score": 0.5, "priority": 0.42},
#     ...
#   ]
# }
```

---

**Step 4: 智能推荐题目**

```python
# 假设题库有这些题目
problems = [
    Problem(topic="double_integrals", subtopics=["integration_bounds_setup"]),  # A
    Problem(topic="double_integrals", subtopics=["iterated_integrals"]),        # B
    Problem(topic="polar_coordinates", subtopics=["polar_integral_setup"]),     # C
]

# V2 推荐算法打分
# A: subtopic_match(60) + topic_priority(40) = 100 ⭐ 推荐！
# B: subtopic_match(42) + topic_priority(40) = 82
# C: subtopic_match(0)  + topic_priority(20) = 20

recommended = recommend_next_problem_v2(problems, profile)
# → 返回 A (integration_bounds_setup)，精准针对薄弱子话题！
```

---

## 📈 优势对比

| 特性 | V1 (Flat) | V2 (Hierarchical) |
|------|-----------|-------------------|
| **追踪粒度** | 话题级别 | 子话题级别 |
| **推荐精度** | "练习 Double Integrals" | "练习 integration_bounds_setup" |
| **问题诊断** | "Double Integrals 薄弱" | "边界设置薄弱，但迭代积分还行" |
| **数据结构** | 扁平字典 | 树状层级 |
| **taxonomy 利用** | ❌ 未使用 | ✅ 完全集成 |
| **迁移路径** | N/A | ✅ 提供 `migrate_from_v1()` |

---

## 🔧 实现文件

| 文件 | 作用 |
|------|------|
| `student_profile_v2.py` | V2 数据结构、序列化、迁移 |
| `recommender_v2.py` | 基于子话题的推荐算法 |
| `example_hierarchical_profile.py` | 使用示例和演示 |
| `taxonomy/__init__.py` | 话题和子话题定义（已存在） |
| `taxonomy/math126.py` | Math 126 的 SUBTOPICS 定义 |

---

## 🚀 集成到现有系统

### 选项 1: 渐进式迁移（推荐）

```python
# app.py
from student_profile import get_profile as get_profile_v1
from student_profile_v2 import get_profile_v2, migrate_from_v1

def get_current_profile():
    # 优先使用 V2
    v2 = get_profile_v2()
    if v2:
        return v2

    # 如果没有 V2，尝试迁移 V1
    v1 = get_profile_v1()
    if v1:
        v2 = migrate_from_v1(v1)
        save_profile_v2(v2)
        return v2

    # 否则创建新 V2
    return create_profile_v2(course="126")
```

### 选项 2: 并行运行（测试）

```python
# 同时维护 V1 和 V2，对比效果
v1_profile = get_profile_v1()
v2_profile = get_profile_v2()

v1_recommendation = recommend_next_problem(problems, v1_profile)
v2_recommendation = recommend_next_problem_v2(problems, v2_profile)

# 记录对比数据，A/B测试
```

---

## 📝 待办事项

### 必须做的
- [ ] 在 `Problem` 数据类中添加 `subtopics: list[str]` 字段
- [ ] 更新 `question_bank.py` 的题目提取逻辑，识别子话题
- [ ] 集成 V2 到 `app.py` 的 teaching session
- [ ] 更新 Supabase schema 支持层级结构存储

### 可选优化
- [ ] UI 显示子话题细分进度条
- [ ] 子话题推荐理由显示："建议练习 integration_bounds_setup"
- [ ] 自动检测题目子话题（基于 heuristics 内容匹配）
- [ ] 子话题掌握度热力图可视化

---

## 🎓 关键设计原则

1. **层级聚合**：话题分数自动从子话题计算，无需手动维护
2. **优先级传递**：最弱子话题决定话题优先级
3. **taxonomy 驱动**：子话题定义来自 `taxonomy/math*.py`，保持一致性
4. **向后兼容**：提供 V1 → V2 迁移路径
5. **精准推荐**：推荐算法优先匹配薄弱子话题

---

## ✅ 运行示例查看效果

```bash
python3 example_hierarchical_profile.py
```

示例输出展示：
- ✅ 诊断初始化子话题
- ✅ 记录子话题尝试
- ✅ 实时更新优先级
- ✅ 跨话题子话题排序
- ✅ 话题细分报告
- ✅ V1 → V2 迁移演示
