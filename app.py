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
from exam_parser import (
    parse_exam_file, parsed_exam_to_exam_questions, ParsedExam,
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


# render_with_hidden_solution REMOVED - now using structured JSON responses


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

    # Get topics from materials or fallback
    bank = st.session_state.exam_context.question_bank if st.session_state.exam_context.has_questions() else None
    has_materials = bank is not None

    if has_materials:
        questions = generate_exam_from_bank(bank, num_questions=5)
        # Show material source
        material_names = st.session_state.exam_context.material_names[:3]
        names_str = ", ".join(material_names)
        if len(st.session_state.exam_context.material_names) > 3:
            names_str += f" +{len(st.session_state.exam_context.material_names) - 3}"
        st.success(f"📂 Using: **{names_str}**")
    else:
        questions = get_fallback_exam()
        st.info("📂 Using practice questions — upload your past exams in the sidebar for a personalized simulation")

    topics = get_exam_topics(questions)

    st.markdown("---")

    col_info, col_topics = st.columns([1, 1.5])
    with col_info:
        st.markdown(f"**Questions:** {len(questions)}")
        st.markdown(f"**Time:** ~{len(questions) * 9} min")
    with col_topics:
        st.markdown("**Topics:**")
        st.caption(" · ".join(topics[:4]))

    st.markdown("---")

    # Main action
    if st.button("🚀 Start Exam", type="primary", use_container_width=True):
        _start_exam_simulation()
        st.rerun()

    st.caption(
        "⚠️ One question at a time · No hints · Timer runs throughout"
    )

    st.markdown("")
    if st.button("← Back", use_container_width=True):
        st.session_state.exam_stage = "not_started"
        st.rerun()

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

    if stage == "upload":
        return _render_exam_upload()
    elif stage == "parsing":
        return _render_exam_parsing()
    elif stage == "preview":
        return _render_exam_preview()
    elif stage == "entry":
        return _render_exam_entry()
    elif stage == "in_progress":
        return _render_exam_in_progress()
    elif stage == "complete":
        return _render_exam_results()

    return False


def _render_exam_upload() -> bool:
    """Render the upload past paper page."""
    st.markdown("## 📄 Upload Past Exam")
    st.caption("Upload a past exam PDF and we'll turn it into a practice simulation.")

    st.markdown("---")

    uploaded = st.file_uploader(
        "Upload past exam",
        type=["pdf", "txt"],
        key="exam_upload",
        help="PDF or text file of a past exam paper"
    )

    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Parse Exam", type="primary", use_container_width=True, disabled=not uploaded):
            if uploaded:
                # Store file info for parsing
                st.session_state._upload_filename = uploaded.name
                st.session_state._upload_bytes = uploaded.getvalue()
                st.session_state.exam_stage = "parsing"
                st.rerun()

    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.exam_stage = "not_started"
            st.rerun()

    st.markdown("---")
    st.info(
        "💡 **What happens:**\n"
        "1. We extract text from your PDF\n"
        "2. AI identifies individual questions\n"
        "3. You preview the parsed exam\n"
        "4. Start simulation!",
        icon=None,
    )

    # Or use materials already loaded
    if st.session_state.exam_context.has_questions():
        st.markdown("---")
        st.markdown("Or use your already loaded materials:")
        if st.button("📝 Start with loaded materials", use_container_width=True):
            st.session_state.exam_stage = "entry"
            st.rerun()

    return True


def _render_exam_parsing() -> bool:
    """Show parsing status and do the actual parsing."""
    st.markdown("## 🔄 Analyzing Exam...")

    filename = st.session_state.get("_upload_filename", "exam.pdf")
    file_bytes = st.session_state.get("_upload_bytes", b"")

    if not file_bytes:
        st.error("No file to parse")
        st.session_state.exam_stage = "upload"
        st.rerun()
        return True

    # Show progress
    status = st.empty()
    progress = st.progress(0)

    status.markdown("*📄 Extracting text from PDF...*")
    progress.progress(20)

    # Parse the exam
    status.markdown("*🤖 AI analyzing exam structure...*")
    progress.progress(50)

    parsed = parse_exam_file(filename, file_bytes)

    progress.progress(100)

    if parsed.parse_success and parsed.questions:
        status.markdown("*✅ Exam parsed successfully!*")
        st.session_state.parsed_exam = parsed
        st.session_state.parsed_exam_questions = parsed_exam_to_exam_questions(parsed)
        time.sleep(0.5)
        st.session_state.exam_stage = "preview"
        st.rerun()
    else:
        status.empty()
        progress.empty()
        st.error(f"❌ {parsed.error_message or 'Could not parse exam'}")
        st.markdown("Try uploading a clearer PDF or a text file.")
        if st.button("← Try Again", use_container_width=True):
            st.session_state.exam_stage = "upload"
            st.rerun()

    return True


def _render_exam_preview() -> bool:
    """Preview parsed exam before starting simulation."""
    parsed = st.session_state.parsed_exam
    questions = st.session_state.parsed_exam_questions

    if not parsed or not questions:
        st.session_state.exam_stage = "upload"
        st.rerun()
        return True

    st.markdown(f"## 📋 {parsed.meta.title}")
    st.caption("Preview your parsed exam before starting simulation")

    st.markdown("---")

    # Exam meta
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions", len(questions))
    with col2:
        st.metric("Total Points", parsed.meta.total_points)
    with col3:
        st.metric("Est. Time", f"{parsed.meta.estimated_duration_minutes} min")

    # Topics
    if parsed.meta.topics_overview:
        st.markdown("**Topics:**")
        st.markdown(" · ".join(parsed.meta.topics_overview[:5]))

    st.markdown("---")

    # Question preview
    st.markdown("### Questions Preview")
    for i, q in enumerate(questions[:5]):  # Show first 5
        with st.expander(f"**{q.id}** — {get_topic_label(q.topic)} ({q.points} pts)"):
            st.markdown(q.text[:500] + "..." if len(q.text) > 500 else q.text)

    if len(questions) > 5:
        st.caption(f"+ {len(questions) - 5} more questions")

    st.markdown("---")

    # Actions
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🚀 Start Exam Simulation", type="primary", use_container_width=True):
            _start_exam_from_parsed()
            st.rerun()
    with col2:
        if st.button("📄 Re-upload", use_container_width=True):
            st.session_state.exam_stage = "upload"
            st.rerun()
    with col3:
        if st.button("← Back", use_container_width=True):
            st.session_state.exam_stage = "not_started"
            st.rerun()

    return True


def _start_exam_from_parsed():
    """Start exam simulation from parsed exam questions."""
    questions = st.session_state.parsed_exam_questions

    if not questions:
        st.session_state.exam_stage = "upload"
        return

    # Limit to reasonable number
    exam_questions = questions[:10]

    st.session_state.exam_session = ExamSession(
        exam_id=st.session_state.session_id,
        questions=exam_questions,
        current_index=0,
        answers=[""] * len(exam_questions),
        time_limit_minutes=len(exam_questions) * 9,
    )
    st.session_state.exam_stage = "in_progress"
    st.session_state.exam_start_time = time.time()
    st.session_state.exam_current_q = 0
    st.session_state.exam_answers = [""] * len(exam_questions)
    st.session_state.exam_result = None


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
# ============================================================
# PRACTICE STATE (Step-by-step engine - system controlled)
# ============================================================
if "practice_state" not in st.session_state:
    st.session_state.practice_state = {
        "mode": "browse",       # browse | practice | solution
        "problem": None,        # Problem text
        "problem_obj": None,    # Original problem object for display
        "step_index": 0,
        "history": [],          # List of step strings
    }
# Feedback prompt state
if "feedback_prompt_shown" not in st.session_state:
    st.session_state.feedback_prompt_shown = False
if "feedback_clicked" not in st.session_state:
    st.session_state.feedback_clicked = False
if "user_interaction_count" not in st.session_state:
    st.session_state.user_interaction_count = 0
# Premium prompt state
if "premium_prompt_dismissed" not in st.session_state:
    st.session_state.premium_prompt_dismissed = False
if "premium_prompt_shown" not in st.session_state:
    st.session_state.premium_prompt_shown = False
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
# "not_started" → "parsing" → "preview" → "entry" → "in_progress" → "complete"
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
if "parsed_exam" not in st.session_state:
    st.session_state.parsed_exam = None
if "parsed_exam_questions" not in st.session_state:
    st.session_state.parsed_exam_questions = []

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
# STEP ENGINE (Minimal, Prompt-Driven)
# ============================================================
# System = scheduler (controls when, how much)
# LLM = policy (decides what)
# ============================================================

def llm_call(prompt: str, max_tokens: int = 400) -> str:
    """
    Direct single-turn LLM call. No agent, no tools.
    """
    from claire_agent import get_secret
    from langchain_core.messages import HumanMessage

    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = get_secret("DEEPSEEK_API_KEY")
        if api_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=api_key,
                base_url="https://api.deepseek.com",
                temperature=0,
                max_tokens=max_tokens,
            )
        else:
            return "Unable to connect to AI service."
    else:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0,
            max_tokens=max_tokens,
        )

    try:
        result = llm.invoke([HumanMessage(content=prompt)])
        return result.content
    except Exception as e:
        return f"Error: {str(e)}"


