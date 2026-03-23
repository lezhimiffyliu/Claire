"""
Claire - Making Calculus Clear
Calculus Cram: Exam prep powered by AI
"""

import streamlit as st
import time
import re
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
from quota import (
    can_use_premium, record_query, get_quota_status,
    inject_localstorage_sync, ANON_FREE_QUERIES, USER_FREE_PREMIUM,
)
from exam_mode import (
    ExamSession, ExamQuestion, ExamResult,
    generate_exam_from_bank, get_fallback_exam, score_exam,
    get_exam_topics, get_topic_label, format_time,
)

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
# THINKING ANIMATION + STRUCTURED OUTPUT
# ────────────────────────────────────────────────────────────

THINKING_MESSAGES = [
    "🤔 Analyzing problem...",
    "📐 Identifying problem type...",
    "🔍 Checking key conditions...",
    "✏️ Generating solution steps...",
]


def render_with_hidden_solution(content: str, msg_idx: int) -> None:
    """
    Render Claire's response with [Solution] hidden behind a button.
    Parses the structured output format and creates an expander for the solution.
    """
    # Try multiple patterns for solution section
    # Matches: **[Solution]**, [Solution], **Solution**, ## Solution, ### Solution
    solution_patterns = [
        r'---\s*\n\s*\*\*\[Solution\]\*\*\s*([\s\S]*)',  # ---\n**[Solution]**
        r'\*\*\[Solution\]\*\*\s*([\s\S]*)',              # **[Solution]**
        r'\[Solution\]\s*([\s\S]*)',                      # [Solution]
        r'---\s*\n\s*\*\*Solution\*\*\s*([\s\S]*)',       # ---\n**Solution**
        r'\*\*Solution:?\*\*\s*([\s\S]*)',                # **Solution** or **Solution:**
        r'#{2,3}\s*Solution\s*([\s\S]*)',                 # ## Solution or ### Solution
    ]

    match = None
    for pattern in solution_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            break

    if match:
        # Split content into main part and solution
        solution_content = match.group(1).strip()
        main_content = content[:match.start()].strip()

        # Remove trailing --- from main content if present
        main_content = re.sub(r'\n---\s*$', '', main_content).strip()

        # Render main content (problem type, key idea, steps, try it)
        st.markdown(main_content)

        # Render solution behind expander
        with st.expander("👁️ Show Solution", expanded=False):
            st.markdown(solution_content)
    else:
        # No structured format - just render as is
        st.markdown(content)


# ────────────────────────────────────────────────────────────
# EXAM SIMULATION MODE
# ────────────────────────────────────────────────────────────

def _start_exam_simulation():
    """Start an exam simulation from uploaded materials or fallback."""
    bank = st.session_state.exam_context.question_bank if st.session_state.exam_context.has_questions() else None
    questions = generate_exam_from_bank(bank, num_questions=5)

    st.session_state.exam_session = ExamSession(
        exam_id=st.session_state.session_id,
        questions=questions,
        current_index=0,
        answers=[""] * len(questions),
        time_limit_minutes=45,
    )
    st.session_state.exam_stage = "in_progress"
    st.session_state.exam_start_time = time.time()
    st.session_state.exam_current_q = 0
    st.session_state.exam_answers = [""] * len(questions)
    st.session_state.exam_result = None


def _finish_exam():
    """Complete the exam and calculate results."""
    session = st.session_state.exam_session
    session.answers = st.session_state.exam_answers
    session.is_complete = True

    # Calculate time taken
    elapsed = int(time.time() - st.session_state.exam_start_time)

    result = score_exam(session)
    result.time_taken_seconds = elapsed

    st.session_state.exam_result = result
    st.session_state.exam_stage = "complete"


