# Claire 内测准备 — Claude Code 改动提示词

每个提示词独立实现，完成后对应 metric 达到 10/10。
按优先级排序：越靠前越影响内测。

---

## Prompt 1 — 首页价值主张 + 引导流程
**Metric: 用户上手体验 (Onboarding) → 目标 10/10**

```
I'm working on a Streamlit app called Claire (app.py) — an AI calculus exam prep tool.

Problem: The homepage has no clear value proposition. Users land and don't immediately understand what to do or why Claire is better than ChatGPT.

Please make the following changes to app.py:

1. HERO SECTION (shows when no messages and no materials uploaded):
   Add a clean hero section at the top of the main area with:
   - Headline: "Your AI study partner for calc exam week."
   - 3 short bullet points (use emoji icons):
     - 📂 Upload your past exams → Claire extracts every problem
     - 🎯 5-min diagnostic → finds exactly where you're weak  
     - 🧑‍🏫 Step-by-step practice → teaches method, not just answers
   - A primary CTA button: "Upload your exam PDF →" that scrolls/focuses the sidebar uploader
   - A secondary text link: "No PDF? Start with an example →" that starts with a sample problem

2. UPLOAD PROMPT (sidebar):
   When no materials are uploaded, add a short caption above the uploader:
   "Paste in your past exams, notes, or syllabus. Claire will read them and build your practice set."

3. POST-DIAGNOSTIC GUIDANCE:
   After the diagnostic completes and the user sees their result, add a clear next-step prompt:
   - If they have materials: "Here's your personalized practice queue → click any problem to start"
   - If no materials: "Upload your past exams to get problems tailored to your actual course →"

4. EMPTY CHAT STATE:
   When messages list is empty but diagnostic is done, show a short prompt:
   "Ask me anything, or pick a problem from the sidebar to practice."

Keep all existing logic intact. Only add UI elements.
```

---

## Prompt 2 — Stripe 付费墙接入
**Metric: 付费转化 → 目标 10/10**