def direct_llm_call(prompt: str) -> dict:
    """Wrapper for compatibility."""
    return {"output": llm_call(prompt)}


def post_process(output: str) -> str:
    """
    Thin enforcement layer. Only cuts off obvious overruns.
    """
    stop_tokens = ["Final Answer", "Therefore", "Thus", "So the answer", "Hence"]

    for t in stop_tokens:
        if t in output:
            output = output.split(t)[0]
            break

    # Limit lines (prevent wall of text)
    lines = output.strip().split("\n")
    return "\n".join(lines[:6]).strip()


def build_step_prompt(problem: str, step_index: int, history: list) -> str:
    """
    The prompt IS the controller. LLM decides what, system decides when.
    """
    history_str = "\n".join(history) if history else "None"

    return f"""You are solving a calculus problem step by step.

Current step: {step_index + 1}

Problem:
{problem}

Previous steps:
{history_str}

Your task:
Produce ONLY the next step.

Rules:
- Do exactly ONE meaningful step
- Do NOT finish the problem
- Do NOT summarize
- Do NOT give final answer
- Keep it concise

Format:
Step {step_index + 1}: ...

Then STOP."""


# ============================================================
# STATE (Minimal - only what's needed)
# ============================================================

def start_practice(problem):
    """Initialize practice state."""
    problem_text = problem.text if hasattr(problem, 'text') else str(problem)
    st.session_state.practice_state = {
        "mode": "practice",
        "problem": problem_text,
        "problem_obj": problem,  # Keep original for display
        "step_index": 0,
        "history": [],  # List of step strings
    }


