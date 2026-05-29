# 修正"做对了还追问"问题 - 简短总结

## 新增的 Modes

### `TeachingMode` (session_state.py)
- `solve_new_problem` - 学生问新问题
- `grade_uploaded_attempt` - 刚评完上传答案（关键模式）
- `continue_teaching` - 继续 Socratic 对话
- `full_solution` - 学生要求完整解答

## Structured Action 长什么样

```python
# Agent 输出 JSON（不再是自由文本）:
{
  "action": "confirm_correct_and_stop",
  "message": "Great work! Your answer is correct.",
  "reasoning": "Verifier confirmed answer is correct"
}
```

**5 种 Actions**:
1. `confirm_correct_and_stop` - 确认正确并停止
2. `give_hint` - 给提示继续
3. `give_feedback` - 解释错误
4. `ask_clarification` - 请学生澄清
5. `show_full_solution` - 完整解答

## 三种情况处理

| Verifier 结果 | Agent 想做 | Rule Enforcement | 最终输出 |
|--------------|-----------|------------------|----------|
| **CORRECT** | 可能继续追问 ❌ | **强制**改为 `confirm_correct_and_stop` ✅ | "Correct!" + 停止 |
| **INCORRECT** | give_hint/feedback | 允许，禁止 confirm | Socratic 引导 |
| **UNCERTAIN** | 可能猜测对错 | **强制**改为 `ask_clarification` | "请解释推理" |

## 为什么能解决"做对了还追问"？

### Before（问题）:
```
Verifier: is_correct=True
  ↓
agent.process_query(通用 prompt)
  ↓
Agent 自由发挥 → "让我们再检查一下..." ❌
```

### After（修复）:
```
Verifier: is_correct=True
  ↓
orchestrate_teaching_response:
  1. Prompt 明确说 "CORRECT → must confirm_and_stop"
  2. Agent 返回 JSON action
  3. enforce_teaching_rules 检查:
     if is_correct && action != confirm_correct_and_stop:
       强制改为 confirm_correct_and_stop ✅
  ↓
"Great work!" + 自动结束 session
```

**关键**：Verifier 说对了 → enforcement 层**强制停止**，Agent 无法绕过。

## 新增文件
1. `session_state.py` - Modes & Actions 定义
2. `teaching_orchestrator.py` - Orchestration + Rule Enforcement

## 修改文件
1. `claire_agent.py` - 新增 `process_structured_teaching()` 方法
2. `app.py` - 使用 orchestrator 替代直接调用 agent

## 实现细节亮点

### 1. Mode-aware prompt injection
每次调用前显式注入已知事实：
```python
VERIFIER RESULT: CORRECT (confirmed by SymPy)
MANDATORY RULE: You MUST output "confirm_correct_and_stop"
```

### 2. Hard rule enforcement
```python
if context.is_correct and decision.action != CONFIRM_CORRECT_AND_STOP:
    # 强制修改
    return TeachingDecision(
        action=CONFIRM_CORRECT_AND_STOP,
        message="Great work!",
        reasoning="Enforced: verifier says correct"
    )
```

### 3. UI 自动结束
```python
if decision.action == AgentAction.CONFIRM_CORRECT_AND_STOP:
    st.session_state.teaching_mode = False
    st.info("Session complete!")
```

## 测试场景

✅ **场景 1**: 上传正确答案
- 期望：Claire 说 "Correct!" → 停止
- 结果：enforce_teaching_rules 强制 confirm_and_stop

✅ **场景 2**: 上传错误答案
- 期望：Socratic 引导
- 结果：允许 give_hint/give_feedback

✅ **场景 3**: 对话中学生改对了
- 期望：确认并停止
- 结果：mode=continue_teaching，verifier re-check → confirm_and_stop

## 架构图

```
┌─────────────────────┐
│  学生上传答案        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Vision + Verifier    │
│ → is_correct: bool   │  ← GROUND TRUTH (SymPy)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ TeachingContext     │
│ mode: GRADE_ATTEMPT │
│ is_correct: True    │
└──────┬──────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ orchestrate_teaching_response    │
│  1. build_mode_aware_prompt      │
│  2. agent.process_structured     │
│  3. parse_agent_decision         │
│  4. enforce_teaching_rules ✅    │ ← 强制检查
└──────┬───────────────────────────┘
       │
       ▼
┌─────────────────────┐
│ TeachingDecision    │
│ action: confirm_    │
│        correct_     │
│        and_stop     │
│ message: "Correct!" │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ UI 自动结束 session │
└─────────────────────┘
```

## 关键差异总结

| Before | After |
|--------|-------|
| Agent 自由决定是否停止 | Verifier 决定 → Enforcement 强制 |
| 通用 teaching prompt | Mode-aware prompt with verifier facts |
| 直接文本输出 | Structured JSON action |
| 无强制检查 | Rule enforcement layer |
| 学生做对了还追问 😞 | 学生做对了自动停止 ✅ |