```
I'm working on a Streamlit app called Claire (app.py, quota.py, claire_agent.py).

I need to add a real Stripe checkout flow. The Stripe keys are already in st.secrets as STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY (test mode).

Please implement the following:

PRICING:
- Free tier: 3 queries (anonymous) or 5 premium queries/day (logged in)
- Pro tier: $9.99/month — unlimited Claude Sonnet queries

CHANGES NEEDED:

1. quota.py — add `is_pro_user(user_id)` function:
   - Query Supabase `payments` table for active subscription
   - Return True if user has active paid subscription
   - Cache result in st.session_state for the session

2. app.py — paywall modal:
   When a user hits their free query limit, instead of the current soft CTA:
   - Show a non-dismissable modal (use st.dialog) with:
     - Title: "You've used your free credits"
     - Body: "Upgrade to Pro for unlimited practice with Claude — the model that actually explains calculus."
     - Price: "$9.99/month, cancel anytime"
     - Button: "Upgrade →" (links to Stripe checkout)
     - Secondary: "Continue with basic model" (switches to DeepSeek, shows once per session)
   - DO NOT block logged-out users from upgrading (prompt login first if not logged in)

3. stripe_checkout.py — create new file:
   - Function `create_checkout_session(user_email, user_id)` that:
     - Calls stripe.checkout.Session.create()
     - price: monthly recurring $9.99
     - success_url: APP_URL + "?upgraded=true"
     - cancel_url: APP_URL
     - metadata: {user_id: user_id}
     - Returns the checkout URL
   - Function `handle_upgrade_success()`:
     - Reads ?upgraded=true from URL params
     - Updates Supabase payments table with user_id, status='active', started_at=now()
     - Shows success toast and clears the param从现在开始，这一轮不要做“重付费墙 + Stripe 强转化”那套。先按当前产品阶段，改成更合理的免费 / Pro 分层。重点是：不大改架构，不大改 UI，只做最小可用实现。

先明确产品判断：

## 产品判断（非常重要）
Claire 现在还在早期，核心目标不是立刻榨付费，而是：
1. 让用户能完整体验核心流程
2. 收集真实 usage
3. 让用户感受到“高级功能真的更值钱”

所以不要做：
- 免费只给 3 次就几乎不能用
- 一上来硬性 Stripe 付费墙
- 把普通问答也强行卡死

正确方向是：

## 新的分层设计

### Free tier
- 默认尽量放开
- 每天可问 20 条（可以先按 session/user 近似实现，后续再细化）
- 默认模型：DeepSeek / basic model
- 免费用户可以完整体验这些核心流程：
  - 上传资料
  - diagnostic
  - 基础 practice
  - 基础问答 / 讲解
- 不要让免费用户感觉“根本用不了”

### Pro tier
- Claude Sonnet
- 卖点不是“更多次数”，而是“更好的结果”
- Pro 的核心价值：
  1. 更强的 step-by-step explanation
  2. 更高质量的复杂题讲解
  3. 根据上传题库 / 学校风格 / 课程材料生成题目
  4. exam-style / course-specific problem generation
- 这些“高级能力”才是主要收费点

一句话：
- 免费卖体验
- 付费卖质量和个性化

---

## 这轮要实现的内容

### 1. 调整 quota / entitlement 设计
请先检查现有 quota.py / app.py 里关于免费额度、premium query、Claude 限额、DeepSeek fallback 的逻辑。

目标改成：
- 免费用户：默认使用 basic model（DeepSeek）
- 免费用户：每天 20 条 basic queries
- Pro 用户：Claude Sonnet unlimited（先按“无限制/极高上限”实现即可）
- 不要让免费用户轻易撞到完全不可用的状态

如果现有逻辑里已经有：
- anonymous 免费次数
- logged-in premium 次数
- DeepSeek fallback
请尽量复用，而不是重写整套 quota 系统

### 2. 定义“高级功能” entitlement
新增一个清晰但最小的判断层，例如：
- `can_use_basic_chat`
- `can_use_pro_model`
- `can_generate_course_specific_problems`

不要求你一定按这个命名，但逻辑上要能区分：
- 普通免费使用
- Pro 专属高价值功能

注意：不要把所有功能都绑到 Pro。
要保留免费用户的基本可用性。

### 3. Paywall 改成“功能触发型”，不是“生存型”
不要做那种：
- 用完几次就彻底不让用

改成：
- 免费用户平时继续用 basic model
- 当用户触发真正高价值功能时，再提示升级

优先作为 Pro-only / paywall 的功能：
1. 根据上传题库生成新题
2. 按学校/课程风格生成 exam-style problems
3. 明显更高质量的 Claude explanation（尤其复杂题）

也就是说，paywall 出现在：
- “Generate exam-style problems”
- “Generate more like this from my materials”
- “Use Claude for deeper explanation”
这种地方

而不是：
- 用户刚开始体验时就被拦住

### 4. UI 改动要小
不要大改首页，不要重排布局，不要顺手优化一堆别的东西。

只允许做小范围插入：
- 在高级功能按钮附近加小字说明：Pro / Claude
- 在触发高级功能时弹出升级提示
- 在普通问答降级到 basic model 时给轻提示（例如：using basic model）

不要重做整个 paywall 页面。
不要大改 browse mode / practice mode / diagnostic UI。

### 5. Stripe 不要作为这轮核心
如果当前代码里已经开始做 Stripe 设计，可以保留接口或 TODO，但这轮不要把重点放在完整支付闭环上。

这轮重点是：
- entitlement / gating 逻辑
- free vs pro 体验设计
- paywall placement

如果你需要保留 Stripe 接口：
- 可以保留 stub / integration point
- 但不要为了支付去重构现有 app flow

---

## 实现原则（必须遵守）

1. 不准大改架构
2. 不准大改 UI
3. 不准顺手重构 unrelated code
4. 优先复用现有 quota / model routing / session_state 逻辑
5. 如果某一步需要大改，先停下来告诉我

---

## 你先做的第一步
先不要直接开写一大堆代码。

先告诉我：
1. 当前 free / premium / DeepSeek / Claude 的现有逻辑在哪里
2. 你准备改哪些文件和函数
3. 哪些功能会被定义为 Pro-only
4. 哪些地方会出现升级提示
5. 你的实现会如何保证：免费用户仍然能完整体验核心流程

然后再开始改。

---

## 再强调一次产品目标
这轮不是“最大化立刻收费”，而是：

- 免费用户可以真的用起来
- Pro 的价值非常清楚
- 升级发生在“用户最想要更强能力”的时刻

不要把 Claire 做成一个一上来就收费、但用户还没感受到价值的产品。

4. app.py — check for upgrade on load:
   Call handle_upgrade_success() near the top of app.py (after session init)
   If user is pro, set st.session_state.is_pro = True and bypass all quota checks

Keep all existing quota logic as fallback. Pro users should never see quota messages.
```