# ============================================================
# CORE FUNCTIONS (Single entry points)
# ============================================================

def next_step() -> str:
    """
    Generate next step. This is the ONLY entry point for step generation.
    """
    state = st.session_state.practice_state

    # Track user interaction
    st.session_state.user_interaction_count += 1

    # Build prompt
    prompt = build_step_prompt(
        state["problem"],
        state["step_index"],
        state["history"]
    )

    # LLM call
    raw = llm_call(prompt)

    # Post-process (thin enforcement)
    step = post_process(raw)

    # Update state
    state["step_index"] += 1
    state["history"].append(step)  # LLM already includes "Step X:" prefix

    return step


def get_hint(problem) -> str:
    """Get a hint. Does not affect step state."""
    problem_text = problem.text if hasattr(problem, 'text') else str(problem)

    prompt = f"""Give a short hint for this calculus problem.

Problem:
{problem_text}

Rules:
- 1-2 sentences
- Do NOT solve it"""

    return llm_call(prompt)


def get_solution(problem) -> str:
    """Get full solution. Bypasses step engine."""
    problem_text = problem.text if hasattr(problem, 'text') else str(problem)

    prompt = f"""Solve this problem completely with all steps.

Problem:
{problem_text}"""

    return llm_call(prompt, max_tokens=1500)


# ============================================================
# FEEDBACK PROMPT (Lightweight, non-intrusive)
# ============================================================

FEEDBACK_FORM_URL = "https://forms.gle/YOUR_FORM_ID_HERE"  # Replace with actual URL

