"""
Claire - Making Calculus Clear
UW Calculus Practice + Photo Grading
"""

import streamlit as st
from problem_loader import load_problems, get_all_parts, Problem, ProblemPart
from grader import parse_image, grade_solution, GradingResult
from quota import can_use_premium, record_query, get_quota_status, is_pro_user, clear_pro_cache
from student_profile import (
    StudentProfile, get_profile, save_profile, create_profile,
    update_profile_from_diagnostic, update_profile_from_grading,
    get_or_create_workspace, load_from_supabase, sync_profile_to_supabase,
    get_current_workspace_id, set_current_workspace_id
)
from attempt_tracker import record_handwritten_attempt
from recommender import recommend_next_problem, get_recommendation_reason
from auth import handle_oauth_callback, get_user, show_login_button, sign_out
from stripe_checkout import create_checkout_session, verify_checkout_session, get_customer_portal_url
from mobile_upload import (
    create_upload_session, get_session_status, get_signed_urls,
    close_session, get_session_by_id
)
from qr_generator import generate_qr_code, get_upload_url
from vision_analyzer import (
    analyze_handwritten_solution, analysis_to_grading_result, get_combined_feedback
)
from streamlit_autorefresh import st_autorefresh
import os
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page config
st.set_page_config(
    page_title="Claire",
    page_icon="📐",
    layout="centered"
)

# ============================================================
# AUTH & PAYMENT CALLBACKS (must be early)
# ============================================================

# Handle OAuth callback (?code=xxx)
if handle_oauth_callback():
    st.rerun()

# Handle Stripe payment callback (?upgraded=true&session_id=xxx)
if st.query_params.get("upgraded") == "true":
    session_id = st.query_params.get("session_id")
    if session_id:
        result = verify_checkout_session(session_id)
        if result["status"] == "complete":
            st.success("🎉 Welcome to Claire Pro! Your account has been upgraded.")
            clear_pro_cache()  # Force re-check pro status
        elif result["status"] == "pending":
            st.warning(result["message"])
        else:
            st.error(result["message"])
        # Clear query params
        st.query_params.clear()