def _render_exam_entry() -> bool:
    """
    Render the exam simulation entry page.
    Returns True if rendered (caller should skip other UI).
    """
    st.markdown("## 📝 Exam Simulation")
    st.caption("Experience a real exam — timed, no hints, no answers until you finish.")

    # Get topics from materials or fallback
    bank = st.session_state.exam_context.question_bank if st.session_state.exam_context.has_questions() else None
    if bank:
        questions = generate_exam_from_bank(bank, num_questions=5)
        source = "from your uploaded materials"
    else:
        questions = get_fallback_exam()
        source = "Practice Exam"

    topics = get_exam_topics(questions)

    st.markdown("---")
    st.markdown("**Topics covered:**")
    for topic in topics[:5]:
        st.markdown(f"• {topic}")

    st.markdown("")
    st.markdown(f"**Questions:** {len(questions)}")
    st.markdown(f"**Time:** ~{len(questions) * 9} minutes")
    st.caption(f"*{source}*")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Exam", type="primary", use_container_width=True):
            _start_exam_simulation()
            st.rerun()
    with col2:
        if st.button("← Back to Practice", use_container_width=True):
            st.session_state.exam_stage = "not_started"
            st.rerun()

    st.markdown("")
    st.info(
        "⚠️ **Exam rules:**\n"
        "- One question at a time\n"
        "- No hints or answers during exam\n"
        "- Can't go back to previous questions\n"
        "- Timer runs throughout",
        icon=None,
    )

    return True


def _render_exam_in_progress() -> bool:
    """
    Render the exam in progress.
    Returns True if rendered.
    """
    session = st.session_state.exam_session
    if not session:
        st.session_state.exam_stage = "not_started"
        return False

    questions = session.questions
    current_idx = st.session_state.exam_current_q
    total = len(questions)

    # Timer
    elapsed = int(time.time() - st.session_state.exam_start_time)
    time_str = format_time(elapsed)

    # Header with timer
    col_progress, col_timer = st.columns([3, 1])
    with col_progress:
        st.markdown(f"### Question {current_idx + 1} of {total}")
        st.progress((current_idx) / total)
    with col_timer:
        st.markdown(f"### ⏱️ {time_str}")

    st.markdown("---")

    # Current question
    q = questions[current_idx]
    st.markdown(f"**{q.source}** · {get_topic_label(q.topic)}")

    # Question text
    st.markdown(q.text)

    st.markdown("---")

    # Answer input
    current_answer = st.session_state.exam_answers[current_idx]
    answer = st.text_area(
        "Your answer:",
        value=current_answer,
        height=200,
        key=f"exam_answer_{current_idx}",
        placeholder="Show your work and final answer...",
    )
    st.session_state.exam_answers[current_idx] = answer

    st.markdown("")

    # Navigation
    is_last = current_idx == total - 1

    if is_last:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", use_container_width=True, disabled=(current_idx == 0)):
                st.session_state.exam_current_q = current_idx - 1
                st.rerun()
        with col2:
            if st.button("✅ Finish Exam", type="primary", use_container_width=True):
                _finish_exam()
                st.rerun()
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if current_idx > 0:
                if st.button("← Previous", use_container_width=True):
                    st.session_state.exam_current_q = current_idx - 1
                    st.rerun()
        with col3:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.exam_current_q = current_idx + 1
                st.rerun()

    return True


