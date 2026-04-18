# 🎉 Welcome Back 个性化欢迎功能

## 功能概述

为returning users（已有学习进度的学生）提供个性化的欢迎页面，总结之前的表现，并根据用户画像智能推荐下一步该练什么。

## 触发条件

Welcome Back页面在以下情况显示：

1. ✅ 用户已登录（Google OAuth）
2. ✅ WorkspaceContext加载成功（有保存的学习数据）
3. ✅ 用户有学习进度：
   - 做过至少1道题（`total_correct + total_incorrect > 0`），**或**
   - 完成过diagnostic test（`diagnostic_completed = True`）

## 页面内容

### 1️⃣ 个性化问候

随机选择以下问候语之一：
- 👋 Welcome back!
- 🎉 Hey there!
- ✨ What's up!
- 💪 Ready to practice?
- 🚀 Let's do this!

显示用户邮箱：`Signed in as user@example.com`

### 2️⃣ 进度总结

**三个核心指标**：

| 指标 | 说明 |
|-----|------|
| **Problems Solved** | 总共做过的题目数 |
| **Accuracy** | 整体正确率（百分比） |
| **Topics Practiced** | 练过的不同topic数量 |

### 3️⃣ 智能状态评估

根据准确率显示不同的鼓励信息：

| 准确率 | 消息 |
|--------|------|
| ≥ 80% | 🔥 You're crushing it! Keep the momentum going. |
| 60-79% | 📈 Making solid progress. Let's tackle some more problems. |
| < 5题 | 🌱 Just getting started. Let's build some practice data. |
| 其他 | 💡 Some tricky spots showing up. Let's work through them together. |

### 4️⃣ 个性化推荐

基于 `StudentProfile.get_priority_topics()` 推荐top 3需要练习的topics。

**推荐逻辑**：
- `priority_score = (1 - score) * (1 - confidence * 0.5)`
- 优先推荐：可能薄弱 + 数据不足的topics

**推荐消息根据情况调整**：

```python
if total_attempts < 3:
    "Since you're just getting started, I recommend focusing on {topics}."

elif accuracy >= 80:
    "You're doing great! Next up: {topics} — let's keep this streak going."

else:
    "Based on your recent work, let's focus on {topics}. These need a bit more practice."
```

### 5️⃣ Topic详细展开

点击 "📋 Topic Breakdown" 查看每个推荐topic的：
- 正确/尝试次数
- 准确率
- 状态标签（`status_label`）：
  - "not yet tested"
  - "needs more signal"
  - "likely needs review"
  - "mixed results"
  - "showing progress"
  - "looking solid"

### 6️⃣ 错误模式洞察

如果某种错误类型出现≥3次，显示提示：

```
💬 Pattern noticed: Most errors are {error_type}.
   Claire will help you work through these!
```

错误类型：
- conceptual misunderstandings（概念误解）
- algebraic mistakes（代数错误）
- logic errors（逻辑错误）
- careless slips（粗心）

### 7️⃣ 行动按钮

两个选项：

| 按钮 | 行为 |
|-----|------|
| 🎯 **Continue Practicing** | 使用smart recommender选择下一题（基于priority topics） |
| 📚 **Browse All Problems** | 从头开始浏览问题列表 |

点击后：
- 设置 `st.session_state.welcome_back_shown = True`（防止重复显示）
- 调用 `start_practice(recommended=True/False)`
- 进入练习模式

---

## 实现细节

### 代码位置

**app.py**

1. **Session初始化逻辑**（约第100-140行）
   ```python
   if ctx:
       # Load profile
       profile = load_from_supabase(workspace_id)

       # Check if returning user
       has_progress = (profile.total_correct + profile.total_incorrect > 0)
                      or ctx.diagnostic_completed

       if has_progress and "welcome_back_shown" not in st.session_state:
           st.session_state.mode = "welcome_back"
   ```

2. **render_welcome_back()函数**（约第930-1060行）
   - 个性化问候
   - 进度统计
   - 智能推荐
   - 行动按钮

3. **Main routing**（约第1510行）
   ```python
   if st.session_state.mode == "welcome_back":
       render_welcome_back()
   ```

### 依赖的模块

- `student_profile.py` - 获取profile数据和优先级topics
- `auth.py` - 获取登录用户信息
- `learning_context.py` - 加载WorkspaceContext
- `recommender.py` - Smart problem recommendation（`start_practice(recommended=True)`调用）

---

## 用户体验流程

### 新用户第一次使用

```
1. 访问app → 课程选择页
2. 选择Math 124 → Diagnostic test
3. 完成diagnostic → Diagnostic result页
4. 开始练习 → Problem page
5. 关闭浏览器
```

### 新用户第二次访问

```
1. 打开app（自动登录）→ Welcome Back页 ✨
   - "Welcome back!"
   - "Problems Solved: 0" (只做了diagnostic)
   - "Continue Practicing" → 直接进入推荐题目
```

### 练过题的用户

```
1. 打开app → Welcome Back页 ✨
   - "What's up!"
   - "Problems Solved: 15"
   - "Accuracy: 73%"
   - "Topics Practiced: 5"
   - 推荐: "Focus on Double Integrals, Lagrange Multipliers"
   - 错误模式: "Most errors are algebraic mistakes"
   - "Continue Practicing" → 推荐Double Integrals的题目
```

### 高分用户