def maybe_show_feedback_prompt():
    """
    Show feedback prompt if:
    - User has engaged (diagnostic done OR 1+ practice interactions)
    - Prompt hasn't been shown yet this session
    - User hasn't already clicked
    """
    # Check if already shown or clicked
    if st.session_state.feedback_prompt_shown or st.session_state.feedback_clicked:
        return

    # Check if user has engaged enough
    diagnostic_done = st.session_state.placement_stage in ("done", "completed", "skipped")
    has_practiced = st.session_state.user_interaction_count >= 1

    if not (diagnostic_done or has_practiced):
        return

    # Mark as shown
    st.session_state.feedback_prompt_shown = True

    # Render subtle prompt
    st.markdown("")
    st.markdown(
        "<div style='background: #f8f9fa; padding: 12px 16px; border-radius: 8px; "
        "border-left: 3px solid #10b981; margin: 8px 0;'>"
        "<span style='font-size: 14px; color: #374151;'>"
        "☕ <b>Want a free coffee for feedback?</b> Takes 2 min"
        "</span></div>",
        unsafe_allow_html=True
    )
    if st.button("Give feedback →", key="feedback_btn"):
        st.session_state.feedback_clicked = True
        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={FEEDBACK_FORM_URL}">',
            unsafe_allow_html=True
        )
        st.success("Thanks! Opening feedback form...")