# Custom CSS
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px; }
    .stButton button { font-weight: 500; }

    /* Error type badges */
    .error-concept { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 4px; }
    .error-algebra { background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 4px; }
    .error-logic { background: #cce5ff; color: #004085; padding: 2px 8px; border-radius: 4px; }
    .error-careless { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "course" not in st.session_state:
    st.session_state.course = None  # "124", "125", "126"

if "mode" not in st.session_state:
    st.session_state.mode = "select"  # "select", "diagnostic", "practice"

if "diagnostic_questions" not in st.session_state:
    st.session_state.diagnostic_questions = []  # Questions for current diagnostic

if "diagnostic_idx" not in st.session_state:
    st.session_state.diagnostic_idx = 0  # Current question index

if "diagnostic_answers" not in st.session_state:
    st.session_state.diagnostic_answers = {}  # {question_id: selected_index}

if "weak_topics" not in st.session_state:
    st.session_state.weak_topics = []  # Topics the user got wrong

if "strong_topics" not in st.session_state:
    st.session_state.strong_topics = []  # Topics the user got right

if "problems" not in st.session_state:
    st.session_state.problems = []  # List of Problem objects

if "parts_list" not in st.session_state:
    st.session_state.parts_list = []  # List of (Problem, part_index) tuples

if "current_part_idx" not in st.session_state:
    st.session_state.current_part_idx = 0

if "grading_result" not in st.session_state:
    st.session_state.grading_result = None

if "error_stats" not in st.session_state:
    st.session_state.error_stats = {
        "algebra": 0,
        "concept": 0,
        "logic": 0,
        "careless": 0,
        "correct": 0,
    }

if "show_solution" not in st.session_state:
    st.session_state.show_solution = False

if "seen_problem_indices" not in st.session_state:
    st.session_state.seen_problem_indices = set()  # Track problems seen this session

if "qr_upload_session" not in st.session_state:
    st.session_state.qr_upload_session = None  # Current QR upload session

if "qr_upload_token" not in st.session_state:
    st.session_state.qr_upload_token = None  # Raw token for QR code URL

if "workspace_id" not in st.session_state:
    st.session_state.workspace_id = None  # Current workspace ID for logged-in users

if "teaching_context" not in st.session_state:
    st.session_state.teaching_context = None  # Context for Socratic teaching after wrong answer

if "teaching_mode" not in st.session_state:
    st.session_state.teaching_mode = False  # True when in teaching dialogue

if "last_teaching_action" not in st.session_state:
    st.session_state.last_teaching_action = None  # Last action from teaching orchestrator


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def build_teaching_context(
    problem: Problem,
    analysis,  # SolutionAnalysis
    grading_result: GradingResult,
    part_index: int = 0,
):
    """
    Build teaching context from analysis results for Socratic teaching.

    Now returns TeachingContext object from teaching_orchestrator.

    Args:
        problem: The Problem object
        analysis: SolutionAnalysis from vision_analyzer
        grading_result: GradingResult for compatibility
        part_index: Which part to focus on

    Returns:
        TeachingContext object
    """
    from teaching_orchestrator import context_from_grading_result
    return context_from_grading_result(problem, grading_result, analysis, part_index)


def start_teaching_session(teaching_context) -> str:
    """
    Start a Socratic teaching session based on the teaching context.

    Now uses teaching_orchestrator for structured decision-making and rule enforcement.

    Args:
        teaching_context: TeachingContext object from teaching_orchestrator

    Returns:
        Initial teaching message from agent
    """
    from claire_agent import ClaireAgent
    from teaching_orchestrator import orchestrate_teaching_response

    # Get or create agent
    if "claire_agent" not in st.session_state:
        st.session_state.claire_agent = ClaireAgent()

    agent = st.session_state.claire_agent

    # Use orchestrator to get structured decision with rule enforcement
    decision = orchestrate_teaching_response(
        context=teaching_context,
        agent=agent,
        user_input="",
    )

    # Store the decision action for UI logic (e.g., auto-end session if confirmed correct)
    st.session_state.last_teaching_action = decision.action

    return decision.message


def load_diagnostic_bank():
    """Load diagnostic questions from JSON."""
    import json
    with open("diagnostic_bank.json", "r") as f:
        return json.load(f)


def get_diagnostic_questions(course: str, count: int = 8) -> list:
    """Get diagnostic questions for a course."""
    track_map = {"124": "calc_i", "125": "calc_ii", "126": "calc_iii"}
    track = track_map.get(course, "calc_i")

    bank = load_diagnostic_bank()
    questions = [q for q in bank["questions"] if q["track"] == track]

    # Sort by difficulty: easy first, then medium, then hard
    difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
    questions.sort(key=lambda q: difficulty_order.get(q["difficulty"], 1))

    # Take up to count questions
    selected = questions[:count]

    # Shuffle choices for each question so correct answer isn't always first
    for q in selected:
        correct_answer = q["choices"][q["correct_index"]]
        shuffled = q["choices"].copy()
        random.shuffle(shuffled)
        q["choices"] = shuffled
        q["correct_index"] = shuffled.index(correct_answer)

    return selected


def select_course(course: str):
    """Select a course and start diagnostic."""
    st.session_state.course = course
    st.session_state.mode = "diagnostic"
    st.session_state.diagnostic_questions = get_diagnostic_questions(course)
    st.session_state.diagnostic_idx = 0

    # For logged-in users: create/load workspace and profile from Supabase
    user = get_user()
    if user:
        workspace_id = get_or_create_workspace(str(user.id), course)
        if workspace_id:
            set_current_workspace_id(workspace_id)
            # Load existing profile from Supabase
            profile = load_from_supabase(workspace_id)
            if profile:
                save_profile(profile)
    st.session_state.diagnostic_answers = {}
    st.session_state.weak_topics = []

    # Create student profile (stored in session for anonymous users)
    create_profile(course)


def skip_diagnostic():
    """Skip diagnostic and go directly to practice."""
    st.session_state.weak_topics = []
    st.session_state.strong_topics = []
    start_practice(recommended=False)
    st.session_state.mode = "practice"


def finish_diagnostic():
    """Complete diagnostic and show results."""
    questions = st.session_state.diagnostic_questions
    answers = st.session_state.diagnostic_answers

    # Categorize topics
    weak = []
    strong = []
    correct_count = 0

    for q in questions:
        topic = q["topic"]
        user_answer = answers.get(q["id"])

        if user_answer is not None:
            if user_answer == q["correct_index"]:
                correct_count += 1
                if topic not in strong:
                    strong.append(topic)
            else:
                if topic not in weak:
                    weak.append(topic)
                # Remove from strong if previously added
                if topic in strong:
                    strong.remove(topic)

    # Topics that are strong but not weak
    st.session_state.strong_topics = [t for t in strong if t not in weak]
    st.session_state.weak_topics = weak

    # Update student profile
    score = correct_count / len(questions) if questions else 0.0
    update_profile_from_diagnostic(score, weak)

    st.session_state.mode = "diagnostic_result"


def start_practice(recommended: bool = True):
    """Load problems and start practice mode."""
    st.session_state.problems = load_problems(st.session_state.course)
    st.session_state.parts_list = get_all_parts(st.session_state.course)
    st.session_state.seen_problem_indices = set()  # Reset seen problems

    # If recommended, try to start with a weak topic problem
    if recommended and st.session_state.weak_topics:
        weak = st.session_state.weak_topics
        for i, (problem, _) in enumerate(st.session_state.parts_list):
            if problem.topic in weak:
                st.session_state.current_part_idx = i
                break
        else:
            st.session_state.current_part_idx = 0
    else:
        st.session_state.current_part_idx = 0

    st.session_state.grading_result = None
    st.session_state.show_solution = False
    st.session_state.mode = "practice"


def next_part():
    """Move to next problem using smart recommendation."""
    if st.session_state.parts_list:
        # Get current problem
        current_problem, _ = st.session_state.parts_list[st.session_state.current_part_idx]

        # Mark ALL parts of current problem as seen
        for i, (p, _) in enumerate(st.session_state.parts_list):
            if p.id == current_problem.id:
                st.session_state.seen_problem_indices.add(i)

        # Use recommender to pick next problem (it will skip seen parts)
        st.session_state.current_part_idx = recommend_next_problem(
            st.session_state.parts_list,
            st.session_state.current_part_idx,
            get_profile(),
            st.session_state.seen_problem_indices
        )
        st.session_state.grading_result = None
        st.session_state.show_solution = False


def get_current_part() -> tuple[Problem, ProblemPart, int] | None:
    """Get current (Problem, ProblemPart, part_index)."""
    if not st.session_state.parts_list:
        return None
    idx = st.session_state.current_part_idx
    if 0 <= idx < len(st.session_state.parts_list):
        problem, part_idx = st.session_state.parts_list[idx]
        return problem, problem.parts[part_idx], part_idx
    return None


def render_error_badge(error_type: str) -> str:
    """Render an error type badge."""
    labels = {
        "concept": "Concept Error",
        "algebra": "Algebra Mistake",
        "logic": "Logic Error",
        "careless": "Careless Slip",
    }
    return f'<span class="error-{error_type}">{labels.get(error_type, error_type)}</span>'


def render_qr_upload_section(problem: Problem):
    """Render QR code mobile upload section."""
    user = get_user()

    if not user:
        st.info("Sign in to use QR mobile upload.")
        show_login_button("Sign in with Google")
        return

    # Get app URL for QR code
    try:
        app_url = st.secrets.get("APP_URL")
    except Exception:
        app_url = None
    if not app_url:
        app_url = os.environ.get("APP_URL", "http://localhost:8501")

    # Check if we have an active session for this problem
    session = st.session_state.qr_upload_session
    token = st.session_state.qr_upload_token

    # Invalidate session if it's for a different problem
    if session and session.question_id != problem.id:
        session = None
        token = None
        st.session_state.qr_upload_session = None
        st.session_state.qr_upload_token = None

    # Generate QR code button
    if not session:
        st.markdown("Scan the QR code with your phone to upload photos of your handwritten work.")

        if st.button("Generate QR Code", type="primary", use_container_width=True):
            # Build problem display text
            display_parts = []
            if problem.stem:
                display_parts.append(problem.stem)
            for p in problem.parts:
                if p.label:
                    display_parts.append(f"({p.label}) {p.question_text}")
                else:
                    display_parts.append(p.question_text)
            display_text = "\n\n".join(display_parts)

            # Create session
            new_session, raw_token = create_upload_session(
                user_id=str(user.id),
                solve_session_id=f"solve_{problem.id}_{user.id}",
                question_id=problem.id,
                course=st.session_state.course or "unknown",
                display_text=display_text[:500],  # Truncate for mobile display
            )

            if new_session:
                st.session_state.qr_upload_session = new_session
                st.session_state.qr_upload_token = raw_token
                st.rerun()
            else:
                st.error("Failed to create upload session. Please try again.")
        return

    # Show QR code and status
    st.markdown("**Scan with your phone:**")

    # Generate and display QR code
    qr_bytes = generate_qr_code(token, app_url, size=250)
    st.image(qr_bytes, width=250)

    # Show upload URL for manual entry
    upload_url = get_upload_url(token, app_url)
    with st.expander("Can't scan? Copy link"):
        st.code(upload_url, language=None)

    st.markdown("---")

    # Poll for status
    status_data = get_session_status(session.id)
    status = status_data.get("status", "unknown")
    image_count = status_data.get("image_count", 0)
    images = status_data.get("images", [])

    # Auto-refresh every 3 seconds while waiting for uploads
    # Stop auto-refresh once images are received (so Analyze button works)
    if status in ["waiting", "paired", "receiving_images"] and not images:
        st_autorefresh(interval=3000, limit=100, key="qr_upload_autorefresh")

    # Status indicator
    if images:
        st.success(f"Received {image_count} photo(s)")
    elif status == "waiting":
        st.info("Waiting for phone to connect...")
    elif status == "paired":
        st.success("Phone connected! Waiting for photos...")
    elif status in ["closed", "expired"]:
        st.warning("Session ended. Generate a new QR code to continue.")
        if st.button("Generate New QR Code", use_container_width=True):
            st.session_state.qr_upload_session = None
            st.session_state.qr_upload_token = None
            st.rerun()
        return
    else:
        st.info(f"Session status: {status}")

    # Show image thumbnails if any
    if images:
        st.markdown("**Uploaded photos:**")
        signed_urls = get_signed_urls(session.id)
        if signed_urls:
            cols = st.columns(min(len(signed_urls), 3))
            for i, url in enumerate(signed_urls):
                with cols[i % 3]:
                    st.image(url, use_container_width=True)

        st.markdown("")

        # Analyze button
        if st.button("✅ Analyze Solution", type="primary", use_container_width=True):
            with st.spinner("Analyzing your handwritten work..."):
                # Check quota
                used_premium = can_use_premium()

                # Get signed URLs for vision analysis
                image_urls = get_signed_urls(session.id, expires_in=300)

                if not image_urls:
                    st.error("Could not retrieve uploaded images.")
                    return

                # Analyze with vision model
                analysis, error_msg = analyze_handwritten_solution(problem, image_urls)

                if not analysis:
                    st.error(error_msg or "Analysis failed. Please try again.")
                    return

                # Convert to GradingResult for display
                result = analysis_to_grading_result(analysis, part_index=0)

                # Record usage
                record_query(used_premium=used_premium)

                # Update stats
                if result.is_correct:
                    st.session_state.error_stats["correct"] += 1
                elif result.error_type:
                    st.session_state.error_stats[result.error_type] = (
                        st.session_state.error_stats.get(result.error_type, 0) + 1
                    )

                # Update student profile
                update_profile_from_grading(
                    topic=problem.topic,
                    correct=result.is_correct,
                    error_type=result.error_type if not result.is_correct else None
                )

                # For logged-in users: record attempt and sync profile to Supabase
                workspace_id = get_current_workspace_id()
                if workspace_id and user:
                    # Record attempt to database
                    record_handwritten_attempt(
                        user_id=str(user.id),
                        workspace_id=workspace_id,
                        question_id=problem.id,
                        analysis_result={
                            "parts": [
                                {
                                    "is_correct": p.is_correct,
                                    "error_type": p.error_type,
                                    "feedback": p.feedback,
                                    "hint": p.hint,
                                }
                                for p in analysis.parts
                            ],
                            "overall_summary": analysis.overall_summary,
                        },
                        upload_session_id=str(session.id),
                    )
                    # Sync profile to Supabase
                    sync_profile_to_supabase()

                # Close the upload session
                close_session(session.id)
                st.session_state.qr_upload_session = None
                st.session_state.qr_upload_token = None

                st.session_state.grading_result = result

                # Prepare teaching context (even if correct, for potential follow-up)
                teaching_ctx = build_teaching_context(problem, analysis, result, part_index=0)
                st.session_state.teaching_context = teaching_ctx

                # Only enter teaching mode if incorrect or uncertain
                if not result.is_correct or result.error_type:
                    st.session_state.teaching_mode = True
                else:
                    st.session_state.teaching_mode = False

                st.rerun()

    # Refresh button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            close_session(session.id)
            st.session_state.qr_upload_session = None
            st.session_state.qr_upload_token = None
            st.rerun()


# ============================================================
# COURSE SELECTION PAGE
# ============================================================

def render_course_selection():
    """Render the course selection page."""
    st.markdown("## Claire")
    st.markdown("### What are you studying?")
    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📘 UW Math 124\n(Calc I)", use_container_width=True):
            select_course("124")
            st.rerun()
        st.caption("Limits, Derivatives, Applications")

    with col2:
        if st.button("📗 UW Math 125\n(Calc II)", use_container_width=True):
            select_course("125")
            st.rerun()
        st.caption("Integration, Techniques, Series")

    with col3:
        if st.button("📙 UW Math 126\n(Calc III)", use_container_width=True):
            select_course("126")
            st.rerun()
        st.caption("Multivariable, Vectors, PDEs")

    st.markdown("---")
    st.markdown("*Problems from UW past exams. Upload your work for instant feedback.*")


# ============================================================
# DIAGNOSTIC PAGE
# ============================================================

def render_diagnostic():
    """Render the 5-minute diagnostic quiz."""
    questions = st.session_state.diagnostic_questions
    idx = st.session_state.diagnostic_idx
    total = len(questions)

    if not questions:
        st.warning("No diagnostic questions available.")
        finish_diagnostic()
        st.rerun()
        return

    # Header
    course_names = {"124": "Math 124", "125": "Math 125", "126": "Math 126"}
    course = st.session_state.course

    col_back, col_title, col_progress, col_skip = st.columns([1, 3, 1, 1])
    with col_back:
        if st.button("← Back"):
            st.session_state.course = None
            st.session_state.mode = "select"
            st.rerun()
    with col_title:
        st.markdown(f"### {course_names.get(course, 'Calculus')} Diagnostic")
    with col_progress:
        st.caption(f"{idx + 1}/{total}")
    with col_skip:
        if st.button("Skip →"):
            skip_diagnostic()
            st.rerun()

    # Progress bar
    st.progress((idx + 1) / total)
    st.caption("⏱️ Quick diagnostic to identify focus areas")
    st.markdown("---")

    # Current question
    q = questions[idx]
    topic_display = q["topic"].replace("_", " ").title()
    difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(q["difficulty"], "")

    st.caption(f"{difficulty_emoji} {topic_display}")
    st.markdown(f"**{q['prompt']}**")
    st.markdown("")

    # Answer choices
    current_answer = st.session_state.diagnostic_answers.get(q["id"])

    for i, choice in enumerate(q["choices"]):
        is_selected = current_answer == i
        btn_type = "primary" if is_selected else "secondary"
        if st.button(choice, key=f"choice_{q['id']}_{i}", type=btn_type, use_container_width=True):
            st.session_state.diagnostic_answers[q["id"]] = i
            st.rerun()

    st.markdown("---")

    # Navigation
    col1, col2 = st.columns(2)

    with col1:
        if idx > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.diagnostic_idx = idx - 1
                st.rerun()

    with col2:
        if idx < total - 1:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.diagnostic_idx = idx + 1
                st.rerun()
        else:
            # Last question - show finish button
            answered_count = len(st.session_state.diagnostic_answers)
            if st.button(f"✅ Finish ({answered_count}/{total} answered)", type="primary", use_container_width=True):
                finish_diagnostic()
                st.rerun()


# ============================================================
# DIAGNOSTIC RESULT PAGE
# ============================================================

def render_diagnostic_result():
    """Show diagnostic results and next steps."""
    course_names = {"124": "Math 124", "125": "Math 125", "126": "Math 126"}
    course = st.session_state.course

    st.markdown(f"## {course_names.get(course, 'Calculus')} Diagnostic Complete")
    st.markdown("---")

    strong = st.session_state.strong_topics
    weak = st.session_state.weak_topics

    def format_topic(t: str) -> str:
        return t.replace("_", " ").title()

    # Summary stats
    questions = st.session_state.diagnostic_questions
    answers = st.session_state.diagnostic_answers
    correct_count = sum(
        1 for q in questions
        if answers.get(q["id"]) == q["correct_index"]
    )
    total = len(questions)
    pct = int(correct_count / total * 100) if total > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Score", f"{correct_count}/{total}", f"{pct}%")
    with col2:
        if pct >= 80:
            st.success("Strong foundation!")
        elif pct >= 50:
            st.warning("Some gaps to fill")
        else:
            st.error("Needs focused practice")

    st.markdown("---")

    # Strengths (what looked good)
    if strong:
        st.markdown("### ✅ Looking good on")
        st.markdown(", ".join(f"**{format_topic(t)}**" for t in strong))
        st.markdown("")

    # Priority areas (NOT "weaknesses" - we're uncertain)
    if weak:
        st.markdown("### 📌 Recommended starting points")
        st.caption("Based on limited data — we'll refine as you practice")
        for t in weak:
            st.markdown(f"- {format_topic(t)}")
        st.markdown("")

        st.markdown("### 💡 Suggested first step")
        st.info(f"Start by reviewing **{format_topic(weak[0])}** — let's gather more signal here.")
    else:
        st.success("No red flags so far. Let's start practicing!")

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        btn_label = "🎯 Start recommended practice" if weak else "🎯 Start practice"
        if st.button(btn_label, type="primary", use_container_width=True):
            start_practice(recommended=True)
            st.rerun()

    with col2:
        if st.button("📚 Browse past exams", use_container_width=True):
            start_practice(recommended=False)
            st.rerun()

    # ============================================================
    # DEBUG: Show profile internals
    # ============================================================
    with st.expander("🔧 Debug: Student Profile"):
        profile = get_profile()
        if profile:
            st.markdown("**Raw Profile Data:**")

            st.markdown(f"- **Course:** {profile.course}")
            st.markdown(f"- **Diagnostic Score:** {profile.diagnostic_score:.1%}")
            st.markdown(f"- **Initial Focus Topics:** {profile.initial_focus_topics}")
            st.markdown(f"- **Needs Foundation:** {profile.needs_foundation}")

            st.markdown("**Topic Estimates:**")
            if profile.topic_estimates:
                for topic, estimate in profile.topic_estimates.items():
                    st.markdown(f"  - `{topic}`: {estimate.correct}/{estimate.attempts} correct, status={estimate.status_label}")
            else:
                st.markdown("  (empty)")

            st.markdown("**get_priority_topics() returns:**")
            priority_from_profile = profile.get_priority_topics()
            st.code(priority_from_profile)

            st.markdown("**Error Counts:**")
            st.json(profile.error_counts)

            # Show problem topics for comparison
            st.markdown("---")
            st.markdown("**Problem Bank Topics (for comparison):**")
            if st.session_state.get("parts_list"):
                problem_topics = set()
                for problem, _ in st.session_state.parts_list:
                    problem_topics.add(problem.topic)
                st.code(sorted(problem_topics))
            else:
                # Load problems to check
                from problem_loader import load_problems
                problems = load_problems(profile.course)
                problem_topics = set(p.topic for p in problems)
                st.code(sorted(problem_topics))

            # Check overlap
            st.markdown("**Topic Match Check:**")
            if priority_from_profile:
                for t in priority_from_profile:
                    if t in problem_topics:
                        st.markdown(f"  ✅ `{t}` exists in problem bank")
                    else:
                        st.markdown(f"  ❌ `{t}` NOT in problem bank")
        else:
            st.warning("No profile found")


# ============================================================
# PROBLEM PAGE
# ============================================================

def render_problem_page():
    """Render the problem + upload + grading page."""
    current = get_current_part()

    if not current:
        st.warning("No problems loaded for this course.")
        if st.button("← Back to course selection"):
            st.session_state.course = None
            st.session_state.mode = "select"
            st.rerun()
        return

    problem, part, part_idx = current

    # Header
    col_back, col_title, col_progress = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            st.session_state.course = None
            st.session_state.mode = "select"
            st.rerun()
    with col_title:
        course_names = {"124": "Math 124", "125": "Math 125", "126": "Math 126"}
        st.markdown(f"### {course_names.get(st.session_state.course, 'Calculus')}")
    with col_progress:
        total = len(st.session_state.problems)
        # Find current problem index
        current_problem_num = next(
            (i + 1 for i, p in enumerate(st.session_state.problems) if p.id == problem.id),
            1
        )
        st.caption(f"Q {current_problem_num}/{total}")

    st.markdown("---")

    # Source info
    source = problem.get_source_label()
    st.caption(f"📄 {source} · {problem.points} pts · {problem.topic.replace('_', ' ').title()}")

    # Show recommendation reason if applicable
    reason = get_recommendation_reason(problem, get_profile())
    if reason:
        st.info(f"🎯 {reason}")

    # Problem display
    st.markdown("#### 📝 Problem")

    # Show stem if exists
    if problem.stem:
        st.markdown(problem.stem)
        st.markdown("")

    # Show ALL parts of this problem
    diagram_shown = False
    for p in problem.parts:
        # Show part question
        if p.label:
            st.markdown(f"**({p.label})** {p.question_text}")
        else:
            st.markdown(p.question_text)

        # Show diagram if exists (only show once per problem)
        if p.has_diagram and not diagram_shown:
            if p.diagram_image_url:
                st.image(p.diagram_image_url, use_container_width=True)
            elif p.diagram_image:
                # Use path relative to this file's directory
                base_dir = os.path.dirname(os.path.abspath(__file__))
                diagram_path = os.path.join(base_dir, p.diagram_image)
                if os.path.exists(diagram_path):
                    st.image(diagram_path, use_container_width=True)
                else:
                    st.caption(f"📊 Diagram: {p.diagram_image} (not found)")
            diagram_shown = True

        st.markdown("")  # Space between parts

    st.markdown("---")

    # Upload section with tabs
    st.markdown("#### 📷 Submit your work")
    upload_tab, qr_tab = st.tabs(["📁 File Upload", "📱 QR Mobile Upload"])

    with upload_tab:
        uploaded_file = st.file_uploader(
            "Take a photo of your solution",
            type=["png", "jpg", "jpeg"],
            key=f"upload_{problem.id}",
            label_visibility="collapsed",
        )

        if uploaded_file:
            # Show preview
            st.image(uploaded_file, caption="Your work", use_container_width=True)

            if st.button("✅ Grade my work", type="primary", use_container_width=True):
                with st.spinner("Analyzing your work..."):
                    # Check quota
                    used_premium = can_use_premium()

                    # Parse image
                    image_bytes = uploaded_file.getvalue()
                    parsed = parse_image(image_bytes)

                    # Build full problem text with all parts
                    question_parts = []
                    if problem.stem:
                        question_parts.append(problem.stem)
                    for p in problem.parts:
                        if p.label:
                            question_parts.append(f"({p.label}) {p.question_text}")
                        else:
                            question_parts.append(p.question_text)

                    # Collect all final answers
                    final_answers = []
                    for p in problem.parts:
                        if p.final_answer:
                            label = f"({p.label}) " if p.label else ""
                            final_answers.append(f"{label}{p.final_answer}")

                    problem_dict = {
                        "question": "\n\n".join(question_parts),
                        "solution_steps": [],
                        "final_answer": "\n".join(final_answers) if final_answers else None,
                    }

                    # Pass first diagram URL if available
                    diagram_url = None
                    for p in problem.parts:
                        if p.has_diagram and p.diagram_image_url:
                            diagram_url = p.diagram_image_url
                            break

                    result = grade_solution(parsed, problem_dict, diagram_url=diagram_url)

                    # Record usage
                    record_query(used_premium=used_premium)

                    # Update stats
                    if result.is_correct:
                        st.session_state.error_stats["correct"] += 1
                    elif result.error_type:
                        st.session_state.error_stats[result.error_type] = (
                            st.session_state.error_stats.get(result.error_type, 0) + 1
                        )

                    # Update student profile
                    update_profile_from_grading(
                        topic=problem.topic,
                        correct=result.is_correct,
                        error_type=result.error_type if not result.is_correct else None
                    )

                    st.session_state.grading_result = result
                    st.rerun()

    with qr_tab:
        render_qr_upload_section(problem)

    # Grading result
    if st.session_state.grading_result:
        result = st.session_state.grading_result
        st.markdown("---")
        st.markdown("#### 📊 Feedback")

        if result.is_correct:
            st.success("✅ Correct! Well done.")
        else:
            # Error info
            if result.error_step is not None:
                st.markdown(f"**Error at:** Step {result.error_step + 1}")
            if result.error_type:
                st.markdown(f"**Type:** {render_error_badge(result.error_type)}", unsafe_allow_html=True)
            st.markdown(f"**What went wrong:** {result.feedback}")
            if result.hint:
                st.info(f"💡 **Hint:** {result.hint}")

            # Socratic teaching option
            if st.session_state.teaching_context:
                st.markdown("")
                if st.button("🎓 Get Help Understanding This", type="secondary", use_container_width=True):
                    st.session_state.teaching_mode = True
                    st.rerun()

        st.markdown("")

    # Teaching dialogue (Socratic mode)
    if st.session_state.teaching_mode and st.session_state.teaching_context:
        st.markdown("---")
        st.markdown("#### 🎓 Let's Work Through This")

        # Initialize teaching messages if not exists
        if "teaching_messages" not in st.session_state:
            st.session_state.teaching_messages = []

        # Start teaching session if no messages yet
        if not st.session_state.teaching_messages:
            with st.spinner("Preparing guidance..."):
                initial_response = start_teaching_session(st.session_state.teaching_context)
                st.session_state.teaching_messages.append({
                    "role": "assistant",
                    "content": initial_response
                })
                st.rerun()

        # Display teaching conversation
        for msg in st.session_state.teaching_messages:
            if msg["role"] == "assistant":
                st.markdown(f"**Claire:** {msg['content']}")
            else:
                st.markdown(f"**You:** {msg['content']}")

        # Student input
        student_input = st.text_input("Your answer:", key="teaching_input", placeholder="Type your response...")
        col_send, col_end = st.columns([3, 1])

        with col_send:
            if st.button("Send", use_container_width=True) and student_input:
                from teaching_orchestrator import orchestrate_teaching_response
                from session_state import TeachingMode, AgentAction

                # Add student message
                st.session_state.teaching_messages.append({
                    "role": "user",
                    "content": student_input
                })

                # Update teaching context mode and history
                if st.session_state.teaching_context:
                    ctx = st.session_state.teaching_context
                    ctx.mode = TeachingMode.CONTINUE_TEACHING
                    ctx.conversation_history = st.session_state.teaching_messages.copy()

                    # Get structured decision from orchestrator
                    if "claire_agent" in st.session_state:
                        agent = st.session_state.claire_agent
                        decision = orchestrate_teaching_response(
                            context=ctx,
                            agent=agent,
                            user_input=student_input,
                        )

                        # Add response
                        st.session_state.teaching_messages.append({
                            "role": "assistant",
                            "content": decision.message
                        })

                        # Auto-end session if confirmed correct
                        if decision.action == AgentAction.CONFIRM_CORRECT_AND_STOP:
                            st.session_state.teaching_mode = False
                            st.info("Session complete! Moving on.")

                st.rerun()

        with col_end:
            if st.button("End Session", use_container_width=True):
                st.session_state.teaching_mode = False
                st.session_state.teaching_messages = []
                st.session_state.teaching_context = None
                st.rerun()

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Show Answer", use_container_width=True):
            st.session_state.show_solution = True
            st.rerun()

    with col2:
        if st.button("➡️ Next Problem", type="primary", use_container_width=True):
            next_part()
            st.rerun()

    # Show solution if requested
    if st.session_state.show_solution:
        st.markdown("---")
        st.markdown("#### 📖 Answers")
        for p in problem.parts:
            if p.final_answer:
                if p.label:
                    st.markdown(f"**({p.label})** {p.final_answer}")
                else:
                    st.markdown(f"**Answer:** {p.final_answer}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### Claire")
    st.caption("UW Calculus Practice")
    st.divider()

    # User account section
    user = get_user()
    if user:
        # Logged in
        st.markdown(f"👤 {user.email}")

        # Pro status & quota
        if is_pro_user():
            st.markdown("✨ **Pro** - Unlimited")
            # Manage subscription link
            customer_id = st.session_state.get("stripe_customer_id")
            if customer_id:
                portal_url = get_customer_portal_url(customer_id)
                if portal_url:
                    st.link_button("Manage subscription", portal_url, use_container_width=True)
        else:
            quota = get_quota_status()
            st.markdown(f"📊 {quota['remaining']}/{quota['limit']} grading left today")

            # Upgrade button
            st.markdown("")
            if st.button("⭐ Upgrade to Pro", type="primary", use_container_width=True):
                checkout_url = create_checkout_session(user.id, user.email)
                if checkout_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
                else:
                    st.error("Could not create checkout session")
            st.caption("$9.99/mo • Unlimited Claude grading")

        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            sign_out()
            st.rerun()
    else:
        # Not logged in
        quota = get_quota_status()
        st.markdown(f"📊 {quota['remaining']}/{quota['limit']} grading left")
        st.caption("Sign in to save progress")
        st.markdown("")
        show_login_button("Sign in with Google")

    st.divider()

    # Student profile summary
    profile = get_profile()
    if profile and (profile.total_correct + profile.total_incorrect) > 0:
        st.markdown("#### Your Profile")
        accuracy = int(profile.overall_accuracy * 100)
        st.metric("Accuracy", f"{accuracy}%")

        # Priority topics (not "weak" - uncertain)
        priority = profile.get_priority_topics()[:3]
        if priority:
            st.markdown("**Focus areas:**")
            for t in priority:
                st.markdown(f"- {t.replace('_', ' ').title()}")

        # Dominant error type
        dominant = profile.get_dominant_error_type()
        if dominant:
            st.caption(f"Common error: {dominant}")

        if profile.needs_foundation:
            st.warning("📚 Foundation review recommended")

        st.divider()

    # Problem navigation (if course selected)
    if st.session_state.course and st.session_state.problems:
        st.markdown("#### 📚 Problems")

        # Group by exam
        exams = {}
        for problem in st.session_state.problems:
            exam_label = problem.get_source_label().split(" - ")[0]
            if exam_label not in exams:
                exams[exam_label] = []
            exams[exam_label].append(problem)

        for exam_label, problems in exams.items():
            with st.expander(f"{exam_label} ({len(problems)} problems)"):
                for problem in problems:
                    # Find first part index for this problem
                    for i, (p, _) in enumerate(st.session_state.parts_list):
                        if p.id == problem.id:
                            is_current_problem = any(
                                st.session_state.current_part_idx == j
                                for j, (pp, _) in enumerate(st.session_state.parts_list)
                                if pp.id == problem.id
                            )
                            prefix = "→ " if is_current_problem else ""
                            num_parts = len(problem.parts)
                            parts_label = f" ({num_parts} parts)" if num_parts > 1 else ""
                            btn_label = f"{prefix}P{problem.problem_number}: {problem.topic.replace('_', ' ').title()}{parts_label}"
                            if st.button(btn_label, key=f"nav_{problem.id}"):
                                st.session_state.current_part_idx = i
                                st.session_state.grading_result = None
                                st.session_state.show_solution = False
                                st.rerun()
                            break


# ============================================================
# MAIN ROUTING
# ============================================================

if st.session_state.mode == "select" or st.session_state.course is None:
    render_course_selection()
elif st.session_state.mode == "diagnostic":
    render_diagnostic()
elif st.session_state.mode == "diagnostic_result":
    render_diagnostic_result()
else:
    render_problem_page()