```
1. 打开app → Welcome Back页
   - "🔥 You're crushing it!"
   - "Accuracy: 87%"
   - "You're doing great! Next up: Partial Derivatives"
   - "Continue Practicing" → 继续挑战
```

---

## 测试步骤

### 测试1: 新用户（无progress）

1. 清除所有session
2. 访问app → 应显示**课程选择页**（不显示Welcome Back）

### 测试2: 完成diagnostic但未练题

```bash
streamlit run app.py
```

1. 登录Google
2. 选择Math 124
3. 完成diagnostic
4. 刷新页面 → 应显示**Welcome Back页**
   - Problems Solved: 0
   - Accuracy: 0%
   - 推荐diagnostic识别的weak topics

### 测试3: 练过题的用户

1. 登录并练习几道题（正确/错误都可以）
2. 刷新页面 → 应显示**Welcome Back页**
   - Problems Solved: > 0
   - Accuracy: 显示实际准确率
   - 推荐基于profile的priority topics
   - 如果某种错误≥3次，显示错误模式提示

### 测试4: 高分用户

1. 做10道题，正确率>80%
2. 刷新页面 → 应显示
   - "🔥 You're crushing it!"
   - "You're doing great! Next up: ..."

### 测试5: 点击按钮后不重复显示

1. 在Welcome Back页点击"Continue Practicing"
2. 进入Problem page
3. 刷新页面 → 应**直接进入Problem page**（不再显示Welcome Back）
   - 因为 `welcome_back_shown = True`

### 测试6: 登出后重新登录

1. 在Welcome Back页登出
2. 重新登录 → 应**再次显示Welcome Back**
   - 因为登出清除了session_state（包括`welcome_back_shown`）

---

## 个性化示例

### Example 1: 刚开始的用户

```
👋 Welcome back!
Signed in as student@uw.edu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Your Math 124 Progress

Problems Solved    Accuracy    Topics Practiced
       2              50%             2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 What's Next?

🌱 Just getting started. Let's build some practice data.

Since you're just getting started, I recommend focusing on
**Derivatives**, **Related Rates**.

📋 Topic Breakdown
  ▸ Derivatives: 1/2 correct (50%) — needs more signal
  ▸ Related Rates: 0/0 correct (0%) — not yet tested

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Continue Practicing    📚 Browse All Problems
```

### Example 2: 表现优秀的用户

```
🚀 Let's do this!
Signed in as alice@uw.edu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Your Math 126 Progress

Problems Solved    Accuracy    Topics Practiced
       18             83%             6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 What's Next?

🔥 You're crushing it! Keep the momentum going.

You're doing great! Next up: **Double Integrals**,
**Polar Coordinates** — let's keep this streak going.

📋 Topic Breakdown
  ▸ Double Integrals: 4/6 correct (67%) — showing progress
  ▸ Polar Coordinates: 3/4 correct (75%) — showing progress
  ▸ Lagrange Multipliers: 2/3 correct (67%) — mixed results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Continue Practicing    📚 Browse All Problems
```

### Example 3: 需要帮助的用户

```
✨ What's up!
Signed in as bob@uw.edu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Your Math 125 Progress

Problems Solved    Accuracy    Topics Practiced
       12             58%             4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 What's Next?

💡 Some tricky spots showing up. Let's work through them together.

Based on your recent work, let's focus on **Integration**,
**U Substitution**. These need a bit more practice.

📋 Topic Breakdown
  ▸ Integration: 3/7 correct (43%) — likely needs review
  ▸ U Substitution: 2/5 correct (40%) — likely needs review
  ▸ Trig Substitution: 2/3 correct (67%) — needs more signal

💬 Pattern noticed: Most errors are algebraic mistakes.
   Claire will help you work through these!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Continue Practicing    📚 Browse All Problems
```

---

## 设计原则

1. **非评判性语言**
   - ❌ "You're weak at..."
   - ✅ "Let's focus on..."
   - ❌ "You failed..."
   - ✅ "Some tricky spots showing up..."

2. **积极鼓励**
   - 高分用户 → 庆祝成就
   - 中等分数 → 强调进步
   - 低分用户 → 提供支持，不打击信心

3. **数据驱动推荐**
   - 基于 `priority_score`（不确定性 + 可能薄弱）
   - 不只看错误率，也考虑尝试次数

4. **行动导向**
   - 明确的下一步
   - 一键继续练习

5. **透明度**
   - 可展开查看详细的topic breakdown
   - 解释为什么推荐这些topics

---

## 未来增强（可选）

1. **连续登录天数**
   - "🔥 5-day streak!"
   - 追踪每日练习

2. **成就徽章**
   - "🏆 10题连对"
   - "📚 完成所有topics"

3. **每周总结**
   - "本周练了15道题，比上周多50%"

4. **同侪对比**（可选）
   - "你的进度超过60%的同学"（需谨慎，避免竞争压力）

5. **个性化学习路径**
   - "建议先巩固基础，再挑战难题"
   - 基于foundation review flag

---

## 总结

Welcome Back功能通过：
- ✅ 个性化问候让用户感到被关注
- ✅ 进度统计提供成就感
- ✅ 智能推荐减少选择困难
- ✅ 鼓励性语言提升学习动力

**最终效果**：用户刷新页面后，不再是冷冰冰的课程列表，而是一个懂他们学习情况、知道下一步该做什么的智能导师！🎯