def maybe_show_premium_prompt():
    """
    Show premium prompt if:
    - User has engaged (diagnostic done OR 2+ interactions)
    - Not dismissed this session
    """
    # Check if dismissed
    if st.session_state.premium_prompt_dismissed:
        return

    # Check if already showing (avoid double render)
    if st.session_state.premium_prompt_shown:
        return

    # Check engagement
    diagnostic_done = st.session_state.placement_stage in ("done", "completed", "skipped")
    has_practiced = st.session_state.user_interaction_count >= 2

    if not (diagnostic_done or has_practiced):
        return

    # Mark as shown
    st.session_state.premium_prompt_shown = True

    # Render premium prompt
    st.markdown("")
    st.markdown(
        "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
        "padding: 20px; border-radius: 12px; color: white; margin: 16px 0;'>"
        "<div style='font-size: 16px; font-weight: 600; margin-bottom: 8px;'>✨ Premium Features</div>"
        "<div style='font-size: 14px; opacity: 0.95; margin-bottom: 6px;'>"
        "Unlock better step-by-step guidance and stronger models.</div>"
        "<div style='font-size: 12px; opacity: 0.8;'>Free for early users during testing.</div>"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Explore premium", key="premium_explore_btn", type="primary", use_container_width=True):
            st.success("🎉 You're already using premium features for free as an early tester! Enjoy!")
    with col2:
        if st.button("Not now", key="premium_dismiss_btn", use_container_width=True):
            st.session_state.premium_prompt_dismissed = True
            st.rerun()


# ============================================================
# PRACTICE VIEW (UI) - Human-guided experience
# ============================================================
def render_practice_view():
    """Render the step-by-step practice view with narrative flow."""
    state = st.session_state.practice_state
    problem_obj = state.get("problem_obj")

    if state["problem"] is None:
        st.warning("No problem selected")
        state["mode"] = "browse"
        return

    # ── Status Bar (shows where you are in the journey) ──────
    step_num = state["step_index"]

    # Get context from problem if available
    topic = ""
    if problem_obj:
        cats = getattr(problem_obj, 'categories', [])
        if cats:
            topic = cats[0].replace("_", " ").title()

    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        st.caption("🧠 **Practice Mode**")
    with col_status2:
        if step_num == 0:
            st.caption("📍 **Ready to start**")
        else:
            st.caption(f"📍 **Step {step_num}**")
    with col_status3:
        if topic:
            st.caption(f"🎯 **{topic}**")
        else:
            st.caption("🎯 **Calculus**")

    # Context hint (connects to larger flow)
    exam_summary = st.session_state.get("exam_summary")
    if exam_summary and topic:
        from exam_panic import get_display_name
        for t, count in exam_summary.top_topics[:3]:
            if topic.lower() in get_display_name(t).lower():
                st.info(f"📊 This is a **high-frequency exam topic** — appeared in {count} problems from your materials.")
                break

    st.markdown("---")

    # Back button (subtle, top right feel)
    if st.button("← Back to problems", type="secondary"):
        st.session_state.practice_state = {
            "mode": "browse",
            "problem": None,
            "problem_obj": None,
            "step_index": 0,
            "history": [],
        }
        st.rerun()

    # Problem display
    st.markdown("### 📝 Here's your problem:")
    if problem_obj and hasattr(problem_obj, 'get_formatted_text'):
        st.markdown(problem_obj.get_formatted_text())
    else:
        st.markdown(state["problem"])

    st.markdown("---")

    # ── Step-by-step section ─────────────────────────────────
    if state["history"]:
        st.markdown("### Let's solve this step by step.")
        st.markdown("")
        for i, step_text in enumerate(state["history"]):
            st.markdown(f"**{step_text}**")
            if i < len(state["history"]) - 1:
                st.markdown("")  # spacing between steps
        st.markdown("---")
    else:
        # No steps yet - gentle prompt
        st.markdown("*Ready when you are. Click below to see the first step, or try it yourself first.*")
        st.markdown("")

    # ── Control buttons (human language) ─────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        # Dynamic button text based on state
        if step_num == 0:
            btn_text = "🚀 Show me how to start"
        else:
            btn_text = "👉 Continue"

        if st.button(btn_text, type="primary", use_container_width=True):
            with st.spinner("Let me think..."):
                next_step()
            st.rerun()

    with col2:
        if st.button("💡 Give me a hint", use_container_width=True):
            with st.spinner("..."):
                hint = get_hint(problem_obj or state["problem"])
            st.session_state._last_hint = hint
            st.rerun()

    with col3:
        if st.button("📝 Show full solution", use_container_width=True):
            with st.spinner("Generating..."):
                solution = get_solution(problem_obj or state["problem"])
            state["mode"] = "solution"
            st.session_state._full_solution = solution
            st.rerun()

    # Show hint if requested
    if hasattr(st.session_state, '_last_hint') and st.session_state._last_hint:
        st.info(f"💡 {st.session_state._last_hint}")

    # Show full solution if in solution mode
    if state["mode"] == "solution" and hasattr(st.session_state, '_full_solution'):
        st.markdown("### Here's the complete solution:")
        st.markdown(st.session_state._full_solution)

        # After solution, offer next action
        st.markdown("---")
        if st.button("✨ Try a similar problem", use_container_width=True):
            st.session_state.pending_similar = True
            st.rerun()

    # Show prompts (if eligible)
    maybe_show_premium_prompt()
    maybe_show_feedback_prompt()


agent = st.session_state.agent
exam_context = st.session_state.exam_context


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Claire")
    st.caption("Personalized calculus exam prep. Focus on what matters.")

    st.divider()

    # Course materials
    st.caption("📂 Course Materials")
    current_user = get_user()
    if current_user:
        st.caption(f"👤 {current_user.email}")
        if st.button("Sign out", use_container_width=True, key="signout"):
            sign_out()
            st.rerun()

    # Always show file uploader
    uploaded = st.file_uploader(
        "Upload past exams or problem sets",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        key="material_uploader"
    )

    # Show sign-in option if not logged in
    if not current_user:
        show_login_button("Sign in with Google")

    if uploaded:
        if st.button("Load", use_container_width=True):
            files = [(f.name, f.getvalue()) for f in uploaded]

            # Quick regex parse only - NO LLM wait
            context = analyze_files(files)
            st.session_state.exam_context = context
            agent.set_exam_context(context)

            # Start background tasks (user doesn't wait)
            import threading

            # Task 1: Prepare 5 diagnostic questions (store in context object)
            def _prepare_diagnostic_bg():
                try:
                    if context.has_questions():
                        bank = context.question_bank
                        qs = build_questions_from_bank(bank, limit=5)
                        if qs:
                            qs = reconstruct_math_problems(qs)
                            context._prepared_diagnostic = qs  # Store in context, not session_state
                            print(f"[BG] Prepared {len(qs)} diagnostic questions")
                except Exception as e:
                    print(f"[BG] Error preparing diagnostic: {e}")

            # Task 2: Clean rest of question bank
            def _clean_rest_bg():
                from exam_context import start_background_cleaning
                start_background_cleaning(context)

            threading.Thread(target=_prepare_diagnostic_bg, daemon=True).start()
            threading.Thread(target=_clean_rest_bg, daemon=True).start()

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

                    # Problem header with practice button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{source_label}**")
                    with col2:
                        if st.button("Go", key=f"practice_{i}", use_container_width=True):
                            start_practice(q)
                            st.rerun()

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
        result = direct_llm_call(similar_query)
    record_query(used_premium=used_premium)
    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
    st.rerun()


# ============================================================
# PLACEMENT TEST HELPERS
# ============================================================

def reconstruct_math_problems(questions: list) -> list:
    """
    Reconstruct math problems from garbled PDF text.
    Uses LLM to rewrite (not fix) the math expressions.
    Only for diagnostic questions (5 max).
    """
    from claire_agent import get_secret
    import json

    if not questions:
        return questions

    print(f"[RECONSTRUCT] Processing {len(questions)} questions")

    try:
        api_key = get_secret("DEEPSEEK_API_KEY")
        if not api_key:
            print("[RECONSTRUCT] No DEEPSEEK_API_KEY, skipping")
            return questions

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0,
            max_tokens=2000,
        )

        # Build input array
        raw_list = [q.prompt for q in questions]
        raw_json = json.dumps(raw_list, ensure_ascii=False)

        prompt = f"""Rewrite these garbled calculus problems as proper LaTeX.

Input: {raw_json}

Rules:
- Output JSON array, same order, same length
- Use $...$ for inline math
- Fix integral bounds, dx/dy order, sqrt, powers
- Remove junk (page numbers, course headers)
- If unclear, output best guess (never empty)

Output ONLY the JSON array, no explanation:
["$\\int_0^1 ...$", "$...$", ...]"""

        result = llm.invoke([HumanMessage(content=prompt)])
        output = result.content.strip()

        # Extract JSON array from response
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
        output = output.strip()

        reconstructed = json.loads(output)
        print(f"[RECONSTRUCT] Got {len(reconstructed)} results")

        for i, (q, text) in enumerate(zip(questions, reconstructed)):
            if text:
                # Normalize backslashes
                fixed = text
                while '\\\\' in fixed:
                    fixed = fixed.replace('\\\\', '\\')
                q.prompt = fixed
                print(f"[RECONSTRUCT] [{i+1}] {fixed[:50]}...")

    except Exception as e:
        print(f"[RECONSTRUCT] Error: {e}")
        import traceback
        traceback.print_exc()

    return questions