---

## Prompt 3 — Session 迁移到 Supabase
**Metric: 技术稳定性 → 目标 10/10**

```
I'm working on a Streamlit app called Claire. Currently, session data is stored in .sessions/<id>.json on disk (session_store.py). On Streamlit Cloud, this filesystem is ephemeral — all session data is lost on every redeploy.

Please migrate session storage to Supabase while keeping the same API.

SUPABASE SETUP:
The Supabase client is initialized via st.secrets["SUPABASE_URL"] and st.secrets["SUPABASE_KEY"].
Create a new table called `sessions` with these columns:
- session_id: text (primary key)
- data: jsonb
- updated_at: timestamptz (default now())

CHANGES TO session_store.py:

1. Replace file-based save/load with Supabase upsert/select:
   - save_session(): upsert into `sessions` table (session_id, data as JSON, updated_at)
   - load_session(): select from `sessions` where session_id = ?
   - delete_session(): delete from `sessions` where session_id = ?

2. Add graceful fallback:
   - If Supabase is unavailable (no keys, network error), fall back to file-based storage
   - Log a warning but don't crash

3. Keep the exact same function signatures so app.py doesn't need changes.

4. Add a cleanup function `cleanup_old_sessions(days=30)` that deletes sessions older than 30 days.
   Call this function once per day (check st.session_state for last cleanup timestamp).

Also write the SQL to create the sessions table as a comment at the top of session_store.py.
```

---

## Prompt 4 — Exam Simulation Mode UI 完成
**Metric: 核心功能完整度 → 目标 10/10**

```
I'm working on a Streamlit app called Claire (app.py, exam_mode.py).

exam_mode.py has the data structures for exam simulation (ExamSession, ExamQuestion, ExamResult) but the UI in app.py is incomplete. Please build out the full Exam Simulation experience.

FLOW:
1. Entry point: A button "📝 Simulate an Exam" in the sidebar (only show if materials are uploaded)

2. Exam setup screen:
   - Show list of available exams extracted from materials (group by source file)
   - Let user pick one or "Mix — random 5 questions from all materials"
   - Show estimated time: (num_questions × 8 minutes)
   - Start button

3. Exam screen (one question at a time):
   - Show question number and timer (count up, no pressure)
   - Show full question text with math rendering
   - Large text area for the student's answer/work
   - "Next →" button (no hints, no help — this is exam conditions)
   - Small "🚨 I'm stuck" button that ends the exam early and goes to review

4. Results screen (after all questions answered):
   - Score: X/Y questions attempted
   - Topic breakdown: which topics they attempted, which they skipped
   - Predicted exam score range (use exam_mode.py ExamResult.predicted_low/high)
     Formula: attempted_ratio × 0.85 as low, × 1.05 as high (rough estimate)
   - Weak areas: topics with skipped or incomplete answers
   - CTA: "Practice your weak spots →" (goes to practice mode filtered to weak topics)

5. After exam, automatically:
   - Add weak topics to practice queue (call practice_planner.prioritize_questions with these topics boosted)
   - Save updated session

Keep all existing app.py logic. Add exam mode as a new state in practice_state["mode"] = "exam".
The exam must be playable without uploading materials — use the fallback question bank if no materials.
```

---