def _render_exam_results() -> bool:
    """
    Render exam results with paywall for detailed analysis.
    Returns True if rendered.
    """
    result = st.session_state.exam_result
    session = st.session_state.exam_session
    if not result or not session:
        st.session_state.exam_stage = "not_started"
        return False

    st.markdown("## 📊 Exam Results")

    # Score display
    percentage = int(result.total_score / result.max_score * 100) if result.max_score > 0 else 0
    time_str = format_time(result.time_taken_seconds)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{result.total_score}/{result.max_score}")
    with col2:
        st.metric("Percentage", f"{percentage}%")
    with col3:
        st.metric("Time", time_str)

    st.markdown("---")

    # Predicted score
    st.markdown("### 🎯 Predicted Exam Score")
    st.markdown(f"## {result.predicted_low} – {result.predicted_high}")
    st.caption("Based on your simulation performance")

    st.markdown("---")

    # Weak/Strong areas
    col_weak, col_strong = st.columns(2)
    with col_weak:
        st.markdown("### ❌ Weak Areas")
        if result.weak_topics:
            for topic in result.weak_topics:
                st.markdown(f"• {get_topic_label(topic)}")
        else:
            st.markdown("*None identified*")

    with col_strong:
        st.markdown("### ✅ Strong Areas")
        if result.strong_topics:
            for topic in result.strong_topics:
                st.markdown(f"• {get_topic_label(topic)}")
        else:
            st.markdown("*Keep practicing*")

    st.markdown("---")

    # Paywall for detailed analysis
    current_user = get_user()
    if not current_user:
        st.markdown("### 🔒 Unlock Full Analysis")
        st.markdown(
            "Sign in to see:\n"
            "- Step-by-step solutions for each question\n"
            "- Detailed weakness breakdown\n"
            "- Personalized improvement roadmap"
        )
        show_login_button("Sign in to unlock")
    else:
        # Show detailed breakdown for logged-in users
        with st.expander("📝 Review Your Answers"):
            for i, q in enumerate(session.questions):
                score = result.question_scores[i]
                answer = st.session_state.exam_answers[i] if i < len(st.session_state.exam_answers) else ""
                icon = "✅" if score == 20 else "⚠️" if score == 10 else "❌"

                st.markdown(f"**Q{i+1}** {icon} — {q.source}")
                st.caption(q.text[:150] + "..." if len(q.text) > 150 else q.text)
                st.text_area(
                    f"Your answer (Q{i+1})",
                    value=answer,
                    height=100,
                    disabled=True,
                    key=f"review_answer_{i}",
                )
                st.divider()

    st.markdown("---")

    # Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Take Another Exam", use_container_width=True):
            st.session_state.exam_stage = "not_started"
            st.session_state.exam_session = None
            st.session_state.exam_result = None
            st.rerun()
    with col2:
        if st.button("💬 Practice with Claire", type="primary", use_container_width=True):
            # Reset to chat mode with context about weak areas
            st.session_state.exam_stage = "not_started"
            if result.weak_topics:
                weak_msg = f"I just finished an exam simulation. My weak areas are: {', '.join(get_topic_label(t) for t in result.weak_topics)}. Can you help me practice?"
                st.session_state.messages.append({"role": "user", "content": weak_msg})
            st.rerun()

    return True


def _render_exam_mode() -> bool:
    """
    Main exam mode router.
    Returns True if exam mode is active and rendered.
    """
    stage = st.session_state.exam_stage

    if stage == "entry":
        return _render_exam_entry()
    elif stage == "in_progress":
        return _render_exam_in_progress()
    elif stage == "complete":
        return _render_exam_results()

    return False


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
if "anon_query_count" not in st.session_state:
    st.session_state.anon_query_count = 0
if "show_login_prompt" not in st.session_state:
    st.session_state.show_login_prompt = False

# Exam simulation state
# "not_started" → "in_progress" → "complete"
if "exam_stage" not in st.session_state:
    st.session_state.exam_stage = "not_started"
if "exam_session" not in st.session_state:
    st.session_state.exam_session = None
if "exam_start_time" not in st.session_state:
    st.session_state.exam_start_time = 0
if "exam_answers" not in st.session_state:
    st.session_state.exam_answers = []
if "exam_current_q" not in st.session_state:
    st.session_state.exam_current_q = 0
if "exam_result" not in st.session_state:
    st.session_state.exam_result = None

# Inject localStorage sync for anonymous quota tracking
inject_localstorage_sync()

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

    # Show diagnostic status (without exposing the internal level)
    if st.session_state.placement_result or st.session_state.placement_stage == "skipped":
        if st.session_state.placement_result:
            result = st.session_state.placement_result
            st.caption("Diagnostic")
            st.markdown(f"✓ {result.score}/{result.total}")
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

    # Check quota and switch model if needed
    used_premium = can_use_premium()
    if not used_premium and agent.model_tier == "premium":
        switched = agent.switch_to_deepseek()
        if switched:
            st.session_state.show_tier_notice = True

    st.session_state.messages.append({"role": "user", "content": "↻ Generate a similar problem"})
    with st.spinner(""):
        result = agent.process_query(similar_query)
    record_query(used_premium=used_premium)
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

        st.markdown("---")

        # Question body with math rendering
        if q.question_excerpt:
            # From uploaded materials: render with st.markdown so LaTeX ($...$) works
            from question_bank import format_math_text
            formatted_q = format_math_text(q.question_excerpt)
            st.markdown(formatted_q)
            if q.ask_text:
                st.markdown(f"*{q.ask_text}*")
        else:
            # Fallback / hand-written questions: already have LaTeX
            st.markdown(q.prompt)

        # Source citation below question
        diff_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        diff_icon = diff_colors.get(q.difficulty, "")
        st.caption(f"{diff_icon} {q.difficulty.capitalize()}  ·  *{q.source}*")

        st.markdown("")

        # Choices as lettered radio options
        LETTERS = ["A", "B", "C", "D", "E"]
        # Only apply format_math_text to plain text (from PDFs), not to fallback questions with existing LaTeX
        if q.question_excerpt:
            from question_bank import format_math_text
            choice_labels = [f"**{LETTERS[i]}.**  {format_math_text(c)}" for i, c in enumerate(q.choices)]
        else:
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

        st.markdown("### Diagnostic Complete!")
        st.metric("Score", f"{result.score}/{result.total}")

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