def _start_placement_from_materials():
    """Start placement test using questions from uploaded materials."""
    print("[START] _start_placement_from_materials called")

    context = st.session_state.exam_context
    questions = None

    # Check if pre-prepared questions are ready (from upload background thread)
    if hasattr(context, '_prepared_diagnostic') and context._prepared_diagnostic:
        questions = context._prepared_diagnostic
        print(f"[START] Using {len(questions)} pre-prepared questions")
    else:
        # Fallback: prepare now (shouldn't happen often)
        print("[START] Pre-prepared not ready, preparing now...")
        bank = context.question_bank if context.has_questions() else None
        questions = build_questions_from_bank(bank, limit=5)
        if questions:
            questions = reconstruct_math_problems(questions)

    # Fallback if still no questions
    if not questions:
        track = st.session_state.calc_track or "calc_i"
        questions = get_fallback_questions(track)
        print(f"[START] Using {len(questions)} fallback questions")

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
    Render the Exam Panic Mode analysis after file upload.
    Shows topic distribution, focus advice, and cram plan.
    Returns True if it rendered (caller should skip other UI).
    """
    if st.session_state.exam_scope_stage != "showing":
        return False

    from exam_panic import generate_exam_summary, get_display_name

    ctx = st.session_state.exam_context
    if not ctx.has_context():
        st.session_state.exam_scope_stage = "done"
        return False

    # Get questions from bank
    questions = []
    if ctx.question_bank:
        questions = ctx.question_bank.questions

    if not questions:
        st.info("📂 Materials loaded — couldn't extract problems. Try uploading a past exam for better analysis.")
        if st.button("Continue →", type="primary"):
            st.session_state.exam_scope_stage = "done"
            st.rerun()
        return True

    # Generate exam summary (only once, then cache)
    if "exam_summary" not in st.session_state or st.session_state.exam_summary is None:
        with st.spinner("Analyzing your materials..."):
            summary = generate_exam_summary(questions, days=3)
            st.session_state.exam_summary = summary
    else:
        summary = st.session_state.exam_summary

    # ── Header ──────────────────────────────────────────────
    st.markdown("## 📊 Exam Analysis")
    names_str = ", ".join(ctx.material_names[:3])
    if len(ctx.material_names) > 3:
        names_str += f" +{len(ctx.material_names) - 3} more"
    st.caption(f"Based on: {names_str}")
    st.caption(f"📝 {summary.total_questions} problems analyzed")
    st.markdown("---")

    if not summary.top_topics:
        st.info("Couldn't detect specific topics. Try uploading more materials.")
        if st.button("Continue →", type="primary"):
            st.session_state.exam_scope_stage = "done"
            st.rerun()
        return True

    # ── Top Topics ───────────────────────────────────────────
    st.markdown("### 🎯 This course heavily focuses on:")
    st.markdown("")

    for i, (topic, count) in enumerate(summary.top_topics[:5], 1):
        name = get_display_name(topic)
        st.markdown(f"**{i}. {name}** — appears in {count} problems")

    st.markdown("---")

    # ── Two-column: Focus Advice + Cram Plan ─────────────────
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown("### 📝 What you should know:")
        st.markdown("")

        for advice in summary.focus_advice[:4]:
            with st.expander(f"**{advice['display_name']}** ({advice['count']} problems)"):
                for step in advice["steps"]:
                    st.markdown(f"• {step}")

    with col_right:
        st.markdown("### 📅 Cram Plan")
        st.markdown("")

        for day in summary.cram_plan:
            topics_str = ", ".join(day["display_names"])
            st.markdown(f"**Day {day['day']}**")
            st.caption(topics_str)

    st.markdown("---")

    # ── CTA buttons ─────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🎯 Start Diagnostic", type="primary", use_container_width=True):
            st.session_state.exam_scope_stage = "done"
            _start_placement_from_materials()
            st.rerun()
        st.caption("Recommended · 5 min · Personalized learning")
    with col_b:
        if st.button("Skip for now", use_container_width=True):
            st.session_state.exam_scope_stage = "done"
            st.session_state.placement_stage = "skipped"
            st.rerun()

    return True


def _render_placement_test():
    """Render the placement test UI."""
    stage = st.session_state.placement_stage

    # ---- NOT STARTED: prompt to take the test ----
    if stage == "not_started":
        st.markdown("## Quick Diagnostic")
        st.caption("5 questions · ~5 min")
        st.markdown("---")

        st.markdown(
            "Let me figure out where you're at so I can teach you more effectively. "
            "You'll get personalized practice focused on your weak areas."
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

        # Source citation FIRST (above question)
        diff_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        diff_icon = diff_colors.get(q.difficulty, "")
        st.caption(f"{diff_icon} {q.difficulty.capitalize()}  ·  {q.source}")

        st.markdown("")

        # Question body - use prompt (already formatted) over raw excerpt
        st.markdown(q.prompt)

        st.markdown("")
        st.markdown("---")
        st.markdown("")

        # Choices - each on its own line with clear formatting
        LETTERS = ["A", "B", "C", "D", "E"]
        st.markdown("**Choose your answer:**")
        st.markdown("")

        # Build choices
        formatted_choices = q.choices

        # Use radio with cleaner labels
        choice_labels = [f"{LETTERS[i]}.  {formatted_choices[i]}" for i in range(len(q.choices))]

        answer = st.radio(
            "Select one:",
            options=list(range(len(q.choices))),
            format_func=lambda i: choice_labels[i],
            index=None,
            key=f"placement_q_{idx}",
            label_visibility="collapsed",
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

        # Show prompts after diagnostic
        maybe_show_premium_prompt()
        maybe_show_feedback_prompt()

        return True

    return False  # "skipped" or "completed" — don't render placement UI


# ============================================================
# MAIN AREA
# ============================================================

# Get practice state
ps = st.session_state.practice_state

# Check practice mode FIRST (highest priority)
if ps["mode"] == "practice":
    render_practice_view()

# Check if exam simulation is active
elif st.session_state.exam_stage in ("upload", "parsing", "preview", "entry", "in_progress", "complete"):
    _render_exam_mode()

# Exam scope analyzer (after upload)
elif st.session_state.exam_scope_stage == "showing":
    _render_exam_scope_analyzer()

# Placement test (only if in_progress or done - NOT on first load)
elif st.session_state.placement_stage in ("in_progress", "done"):
    _render_placement_test()

elif ps["mode"] == "browse":
    # ============================================================
    # BROWSE MODE - Entry to the practice journey
    # ============================================================
    st.markdown("## Claire")
    st.caption("Your exam survival companion")

    has_materials = exam_context.has_questions()
    exam_summary = st.session_state.get("exam_summary")

    # ── Show journey context ─────────────────────────────────
    if has_materials and exam_summary:
        # User has materials - show personalized context
        st.markdown("---")
        from exam_panic import get_display_name
        top_topic = exam_summary.top_topics[0] if exam_summary.top_topics else None

        if top_topic:
            st.markdown(f"### 🎯 Your exam focuses heavily on **{get_display_name(top_topic[0])}**")
            st.caption(f"This topic appeared in {top_topic[1]} problems from your materials.")

        st.markdown("")
        st.success(f"📂 {exam_context.get_question_count()} problems loaded · Ready to practice")

    elif has_materials:
        # Materials but no analysis yet
        st.markdown("---")
        q_count = exam_context.get_question_count()
        st.success(f"📂 {q_count} problems loaded from your materials")

    else:
        # No materials - gentle nudge
        st.markdown("---")
        st.info("📂 **Tip:** Upload your past exams or problem sets in the sidebar for personalized practice")

    st.markdown("")

    # ⭐ PRIMARY ACTION
    if has_materials:
        if st.button("🚀 **Start targeted practice**", type="primary", use_container_width=True):
            # Start with first problem (ideally prioritized)
            prioritized = st.session_state.get("prioritized_questions", [])
            if prioritized:
                start_practice(prioritized[0])
            else:
                start_practice(exam_context.question_bank.questions[0])
            st.rerun()
    else:
        if st.button("🚀 **Try a practice problem**", type="primary", use_container_width=True):
            from dataclasses import dataclass
            @dataclass
            class SimpleProblem:
                text: str
                difficulty: str = "medium"
                categories: list = None
                def format_source(self): return "Example"
                def get_formatted_text(self): return self.text
            start_practice(SimpleProblem(
                text="Find the critical points of f(x,y) = x² + y² - 4x",
                categories=["critical_points"]
            ))
            st.rerun()

    st.markdown("---")

    # ── Problem list ─────────────────────────────────────────
    st.markdown("#### Or choose a specific problem:")
    if has_materials:
        bank = exam_context.question_bank
        prioritized = st.session_state.get("prioritized_questions", [])
        problems_to_show = prioritized[:5] if prioritized else bank.questions[:5]

        for i, q in enumerate(problems_to_show):
            source_label = q.format_source()
            text_preview = q.text[:50] + "..." if len(q.text) > 50 else q.text

            # Show why this problem matters
            cats = getattr(q, 'categories', [])
            diff = getattr(q, 'difficulty', 'medium')
            diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(diff, "")

            label = f"{diff_icon} {source_label}"
            if cats:
                label += f" · {cats[0].replace('_', ' ').title()}"

            if st.button(f"{label}\n{text_preview}", key=f"q_{i}", use_container_width=True):
                start_practice(q)
                st.rerun()
    else:
        examples = [
            ("critical_points", "🟡 Critical Points", "Find the critical points of f(x,y) = x² + y² - 4x"),
            ("lagrange_multipliers", "🔴 Lagrange Multipliers", "Use Lagrange multipliers: max xy subject to x + 2y = 10"),
            ("double_integrals", "🟡 Double Integrals", "Evaluate ∫∫ xy dA over the region bounded by y=x² and y=4"),
        ]
        from dataclasses import dataclass
        @dataclass
        class SimpleProblem:
            text: str
            difficulty: str = "medium"
            categories: list = None
            def format_source(self): return "Example"
            def get_formatted_text(self): return self.text

        for cat, label, text in examples:
            if st.button(f"{label}\n{text[:45]}...", key=f"ex_{cat}", use_container_width=True):
                start_practice(SimpleProblem(text=text, categories=[cat]))
                st.rerun()
# (No else block needed - all modes handled by practice_state)


# ============================================================
# NO FREE-FORM CHAT INPUT
# All interaction happens through practice mode
# ============================================================
