# 错误类型驱动推荐系统

## 🎯 核心思想

**不同错误类型 = 不同紧迫程度**

```python
错误类型优先级:
concept  (概念错) → 30 分加成 (最高优先级)
logic    (逻辑错) → 25 分加成 (高优先级)
algebra  (代数错) → 10 分加成 (中优先级)
careless (粗心错) → 0 分加成  (低优先级)
```

**原理**：
- 概念错误 → 需要重新理解，最紧迫
- 逻辑错误 → 理解概念但推理有问题，次紧迫
- 代数错误 → 懂方法但计算有误，需要练习
- 粗心错误 → 已掌握，只需小心，不优先推荐

---

## 📊 数据结构升级

### SubtopicEstimate 新增字段

```python
@dataclass
class SubtopicEstimate:
    subtopic: str
    score: float = 0.5
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0

    # 新增 ⭐
    error_counts: Dict[str, int] = field(default_factory=lambda: {
        "concept": 0,
        "algebra": 0,
        "logic": 0,
        "careless": 0,
    })
    last_error_type: Optional[str] = None
```

### 新增方法

#### 1. `get_dominant_error_type()` - 获取主要错误类型

```python
def get_dominant_error_type(self) -> Optional[str]:
    """返回最常见的错误类型"""
    if not any(self.error_counts.values()):
        return None
    return max(self.error_counts.items(), key=lambda x: x[1])[0]
```

**示例**：
```python
# 学生在 integration_bounds_setup 上犯了 2 次概念错误，1 次代数错误
sub_est.error_counts = {"concept": 2, "algebra": 1, "logic": 0, "careless": 0}
sub_est.get_dominant_error_type()
# → 返回 "concept"
```

---

#### 2. `get_error_urgency_boost()` - 计算错误紧迫度加成 ⭐ 核心

```python
def get_error_urgency_boost(self) -> float:
    """
    根据错误类型模式返回推荐加成分数

    错误类型紧迫度:
    - concept: 30 分 (需要理解，高优先级)
    - logic: 25 分 (需要推理练习)
    - algebra: 10 分 (计算练习)
    - careless: 0 分 (已理解，只需小心)

    返回 0-30 分，基于主要错误类型和错误频率
    """
    dominant_error = self.get_dominant_error_type()
    if not dominant_error:
        return 0.0

    # 基础加成
    error_boosts = {
        "concept": 30,
        "logic": 25,
        "algebra": 10,
        "careless": 0,
    }

    base_boost = error_boosts.get(dominant_error, 0)

    # 根据错误频率调整（递减效应）
    error_count = self.error_counts[dominant_error]
    frequency_multiplier = min(1.0, error_count / 2)

    return base_boost * frequency_multiplier
```

**示例**：

| 错误类型 | 错误次数 | 基础加成 | 频率乘数 | 最终加成 |
|---------|---------|---------|---------|---------|
| concept | 1 | 30 | 0.5 | **15** |
| concept | 2 | 30 | 1.0 | **30** |
| concept | 3+ | 30 | 1.0 | **30** |
| logic | 2 | 25 | 1.0 | **25** |
| algebra | 2 | 10 | 1.0 | **10** |
| careless | 2 | 0 | 1.0 | **0** |

---

## 🎯 推荐算法集成

### recommender_v2.py 新增优先级层

```python
# 原有优先级:
# Priority 1: 子话题匹配 (0-120分)
# Priority 2: 话题优先级 (0-100分)
# Priority 3: 基础话题 (0-30分)
# ...

# 新增 ⭐
# Priority 1.5: 错误类型紧迫度加成 (0-30分)
error_urgency_boost = 0
if topic in profile.topic_estimates and problem_subtopics:
    topic_est = profile.topic_estimates[topic]
    for prob_subtopic in problem_subtopics:
        if prob_subtopic in topic_est.subtopics:
            sub_est = topic_est.subtopics[prob_subtopic]
            error_urgency_boost += sub_est.get_error_urgency_boost()

score += error_urgency_boost
```

---

## 📈 实际推荐示例

### 场景：学生犯不同类型错误

**学生做题记录**：
```python
# 做题 1: integration_bounds_setup - 概念错误
profile.record_attempt("double_integrals", "integration_bounds_setup", False, "concept")
profile.record_attempt("double_integrals", "integration_bounds_setup", False, "concept")
# → 错误加成: +30 分

# 做题 2: iterated_integrals - 粗心错误
profile.record_attempt("double_integrals", "iterated_integrals", False, "careless")
# → 错误加成: +0 分

# 做题 3: lagrange_multipliers - 逻辑错误
profile.record_attempt("multivariable_optimization", "lagrange_multipliers", False, "logic")
# → 错误加成: +12.5 分 (1次错误)

# 做题 4: mixed_partials - 代数错误
profile.record_attempt("partial_derivatives", "mixed_partials", False, "algebra")
# → 错误加成: +5 分 (1次错误)
```

---

### 推荐打分对比

**可选题目**：
| 题目 | 子话题 | 子话题匹配 | 错误加成 | 话题优先级 | 总分 | 排名 |
|------|--------|-----------|---------|-----------|------|------|
| P1 | integration_bounds_setup | 48 | **+30** | 50 | **128** | 🏆 1st |
| P3 | lagrange_multipliers | 56 | **+12.5** | 50 | 118.5 | 2nd |
| P2 | iterated_integrals | 60 | **+0** | 50 | 110 | 3rd |
| P4 | mixed_partials | 52 | **+5** | 50 | 107 | 4th |

