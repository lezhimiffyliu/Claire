"""
Claire - Making Calculus Clear
UW Calculus Practice + Photo Grading
"""

import streamlit as st
from problem_loader import load_problems, Problem
from grader import parse_image, grade_solution, GradingResult
from quota import can_use_premium, record_query, get_quota_status, is_pro_user

# Page config
st.set_page_config(
    page_title="Claire",
    page_icon="📐",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px; }
    .stButton button { font-weight: 500; }

    /* Difficulty badges */
    .difficulty-easy { color: #155724; }
    .difficulty-medium { color: #856404; }
    .difficulty-hard { color: #721c24; }

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

if "problems" not in st.session_state:
    st.session_state.problems = []

if "current_problem_idx" not in st.session_state:
    st.session_state.current_problem_idx = 0

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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def select_course(course: str):
    """Select a course and load its problems."""
    st.session_state.course = course
    st.session_state.problems = load_problems(course)
    st.session_state.current_problem_idx = 0
    st.session_state.grading_result = None
    st.session_state.show_solution = False


def next_problem():
    """Move to next problem."""
    if st.session_state.problems:
        st.session_state.current_problem_idx = (
            st.session_state.current_problem_idx + 1
        ) % len(st.session_state.problems)
        st.session_state.grading_result = None
        st.session_state.show_solution = False


def get_current_problem() -> Problem | None:
    """Get the current problem."""
    if not st.session_state.problems:
        return None
    idx = st.session_state.current_problem_idx
    if 0 <= idx < len(st.session_state.problems):
        return st.session_state.problems[idx]
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
# PROBLEM PAGE
# ============================================================

def render_problem_page():
    """Render the problem + upload + grading page."""
    problem = get_current_problem()

    if not problem:
        st.warning("No problems loaded for this course.")
        if st.button("← Back to course selection"):
            st.session_state.course = None
            st.rerun()
        return

    # Header
    col_back, col_title, col_progress = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            st.session_state.course = None
            st.rerun()
    with col_title:
        course_names = {"124": "Math 124", "125": "Math 125", "126": "Math 126"}
        st.markdown(f"### {course_names.get(st.session_state.course, 'Calculus')}")
    with col_progress:
        total = len(st.session_state.problems)
        current = st.session_state.current_problem_idx + 1
        st.caption(f"Problem {current}/{total}")

    st.markdown("---")

    # Problem display
    st.markdown("#### 📝 Problem")
    diff_icons = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
    st.caption(f"{diff_icons.get(problem.difficulty, '')} {problem.difficulty.capitalize()} · {problem.topic.replace('_', ' ').title()}")
    st.markdown(problem.question)

    st.markdown("---")

    # Upload section
    st.markdown("#### 📷 Upload your work")
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

                # Grade
                problem_dict = {
                    "question": problem.question,
                    "solution_steps": problem.solution_steps,
                    "final_answer": problem.final_answer,
                }
                result = grade_solution(parsed, problem_dict)

                # Record usage
                record_query(used_premium=used_premium)

                # Update stats
                if result.is_correct:
                    st.session_state.error_stats["correct"] += 1
                elif result.error_type:
                    st.session_state.error_stats[result.error_type] = (
                        st.session_state.error_stats.get(result.error_type, 0) + 1
                    )

                st.session_state.grading_result = result
                st.rerun()

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

        st.markdown("")

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Show Solution", use_container_width=True):
            st.session_state.show_solution = True
            st.rerun()

    with col2:
        if st.button("➡️ Next Problem", type="primary", use_container_width=True):
            next_problem()
            st.rerun()

    # Show solution if requested
    if st.session_state.show_solution:
        st.markdown("---")
        st.markdown("#### 📖 Solution")
        for i, step in enumerate(problem.solution_steps):
            st.markdown(f"**Step {i+1}:** {step}")
        st.markdown(f"**Final Answer:** {problem.final_answer}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### Claire")
    st.caption("UW Calculus Practice")
    st.divider()

    # Quota status
    quota = get_quota_status()
    if is_pro_user():
        st.markdown("✨ **Pro** - Unlimited")
    else:
        st.markdown(f"📊 {quota['remaining']}/{quota['limit']} grading left today")

    st.divider()

    # Error stats
    if any(v > 0 for v in st.session_state.error_stats.values()):
        st.markdown("#### Your Session Stats")
        stats = st.session_state.error_stats
        total = sum(stats.values())
        if total > 0:
            correct_pct = int(stats["correct"] / total * 100) if total else 0
            st.metric("Accuracy", f"{correct_pct}%")

            st.markdown("**Error breakdown:**")
            for error_type in ["algebra", "concept", "logic", "careless"]:
                count = stats.get(error_type, 0)
                if count > 0:
                    st.markdown(f"- {error_type.title()}: {count}")

        st.divider()

    # Problem list (if course selected)
    if st.session_state.course and st.session_state.problems:
        with st.expander("📚 All Problems"):
            for i, p in enumerate(st.session_state.problems):
                diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(p.difficulty, "")
                is_current = i == st.session_state.current_problem_idx
                prefix = "→ " if is_current else ""
                if st.button(f"{prefix}{diff_icon} {p.topic}", key=f"nav_{i}"):
                    st.session_state.current_problem_idx = i
                    st.session_state.grading_result = None
                    st.session_state.show_solution = False
                    st.rerun()


# ============================================================
# MAIN ROUTING
# ============================================================

if st.session_state.course is None:
    render_course_selection()
else:
    render_problem_page()
