"""
Claire - Making Calculus Clear
Calculus Cram: Exam prep powered by AI
"""

import streamlit as st
from claire_agent import ClaireAgent
from exam_context import analyze_files, ExamContext
from placement_test import (
    build_questions_from_bank,
    get_fallback_questions,
    score_placement,
    PlacementQuestion,
)
from session_store import new_session_id, save_session, load_session
from practice_planner import prioritize_questions, format_study_plan
from practice_planner import prioritize_questions, format_study_plan, study_plan_for_prompt
from tracker import track, track_feedback
from auth import handle_oauth_callback, get_user, show_login_button, sign_out

# Page config
st.set_page_config(
    page_title="Claire",
    page_icon="📐",
    layout="centered"
)

# Custom CSS for cleaner look and labels
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px; }
    .stButton button { font-weight: 500; }
    div[data-testid="stExpander"] { border: none; }

    /* Category labels */
    .category-label {
        display: inline-block;
        padding: 2px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 12px;
        background: #e8f4f8;
        color: #1a5f7a;
    }
    .difficulty-easy {
        background: #d4edda;
        color: #155724;
    }
    .difficulty-medium {
        background: #fff3cd;
        color: #856404;
    }
    .difficulty-hard {
        background: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────
# Session ID — lives in URL as ?s=<id>
# ────────────────────────────────────────────────────────────
# Handle Google OAuth callback (must be before any other st calls)
handle_oauth_callback()

if "session_id" not in st.session_state:
    params = st.query_params
    sid = params.get("s", None)
    if sid:
        st.session_state.session_id = sid
        st.session_state._restored = False   # will attempt restore below
    else:
        # Brand-new visitor — generate an ID and put it in the URL
        sid = new_session_id()
        st.session_state.session_id = sid
        st.query_params["s"] = sid
        st.session_state._restored = True    # nothing to restore
        track(sid, "session_start")

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = ClaireAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "exam_context" not in st.session_state:
    st.session_state.exam_context = ExamContext()
if "selected_problem" not in st.session_state:
    st.session_state.selected_problem = None
if "pending_problem" not in st.session_state:
    st.session_state.pending_problem = None
# Placement test state
# "not_started" → "choosing_track" → "in_progress" → "done" | "skipped"
if "placement_stage" not in st.session_state:
    st.session_state.placement_stage = "not_started"
if "placement_questions" not in st.session_state:
    st.session_state.placement_questions = []
if "placement_answers" not in st.session_state:
    st.session_state.placement_answers = []
if "placement_current" not in st.session_state:
    st.session_state.placement_current = 0
if "placement_result" not in st.session_state:
    st.session_state.placement_result = None
if "calc_track" not in st.session_state:
    st.session_state.calc_track = None
if "prioritized_questions" not in st.session_state:
    st.session_state.prioritized_questions = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "show_tier_notice" not in st.session_state:
    st.session_state.show_tier_notice = False
# "hidden" → "showing" (after upload) → "done" (user clicked through)
if "exam_scope_stage" not in st.session_state:
    st.session_state.exam_scope_stage = "hidden"
if "pending_similar" not in st.session_state:
    st.session_state.pending_similar = False

FREE_PREMIUM_QUERIES = 5

# ────────────────────────────────────────────────────────────
# Restore from disk if this is a returning visitor
# ────────────────────────────────────────────────────────────
if not st.session_state.get("_restored", False):
    saved = load_session(st.session_state.session_id)
    st.session_state._restored = True

    if saved and saved.get("material_names"):
        # Rebuild ExamContext from saved questions (no need to re-upload)
        from question_bank import QuestionBank
        qb = QuestionBank()
        qb.questions = saved["questions"]
        ctx = ExamContext(
            material_names=saved["material_names"],
            materials=["(restored)"] * len(saved["material_names"]),
        )
        ctx.question_bank = qb
        st.session_state.exam_context = ctx
        st.session_state.agent.set_exam_context(ctx)

        # Restore user level + placement
        st.session_state.placement_stage = saved["placement_stage"]
        st.session_state.placement_result = saved["placement_result"]
        st.session_state.placement_questions = saved["placement_questions"]
        st.session_state.placement_answers = saved["placement_answers"]
        st.session_state.calc_track = saved["calc_track"]

        # Restore weak/strong topics into agent
        p_result = saved["placement_result"]
        if p_result:
            st.session_state.agent.set_diagnostic_result(p_result)
            bank = ctx.question_bank if ctx.has_questions() else None
            prioritized = prioritize_questions(p_result, bank)
            st.session_state.prioritized_questions = prioritized
        else:
            st.session_state.agent.user_level = saved["user_level"]

    elif saved and saved.get("calc_track"):
        # No materials but has done placement (e.g., skipped upload)
        st.session_state.placement_stage = saved["placement_stage"]
        st.session_state.placement_result = saved["placement_result"]
        st.session_state.placement_questions = saved["placement_questions"]
        st.session_state.placement_answers = saved["placement_answers"]
        st.session_state.calc_track = saved["calc_track"]
        p_result = saved["placement_result"]
        if p_result:
            st.session_state.agent.set_diagnostic_result(p_result)
        else:
            st.session_state.agent.user_level = saved["user_level"]


def _save_current_session():
    """Snapshot current state to disk."""
    ctx = st.session_state.exam_context
    questions = ctx.question_bank.questions if ctx.question_bank else []
    save_session(
        st.session_state.session_id,
        material_names=ctx.material_names,
        questions=questions,
        detected_patterns=ctx.detected_patterns,
        user_level=st.session_state.agent.user_level,
        calc_track=st.session_state.calc_track,
        placement_stage=st.session_state.placement_stage,
        placement_result=st.session_state.placement_result,
        placement_questions=st.session_state.placement_questions,
        placement_answers=st.session_state.placement_answers,
    )


# ============================================================
# PROBLEM DETAIL DIALOG
# ============================================================
@st.dialog("Problem Details", width="large")
def show_problem_detail(question):
    """Show problem details in a popup dialog."""
    st.markdown(f"### {question.format_source()}")

    # Difficulty badge
    diff_class = f"difficulty-{question.difficulty}"
    st.markdown(
        f'<span class="category-label {diff_class}">{question.difficulty.upper()}</span>',
        unsafe_allow_html=True
    )

    # Category labels
    if question.categories:
        labels_html = " ".join(
            f'<span class="category-label">{cat}</span>'
            for cat in question.categories
        )
        st.markdown(labels_html, unsafe_allow_html=True)

    st.markdown("---")

    # Full problem text with math rendering
    st.markdown("**Problem:**")
    formatted_text = question.get_formatted_text()
    st.markdown(formatted_text)

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Practice this problem", use_container_width=True, type="primary"):
            st.session_state.pending_problem = question.text
            st.session_state.selected_problem = None
            st.rerun()
    with col2:
        if st.button("Close", use_container_width=True):
            st.session_state.selected_problem = None
            st.rerun()

agent = st.session_state.agent
exam_context = st.session_state.exam_context


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Claire")

    st.divider()

    # Course materials
    st.caption("Course Materials")
    current_user = get_user()
    if not current_user:
        show_login_button("Sign in to upload materials")
        uploaded = None
    else:
        st.caption(f"👤 {current_user.email}")
        if st.button("Sign out", use_container_width=True, key="signout"):
            sign_out()
            st.rerun()
        uploaded = st.file_uploader(
            "Upload",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

    if uploaded:
        if st.button("Load", use_container_width=True):
            files = [(f.name, f.getvalue()) for f in uploaded]
            with st.spinner("Loading..."):
                context = analyze_files(files)
                st.session_state.exam_context = context
                agent.set_exam_context(context)
            track(st.session_state.session_id, "file_upload", {
                "file_count": len(files),
                "names": [f.name for f in uploaded],
            })
            # Show exam scope analyzer first, then placement test
            st.session_state.exam_scope_stage = "showing"
            if st.session_state.placement_stage in ("not_started", "choosing_track"):
                st.session_state.placement_stage = "not_started"
            # Clear chat so the analyzer screen shows immediately
            st.session_state.messages = []
            agent.conversation_history = []
            _save_current_session()
            st.rerun()

    if exam_context.has_context():
        count = exam_context.get_question_count()
        st.success(f"{count} problems loaded" if count else "Materials loaded")

        # Expandable problem list with clickable items
        if exam_context.has_questions():
            with st.expander(f"View all problems ({count})"):
                bank = exam_context.question_bank
                for i, q in enumerate(bank.questions):
                    source_label = q.format_source()

                    # Problem header with view button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{source_label}**")
                    with col2:
                        if st.button("View", key=f"view_{i}", use_container_width=True):
                            st.session_state.selected_problem = q

                    # Preview text
                    preview = q.text[:120] + "..." if len(q.text) > 120 else q.text
                    st.caption(preview)

                    # Category and difficulty labels
                    labels = []
                    if q.difficulty:
                        diff_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(q.difficulty, "")
                        labels.append(f"{diff_emoji} {q.difficulty}")
                    labels.extend(q.categories[:2])  # Show first 2 categories
                    if labels:
                        st.caption(" · ".join(labels))

                    if i < len(bank.questions) - 1:
                        st.divider()

        if st.button("Clear", use_container_width=True):
            st.session_state.exam_context = ExamContext()
            agent.clear_exam_context()
            st.rerun()

    st.divider()

    # Show student level
    if st.session_state.placement_result or st.session_state.placement_stage == "skipped":
        level = agent.user_level
        level_labels = {
            "beginner": "🌱 Beginner",
            "intermediate": "📚 Intermediate",
            "advanced": "🚀 Advanced",
        }
        st.caption("Student Level")
        st.markdown(level_labels.get(level, level))
        if st.button("Retake diagnostic", use_container_width=True):
            st.session_state.placement_stage = "not_started"
            st.session_state.placement_questions = []
            st.session_state.placement_answers = []
            st.session_state.placement_current = 0
            st.session_state.placement_result = None
            st.session_state.messages = []
            agent.conversation_history = []
            _save_current_session()
            st.rerun()
        st.divider()

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        agent.conversation_history = []
        st.rerun()

    st.divider()

    # Feedback
    with st.expander("💬 Leave feedback"):
        fb_text = st.text_area(
            "What's not working? Any suggestions?",
            key="feedback_text",
            placeholder="e.g. The explanation was confusing, wrong answer, missing feature...",
            label_visibility="visible",
        )
        fb_col1, fb_col2, fb_col3 = st.columns(3)
        with fb_col1:
            if st.button("👍", use_container_width=True, key="fb_good"):
                track_feedback(st.session_state.session_id, fb_text or "", rating="good")
                st.success("Thanks!")
        with fb_col2:
            if st.button("👎", use_container_width=True, key="fb_bad"):
                track_feedback(st.session_state.session_id, fb_text or "", rating="bad")
                st.success("Thanks!")
        with fb_col3:
            if st.button("Send", use_container_width=True, key="fb_send"):
                if fb_text.strip():
                    track_feedback(st.session_state.session_id, fb_text)
                    st.success("Got it!")
                else:
                    st.warning("Write something first")


# ============================================================
# SHOW PROBLEM DIALOG IF SELECTED
# ============================================================
if st.session_state.selected_problem:
    show_problem_detail(st.session_state.selected_problem)

# ============================================================
# PROCESS PENDING SIMILAR PROBLEM REQUEST
# ============================================================
if st.session_state.pending_similar:
    st.session_state.pending_similar = False
    similar_query = (
        "Generate a new practice problem similar to what we just worked on "
        "(use different numbers or a slight variation). "
        "Give me just the problem statement — don't solve it yet."
    )
    track(st.session_state.session_id, "query", {"query": "generate_similar"})
    st.session_state.query_count += 1

    if st.session_state.query_count > FREE_PREMIUM_QUERIES and agent.model_tier == "premium":
        switched = agent.switch_to_deepseek()
        if switched:
            st.session_state.show_tier_notice = True

    st.session_state.messages.append({"role": "user", "content": "↻ Generate a similar problem"})
    with st.spinner(""):
        result = agent.process_query(similar_query)
    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
    st.rerun()


# ============================================================
# PROCESS PENDING PROBLEM FROM DIALOG
# ============================================================
if st.session_state.pending_problem:
    problem_text = st.session_state.pending_problem
    st.session_state.pending_problem = None

    # Add user message
    st.session_state.messages.append({"role": "user", "content": problem_text})

    # Get agent response
    with st.spinner(""):
        result = agent.process_query(problem_text)

    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
    st.rerun()


# ============================================================
# PLACEMENT TEST HELPERS
# ============================================================

def _start_placement_from_materials():
    """Start placement test using questions from uploaded materials (LaTeX pre-cleaned)."""
    bank = st.session_state.exam_context.question_bank if st.session_state.exam_context.has_questions() else None
    questions = build_questions_from_bank(bank, limit=5)
    if not questions:
        track = st.session_state.calc_track or "calc_i"
        questions = get_fallback_questions(track)
    st.session_state.placement_questions = questions
    st.session_state.placement_answers = [None] * len(questions)
    st.session_state.placement_current = 0
    st.session_state.placement_stage = "in_progress"


def _start_placement_for_track(track: str):
    """Start placement test for a specific calc track (no materials)."""
    st.session_state.calc_track = track
    questions = get_fallback_questions(track)
    st.session_state.placement_questions = questions
    st.session_state.placement_answers = [None] * len(questions)
    st.session_state.placement_current = 0
    st.session_state.placement_stage = "in_progress"
    _save_current_session()


def _finish_placement():
    """Score placement test and apply result."""
    result = score_placement(
        st.session_state.placement_questions,
        st.session_state.placement_answers,
    )
    st.session_state.placement_result = result
    st.session_state.placement_stage = "done"

    track(st.session_state.session_id, "placement_done", {
        "level": result.level,
        "score": result.score,
        "total": result.total,
        "weak_topics": result.weak_topics,
    })

    # Apply level + weak/strong topics to the agent
    agent.set_diagnostic_result(result)

    # Build prioritized practice queue from uploaded materials
    bank = st.session_state.exam_context.question_bank if st.session_state.exam_context.has_questions() else None
    prioritized = prioritize_questions(result, bank)
    st.session_state.prioritized_questions = prioritized

    _save_current_session()


def _skip_placement():
    """Skip the placement test."""
    st.session_state.placement_stage = "skipped"
    agent.set_user_level("intermediate")
    _save_current_session()


def _inject_welcome_message(result):
    """Send a personalized first assistant message based on diagnostic level and weak topics."""
    from practice_planner import TOPIC_LABELS
    level = result.level
    score_str = f"{result.score}/{result.total}"

    # Build weak/strong topic phrase
    weak_labels = [TOPIC_LABELS.get(t, t.replace("_", " ").title()) for t in result.weak_topics]
    strong_labels = [TOPIC_LABELS.get(t, t.replace("_", " ").title()) for t in result.strong_topics]

    focus_line = ""
    if weak_labels:
        focus_line = f"Based on the diagnostic, let's pay extra attention to: **{', '.join(weak_labels)}**."
        if strong_labels:
            focus_line += f" You're solid on {', '.join(strong_labels)}, so we'll move faster there."

    if level == "beginner":
        msg = (
            f"Diagnostic done — {score_str}. No worries, everyone starts somewhere.\n\n"
            f"{focus_line}\n\n"
            "I'll walk you through everything step by step in plain language — no jargon "
            "unless we define it first. "
            "Just paste in a problem you want to work on. 🌱"
        )
    elif level == "intermediate":
        msg = (
            f"Diagnostic done — {score_str}. You've got the basics.\n\n"
            f"{focus_line}\n\n"
            "We'll focus on picking the right method quickly and avoiding common traps. "
            "Drop in any problem. 📚"
        )
    else:  # advanced
        msg = (
            f"Diagnostic done — {score_str}. Solid foundation.\n\n"
            f"{focus_line}\n\n"
            "I'll keep explanations concise and focus on strategy and exam speed. "
            "Throw a problem at me. 🚀"
        )

    # Append prioritized problem list if materials were loaded
    prioritized = st.session_state.get("prioritized_questions", [])
    if prioritized:
        import re as _re
        plan_lines = ["\n\n---\n**Recommended practice order from your materials:**"]
        for i, q in enumerate(prioritized[:6], 1):
            src = getattr(q, "source", "")
            pid = getattr(q, "problem_id", "")
            diff = getattr(q, "difficulty", "medium")
            diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(diff, "")
            label = f"{src} — {pid}" if pid else src
            pts_m = _re.search(r"(\d{1,3})\s*(?:pts?|points?)", getattr(q, "text", ""), _re.IGNORECASE)
            pts_str = f" · {pts_m.group(1)} pts" if pts_m else ""
            plan_lines.append(f"{i}. {diff_icon} **{label}**{pts_str}")
        plan_lines.append("\nJust click any problem in the sidebar, or paste one here.")
        msg = msg + "\n".join(plan_lines)

        # Strip stray blank lines
    msg = msg.replace("\n\n\n\n", "\n\n").strip()
    st.session_state.messages.append({"role": "assistant", "content": msg})
    agent.conversation_history.append({"role": "assistant", "content": msg})


def _render_exam_scope_analyzer():
    """
    Render the Exam Scope Analyzer screen after file upload.
    Shows topic distribution, high-freq topics, risk areas, and min passing path.
    Returns True if it rendered (caller should skip other UI).
    """
    if st.session_state.exam_scope_stage != "showing":
        return False

    from exam_analyzer import generate_exam_scope, TOPIC_DISPLAY, TOPIC_EMOJI

    ctx = st.session_state.exam_context
    if not ctx.has_context():
        st.session_state.exam_scope_stage = "done"
        return False

    report = generate_exam_scope(ctx)

    # ── Header ──────────────────────────────────────────────
    st.markdown("## 📊 Exam Scope Analysis")
    names_str = ", ".join(report.material_names[:3])
    if len(report.material_names) > 3:
        names_str += f" +{len(report.material_names) - 3} more"
    st.caption(f"Based on: {names_str}")
    if report.total_questions:
        st.caption(f"📝 {report.total_questions} problems extracted")
    st.markdown("---")

    if not report.topic_distribution:
        st.info("📂 Materials loaded — couldn't detect clear topic patterns. Try uploading a past exam or syllabus for better analysis.")
        if st.button("Continue →", type="primary"):
            st.session_state.exam_scope_stage = "done"
            st.rerun()
        return True

    # ── Two-column layout ────────────────────────────────────
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.markdown("#### 📈 Topic Distribution")
        for topic_name, pct, raw in report.topic_distribution:
            display = TOPIC_DISPLAY.get(topic_name, topic_name.replace("_", " ").title())
            emoji = TOPIC_EMOJI.get(topic_name, "•")
            st.markdown(f"**{emoji} {display}**")
            st.progress(pct / 100, text=f"{pct}%")

        st.markdown("")
        st.markdown("#### 🎯 Likely Exam Topics")
        for t in report.high_freq_topics:
            disp = TOPIC_DISPLAY.get(t, t.replace("_", " ").title())
            st.markdown(f"✅ {disp}")

    with col_right:
        if report.risk_areas:
            st.markdown("#### ⚠️ Risk Areas")
            st.caption("Low/no coverage in your materials — don't skip these:")
            for t in report.risk_areas:
                disp = TOPIC_DISPLAY.get(t, t.replace("_", " ").title())
                st.markdown(f"⚠️ {disp}")

        st.markdown("")
        st.markdown("#### 🚀 Minimum Passing Path")
        st.caption("Master these first to cover ~70% of exam content:")
        for i, t in enumerate(report.min_passing_path, 1):
            pct = next((p for n, p, _ in report.topic_distribution if n == t), 0)
            disp = TOPIC_DISPLAY.get(t, t.replace("_", " ").title())
            st.markdown(f"**{i}.** {disp} — ~{pct}% of exam")

    st.markdown("---")

    # ── CTA buttons ─────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Start Practicing →", type="primary", use_container_width=True):
            st.session_state.exam_scope_stage = "done"
            st.rerun()
    with col_b:
        if st.button("Skip, just ask questions", use_container_width=True):
            st.session_state.exam_scope_stage = "done"
            _skip_placement()
            st.rerun()

    return True


def _render_placement_test():
    """Render the placement test UI."""
    stage = st.session_state.placement_stage

    # ---- NOT STARTED: prompt to take the test ----
    if stage == "not_started":
        st.markdown("## Claire")
        st.caption("Making Calculus Clear · Calculus Cram")
        st.markdown("---")

        st.markdown("### 📝 Quick Diagnostic (5 min)")
        st.markdown(
            "Before we start, let's figure out where you are so I can teach "
            "in a way that actually helps. This is **5 multiple-choice questions** "
            "— should take about 5 minutes."
        )

        has_materials = exam_context.has_questions()
        if has_materials:
            st.info("📂 I'll use questions from your uploaded materials.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start diagnostic", type="primary", use_container_width=True):
                    _start_placement_from_materials()
                    st.rerun()
            with col2:
                if st.button("Skip — let's just start", use_container_width=True):
                    _skip_placement()
                    st.rerun()
        else:
            st.markdown("Which calculus course are you studying?")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Calc I", use_container_width=True, type="primary"):
                    _start_placement_for_track("calc_i")
                    st.rerun()
            with col2:
                if st.button("Calc II", use_container_width=True, type="primary"):
                    _start_placement_for_track("calc_ii")
                    st.rerun()
            with col3:
                if st.button("Calc III", use_container_width=True, type="primary"):
                    _start_placement_for_track("calc_iii")
                    st.rerun()

            st.caption("")
            if st.button("Skip — I just want to start practicing", use_container_width=True):
                _skip_placement()
                st.rerun()

        return True  # signal that we rendered the placement UI

    # ---- IN PROGRESS: show current question ----
    if stage == "in_progress":
        questions = st.session_state.placement_questions
        idx = st.session_state.placement_current
        total = len(questions)

        st.markdown(f"### Diagnostic — Question {idx + 1} of {total}")
        st.progress((idx) / total)

        q = questions[idx]

        # Source + difficulty on one line
        diff_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        diff_icon = diff_colors.get(q.difficulty, "")
        st.caption(f"{diff_icon} {q.difficulty.capitalize()}  ·  {q.source}")

        st.markdown("---")

        # Question body
        if q.question_excerpt:
            # From uploaded materials: render with st.markdown so LaTeX ($...$) works
            st.markdown(q.question_excerpt)
            if q.ask_text:
                st.markdown(f"*{q.ask_text}*")
        else:
            # Fallback / hand-written questions: render LaTeX markdown
            st.markdown(q.prompt)

        st.markdown("")

        # Choices as lettered radio options
        LETTERS = ["A", "B", "C", "D", "E"]
        choice_labels = [f"**{LETTERS[i]}.**  {c}" for i, c in enumerate(q.choices)]

        answer = st.radio(
            "Your answer:",
            options=list(range(len(q.choices))),
            format_func=lambda i: choice_labels[i],
            index=None,
            key=f"placement_q_{idx}",
            label_visibility="visible",
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if idx > 0:
                if st.button("← Back", use_container_width=True):
                    st.session_state.placement_current = idx - 1
                    st.rerun()
        with col2:
            if st.button("Skip diagnostic", use_container_width=True):
                _skip_placement()
                st.rerun()
        with col3:
            is_last = idx == total - 1
            btn_label = "Finish" if is_last else "Next →"
            if st.button(btn_label, use_container_width=True, type="primary", disabled=(answer is None)):
                st.session_state.placement_answers[idx] = answer
                if is_last:
                    _finish_placement()
                else:
                    st.session_state.placement_current = idx + 1
                st.rerun()

        return True

    # ---- DONE: show result ----
    if stage == "done":
        result = st.session_state.placement_result
        level_emoji = {"beginner": "🌱", "intermediate": "📚", "advanced": "🚀"}.get(result.level, "📚")

        st.markdown("### Diagnostic Complete!")
        col_score, col_level = st.columns(2)
        with col_score:
            st.metric("Score", f"{result.score}/{result.total}")
        with col_level:
            st.metric("Level", f"{level_emoji} {result.level.capitalize()}")

        st.markdown(f"*{result.title}*")
        st.markdown("---")

        # Study plan — topic breakdown + prioritized practice queue
        prioritized = st.session_state.get("prioritized_questions", [])
        has_materials = exam_context.has_questions()
        plan_md = format_study_plan(result, prioritized, has_materials=has_materials)
        st.markdown("#### 📋 Your Study Plan")
        st.markdown(plan_md)
        st.markdown("---")

        # Answer review (collapsed by default)
        with st.expander("Review your answers"):
            LETTERS = ["A", "B", "C", "D", "E"]
            for i, (q, a) in enumerate(zip(
                st.session_state.placement_questions,
                st.session_state.placement_answers,
            )):
                correct = a == q.correct_index
                icon = "✅" if correct else "❌"
                diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(q.difficulty, "")
                st.markdown(f"**Q{i+1}** {icon}  ·  {diff_icon} {q.source}")
                # Show excerpt or prompt as preview
                body = q.question_excerpt if q.question_excerpt else q.prompt
                st.caption(body[:160] + "..." if len(body) > 160 else body)
                if a is not None:
                    chosen = q.choices[a] if a < len(q.choices) else "—"
                    correct_ans = q.choices[q.correct_index]
                    if not correct:
                        st.caption(f"You chose: {LETTERS[a] if a < len(LETTERS) else a}. {chosen}")
                        st.caption(f"Correct: {LETTERS[q.correct_index]}. {correct_ans}")
                        st.caption(f"💡 {q.explanation}")
                st.divider()

        if st.button("Let's start practicing! →", type="primary", use_container_width=True):
            st.session_state.placement_stage = "completed"
            # Inject a personalized opening message into chat
            _inject_welcome_message(result)
            st.rerun()

        return True

    return False  # "skipped" or "completed" — don't render placement UI


# ============================================================
# MAIN AREA
# ============================================================

# Header
if st.session_state.exam_scope_stage == "showing":
    # Show exam scope analyzer (after upload, before placement test)
    _render_exam_scope_analyzer()

elif not st.session_state.messages:
    # Show placement test if not done yet
    placement_active = _render_placement_test()

    if not placement_active:
        st.markdown("## Claire")
        st.caption("Making Calculus Clear · Calculus Cram")

        # Show current level if diagnostic was completed
        if st.session_state.placement_result:
            result = st.session_state.placement_result
            level_emoji = {"beginner": "🌱", "intermediate": "📚", "advanced": "🚀"}.get(result.level, "📚")
            st.caption(f"{level_emoji} Teaching level: {result.title}")

        st.markdown("---")

        # Show problems from materials or examples
        if exam_context.has_questions():
            st.markdown("#### From your materials")
            bank = exam_context.question_bank
            for i, q in enumerate(bank.questions[:4]):
                source_label = q.format_source()
                text_preview = q.text[:50] + "..." if len(q.text) > 50 else q.text
                label = f"**{source_label}**: {text_preview}"
                if st.button(label, key=f"q_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": q.text})
                    result = agent.process_query(q.text)
                    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
                    st.rerun()
        else:
            st.markdown("#### Try an example")
            examples = [
                "Find the maximum area of a rectangle with perimeter 100",
                "Maximize xy subject to x + 2y = 10",
                "Find d/dx of ln(x² + 1)",
                "Evaluate ∫ x·eˣ dx",
            ]
            for i, ex in enumerate(examples):
                if st.button(ex, key=f"ex_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": ex})
                    result = agent.process_query(ex)
                    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
                    st.rerun()

else:
    # If materials were just loaded and diagnostic isn't done, show a nudge banner
    if (
        st.session_state.placement_stage == "not_started"
        and exam_context.has_questions()
    ):
        with st.container():
            st.info(
                "📝 **Quick diagnostic available** — I can gauge your level with 5 questions "
                "(~5 min) and teach more effectively. Want to take it?",
                icon=None,
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Take the diagnostic", type="primary", use_container_width=True):
                    st.session_state.messages = []
                    agent.conversation_history = []
                    st.rerun()
            with col2:
                if st.button("Skip, keep chatting", use_container_width=True):
                    _skip_placement()
                    st.rerun()

    # Tier switch notice (show once)
    if st.session_state.show_tier_notice:
        st.info(
            "✨ You've used your 5 free premium credits. "
            "Switched to basic mode — you can keep using Claire without limits.",
            icon=None,
        )
        st.session_state.show_tier_notice = False

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # "Generate similar problem" button — shown after last assistant reply
    if (
        st.session_state.messages
        and st.session_state.messages[-1]["role"] == "assistant"
    ):
        col_sim, col_gap = st.columns([1, 2])
        with col_sim:
            if st.button("↻ Similar problem", key="gen_similar", use_container_width=True):
                st.session_state.pending_similar = True
                st.rerun()

    # Soft upgrade CTA — nudge after extended basic-mode usage (non-intrusive)
    qc = st.session_state.query_count
    if agent.model_tier == "basic" and qc > FREE_PREMIUM_QUERIES and qc % 6 == 2:
        st.caption("💡 Enjoying Claire? **Unlock full power for exam prep** — premium model available.")


# ============================================================
# INPUT - with IME-aware Enter handling
# ============================================================

# Inject JavaScript to handle IME composition properly
import streamlit.components.v1 as components

components.html("""
<script>
(function() {
    const doc = window.parent.document;

    if (doc.body.dataset.imeHandlerAdded) return;
    doc.body.dataset.imeHandlerAdded = 'true';

    let composing = false;

    doc.addEventListener('compositionstart', () => { composing = true; }, true);
    doc.addEventListener('compositionend', () => {
        composing = false;
    }, true);

    doc.addEventListener('keydown', function(e) {
        // keyCode 229 = IME processing, or isComposing, or our composing flag
        if (e.key === 'Enter' && (e.keyCode === 229 || e.isComposing || composing)) {
            e.stopImmediatePropagation();
            e.preventDefault();
            return false;
        }
    }, true);
})();
</script>
""", height=0)

prompt = st.chat_input("Enter a calculus problem...")

if prompt:
    track(st.session_state.session_id, "query", {"query": prompt[:300]})
    st.session_state.query_count += 1

    # Tier switch: after FREE_PREMIUM_QUERIES, move to DeepSeek
    if (
        st.session_state.query_count > FREE_PREMIUM_QUERIES
        and agent.model_tier == "premium"
    ):
        switched = agent.switch_to_deepseek()
        if switched:
            st.session_state.show_tier_notice = True

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            result = agent.process_query(prompt)
        st.markdown(result["output"])

    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