## Prompt 5 — 差异化可见性：Topic Map UI
**Metric: 差异化 vs ChatGPT → 目标 10/10**

```
I'm working on a Streamlit app called Claire (app.py, exam_panic.py, topics/).

Currently, the topic analysis from uploaded materials is computed but barely shown to users. I want to make the "Claire understands YOUR exam" moment visible and impressive.

Please add a Topic Map section that appears after materials are uploaded and analyzed.

DESIGN:

1. Location: In the main area, shown between the hero/diagnostic section and the practice queue.
   Only show when materials are uploaded AND diagnostic is complete.

2. Header: "📊 Your Exam at a Glance"
   Subtitle: "Based on [X] problems from [Y] exams"

3. Topic frequency bars:
   For each detected topic (from exam_panic.py ExamSummary.top_topics):
   - Show topic name (user-friendly from TOPIC_DISPLAY)
   - A simple horizontal progress bar (st.progress) scaled to max frequency
   - A badge: "🔥 High frequency" if top 3, "⚠️ Study this" if it's in user's weak topics
   - Small caption: "[N] problems across your materials"
   
   Max 8 topics shown. Add "Show all →" expander for the rest.

4. Risk callout (if applicable):
   If any of the user's weak topics (from diagnostic) overlap with high-frequency exam topics:
   Show a yellow warning box:
   "⚠️ [Topic] appears in [N] of your past exams and was flagged as a weak area. Prioritize this."

5. Minimum passing path:
   Small section below: "📍 Focus here first (minimum to pass)"
   Show 3-4 topics as chips/badges that together cover the most exam weight.

Keep it clean — this should feel like a dashboard, not a wall of text.
Use st.columns for layout. No tables (Streamlit markdown tables render poorly on mobile).
```

---

## Prompt 6 — 错误体验 + 等待状态优化
**Metric: 用户上手体验 + 技术稳定性 → 补充**

```
I'm working on a Streamlit app called Claire (app.py, claire_agent.py).

Currently, when AI responses are loading, users see a blank spinner with no context.
And when errors happen, users see raw Python error messages.

Please fix both:

1. LOADING STATES — replace all `with st.spinner(""):` with meaningful messages:
   - While uploading/parsing materials: "Reading your exams... extracting problems 📄"
   - While running diagnostic: "Analyzing your answers..."
   - While generating AI response: Pick one randomly from:
     - "Working through it..."
     - "Checking the approach..."
     - "One moment..."
   - While switching to DeepSeek: "Switching to base model..."

2. ERROR HANDLING — wrap the main process_query call in a try/except:
   - If Anthropic API error (rate limit, timeout): 
     Show: "Slow down a bit — I'm catching up. Try again in a few seconds."
     Auto-retry once after 3 seconds.
   - If DeepSeek API error:
     Show: "The base model is temporarily unavailable. Try again in a moment."
   - If any other error:
     Show: "Something went wrong on my end. Try refreshing the page."
     Log the full traceback server-side but never show it to the user.

3. EMPTY STATES:
   - If PDF uploaded but 0 problems extracted:
     Show: "I couldn't find any problems in this file. Try uploading a past exam or problem set PDF."
   - If diagnostic done but no materials:
     Show a gentle nudge: "Upload your past exams to get problems from your actual course. →"

No user should ever see a Python traceback or an API error code.
```

---

## 内测就绪检查清单

实现以上 6 个 prompt 后，逐一确认：

- [ ] Prompt 1 ✅ — 用户进来10秒内知道Claire是什么
- [ ] Prompt 2 ✅ — 有真实付费入口，出血换来的收入
- [ ] Prompt 3 ✅ — 重新部署不丢用户数据
- [ ] Prompt 4 ✅ — Exam Simulation 完整跑通
- [ ] Prompt 5 ✅ — "这是为我专属的"第一感观
- [ ] Prompt 6 ✅ — 没有任何报错出现在用户面前

完成以上 → Claire 内测就绪。

**还有一件事这里没覆盖但影响内测：**
把反馈 Google Form 的链接嵌入 app 里（比如侧边栏底部或对话结束后），让用户不需要额外找入口就能填。
```