# Check if exam simulation is active first
if st.session_state.exam_stage in ("entry", "in_progress", "complete"):
    _render_exam_mode()

# Header
elif st.session_state.exam_scope_stage == "showing":
    # Show exam scope analyzer (after upload, before placement test)
    _render_exam_scope_analyzer()

elif not st.session_state.messages:
    # Show placement test if not done yet
    placement_active = _render_placement_test()

    if not placement_active:
        st.markdown("## Claire")
        st.caption("Making Calculus Clear · Calculus Cram")

        st.markdown("---")

        # Show exam simulation option prominently
        has_materials = exam_context.has_questions()

        st.markdown("### 🎯 What do you want to do?")
        st.markdown("")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "📝 **Take Exam Simulation**\n\nTest yourself under real exam conditions",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.exam_stage = "entry"
                st.rerun()

        with col2:
            if st.button(
                "💬 **Practice with Claire**\n\nGet step-by-step guidance on problems",
                use_container_width=True,
            ):
                # Just continue to chat
                pass

        st.markdown("---")

        # Show problems from materials or examples
        if has_materials:
            st.markdown("#### Quick practice from your materials")
            bank = exam_context.question_bank
            for i, q in enumerate(bank.questions[:3]):
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
                "Find the critical points of f(x,y) = x² + y² - 4x",
                "Use Lagrange multipliers: max xy subject to x + 2y = 10",
                "Evaluate ∫∫ xy dA over the region bounded by y=x² and y=4",
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
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_with_hidden_solution(msg["content"], i)
            else:
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

    # Show login prompt for anonymous users who've hit their limit
    quota = get_quota_status()
    if not quota["is_logged_in"] and not quota["can_premium"]:
        st.info(
            "🔑 **Sign in to continue with the premium model.** "
            "You've used your 3 free queries. Sign in to get 5 premium queries per day!",
            icon=None,
        )
        show_login_button("Sign in to continue")
    elif agent.model_tier == "basic" and not quota["can_premium"]:
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

    # Check quota before making query
    used_premium = can_use_premium()
    if not used_premium and agent.model_tier == "premium":
        switched = agent.switch_to_deepseek()
        if switched:
            st.session_state.show_tier_notice = True

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Thinking animation - show rotating messages while waiting
        status_placeholder = st.empty()
        result = None

        import threading
        import queue

        result_queue = queue.Queue()

        def fetch_response():
            try:
                r = agent.process_query(prompt)
                result_queue.put(r)
            except Exception as e:
                result_queue.put({"output": f"Error: {e}", "intermediate_steps": []})

        thread = threading.Thread(target=fetch_response)
        thread.start()

        # Show rotating thinking messages while waiting
        msg_idx = 0
        while thread.is_alive():
            status_placeholder.markdown(f"*{THINKING_MESSAGES[msg_idx % len(THINKING_MESSAGES)]}*")
            time.sleep(0.5)
            msg_idx += 1

        # Get result from queue
        result = result_queue.get()
        status_placeholder.empty()

        # Record query for quota tracking
        record_query(used_premium=used_premium)

        # Render with hidden solution
        msg_count = len(st.session_state.messages)
        render_with_hidden_solution(result["output"], msg_count)

    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