**结果**：
- ✅ **P1 获胜**：虽然子话题匹配分不是最高，但因为有**概念错误**，获得 +30 加成，总分最高
- ❌ P2 被降级：虽然子话题匹配最高 (60分)，但只是粗心错误 (+0 加成)，理解已足够

---

## 💡 关键优势

### 对比：有无错误类型加成

**场景**：学生在两个子话题上都犯错

| 子话题 | 分数 | 优先级 | 错误类型 | 错误加成 |
|--------|------|--------|---------|---------|
| integration_bounds | 0.30 | 0.58 | **concept** | **+30** |
| polar_setup | 0.20 | 0.64 | **careless** | **+0** |

**没有错误加成**：
```
polar_setup 获胜 (优先级 0.64 > 0.58)
→ 但学生只是粗心，已经理解概念！
→ 过度练习没必要
```

**有错误加成**：
```
integration_bounds 获胜 (+30 加成)
→ 学生有概念错误，需要先理解！
→ 优先解决概念缺陷
```

---

## 🔄 错误类型演化追踪

### 学习进度典型路径

```
阶段 1: 概念学习
❌❌ 概念错误 (score=0.3, boost=+30)
→ 系统高优先级推荐相关题目
→ 需要概念性教学

阶段 2: 理解提升
❌✅ 逻辑错误 (score=0.4, boost=+25)
→ 理解概念，但推理有问题
→ 需要逻辑练习

阶段 3: 熟练度提升
✅❌ 代数错误 (score=0.5, boost=+10)
→ 懂方法，但计算有误
→ 需要计算练习

阶段 4: 精细化
✅✅ 偶尔粗心 (score=0.7, boost=+0)
→ 已掌握，无需优先推荐
→ 可以转向新话题
```

---

## 📝 使用方法

### 1. 记录做题时指定错误类型

```python
from student_profile_v2 import StudentProfileV2

profile = StudentProfileV2(course="126")

# 记录尝试时指定 error_type
profile.record_attempt(
    topic="double_integrals",
    subtopic="integration_bounds_setup",
    correct=False,
    error_type="concept"  # ⭐ 指定错误类型
)
```

---

### 2. 查看子话题错误分析

```python
topic_est = profile.topic_estimates["double_integrals"]
sub_est = topic_est.subtopics["integration_bounds_setup"]

# 查看主要错误类型
dominant_error = sub_est.get_dominant_error_type()
print(f"主要错误: {dominant_error}")  # → "concept"

# 查看错误加成
boost = sub_est.get_error_urgency_boost()
print(f"推荐加成: {boost} 分")  # → 30.0

# 查看详细错误统计
print(sub_est.error_counts)
# → {"concept": 2, "algebra": 0, "logic": 0, "careless": 0}
```

---

### 3. 推荐系统自动使用

```python
from recommender_v2 import recommend_next_problem_v2

# 推荐算法会自动考虑错误类型
next_idx = recommend_next_problem_v2(
    parts_list=problems,
    current_idx=0,
    profile=profile
)
# → 返回带有概念错误子话题的题目（优先级最高）
```

---

## 🎯 错误类型检测（可选实现）

### 自动检测错误类型

可以根据学生的错误模式自动推断错误类型：

```python
def detect_error_type(problem, student_answer, correct_answer, verifier_result):
    """自动检测错误类型（建议实现）"""

    # 1. 如果 verifier 说最终答案完全错误 + 关键步骤缺失 → concept
    if verifier_result.get("missing_key_steps"):
        return "concept"

    # 2. 如果设置正确但执行错误 → logic
    if verifier_result.get("setup_correct") and not verifier_result.get("execution_correct"):
        return "logic"

    # 3. 如果方法正确但计算错误 → algebra
    if verifier_result.get("method_correct") and verifier_result.get("computational_error"):
        return "algebra"

    # 4. 如果非常接近正确答案（符号错误、小数点等）→ careless
    if verifier_result.get("near_miss"):
        return "careless"

    return "concept"  # 默认
```

---

## 🧪 运行示例

```bash
python3 example_error_type_recommendations.py
```

**输出展示**：
- ✅ 错误紧迫度计算
- ✅ 推荐打分对比（有/无错误加成）
- ✅ 错误类型演化追踪
- ✅ 实际推荐决策

---

## 📊 总结

| 改进点 | 效果 |
|--------|------|
| **优先级智能化** | 概念错优先于粗心错 |
| **学习路径优化** | 先补概念缺陷，再练计算 |
| **避免过度练习** | 粗心错不反复推荐 |
| **细粒度诊断** | 子话题 + 错误类型 = 精准定位 |
| **自动调整** | 错误类型变化 → 推荐自动调整 |

---

## 🔗 相关文件

| 文件 | 改动 |
|------|------|
| `student_profile_v2.py` | ✅ 添加 error_counts, get_error_urgency_boost() |
| `recommender_v2.py` | ✅ 添加 Priority 1.5: 错误类型加成 |
| `example_error_type_recommendations.py` | ✅ 4个完整示例 |
| `ERROR_TYPE_RECOMMENDATIONS.md` | ✅ 本文档 |

---

## 🚀 下一步

1. **集成到 app.py**：
   - 在 grading 结果中自动检测错误类型
   - 调用 `profile.record_attempt(..., error_type=detected_type)`

2. **UI 显示**：
   - 显示每个子话题的主要错误类型
   - "You have concept errors in integration_bounds_setup"

3. **Verifier 增强**：
   - 让 `verifier.py` 返回错误分类
   - 基于学生答案和正确答案的差异自动判断

4. **反馈优化**：
   - 概念错误 → 提供概念解释
   - 代数错误 → 提供计算步骤
   - 粗心错误 → 提醒检查
