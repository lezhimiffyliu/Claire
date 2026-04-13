"""
Claire - Making Calculus Clear
UW Calculus Practice + Photo Grading
"""

import streamlit as st
from problem_loader import load_problems, get_all_parts, Problem, ProblemPart
from grader import parse_image, grade_solution, GradingResult
from quota import can_use_premium, record_query, get_quota_status, is_pro_user
from student_profile import (
    StudentProfile, get_profile, save_profile, create_profile,
    update_profile_from_diagnostic, update_profile_from_grading
)
from recommender import recommend_next_problem, get_recommendation_reason

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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

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
    return questions[:count]


def select_course(course: str):
    """Select a course and start diagnostic."""
    st.session_state.course = course
    st.session_state.mode = "diagnostic"
    st.session_state.diagnostic_questions = get_diagnostic_questions(course)
    st.session_state.diagnostic_idx = 0
    st.session_state.diagnostic_answers = {}
    st.session_state.weak_topics = []

    # Create student profile (stored in session for anonymous users)
    create_profile(course)


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
    """Move to next part using smart recommendation."""
    if st.session_state.parts_list:
        # Mark current as seen
        st.session_state.seen_problem_indices.add(st.session_state.current_part_idx)

        # Use recommender to pick next problem
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

    col_back, col_title, col_progress = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            st.session_state.course = None
            st.session_state.mode = "select"
            st.rerun()
    with col_title:
        st.markdown(f"### {course_names.get(course, 'Calculus')} Diagnostic")
    with col_progress:
        st.caption(f"{idx + 1}/{total}")

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

            st.markdown("**Topic Mastery:**")
            if profile.topic_mastery:
                for topic, mastery in profile.topic_mastery.items():
                    st.markdown(f"  - `{topic}`: {mastery.correct}/{mastery.attempts} correct, level={mastery.mastery_level}")
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
        total = len(st.session_state.parts_list)
        current_num = st.session_state.current_part_idx + 1
        st.caption(f"Q {current_num}/{total}")

    st.markdown("---")

    # Source info
    source = problem.get_source_label()
    part_label = f" ({part.label})" if part.label else ""
    st.caption(f"📄 {source}{part_label} · {problem.points} pts · {problem.topic.replace('_', ' ').title()}")

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

    # Show part question
    if part.label:
        st.markdown(f"**({part.label})** {part.question_text}")
    else:
        st.markdown(part.question_text)

    # Show diagram if exists
    if part.has_diagram and part.diagram_image:
        diagram_path = f"/Users/lezhiliu/Desktop/calculus/{part.diagram_image}"
        try:
            st.image(diagram_path, caption="Diagram", use_container_width=True)
        except:
            st.caption(f"📊 Diagram: {part.diagram_image}")

    st.markdown("---")

    # Upload section
    st.markdown("#### 📷 Upload your work")
    uploaded_file = st.file_uploader(
        "Take a photo of your solution",
        type=["png", "jpg", "jpeg"],
        key=f"upload_{problem.id}_{part_idx}",
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

                # Build problem dict for grading
                question_text = problem.get_display_text(part_idx)
                problem_dict = {
                    "question": question_text,
                    "solution_steps": [],  # Not available in this format
                    "final_answer": part.final_answer,
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

                # Update student profile
                update_profile_from_grading(
                    topic=problem.topic,
                    correct=result.is_correct,
                    error_type=result.error_type if not result.is_correct else None
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
        if st.button("📝 Show Answer", use_container_width=True):
            st.session_state.show_solution = True
            st.rerun()

    with col2:
        if st.button("➡️ Next Question", type="primary", use_container_width=True):
            next_part()
            st.rerun()

    # Show solution if requested
    if st.session_state.show_solution:
        st.markdown("---")
        st.markdown("#### 📖 Answer")
        st.markdown(f"**Final Answer:** {part.final_answer}")


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
                            is_current = i == st.session_state.current_part_idx
                            prefix = "→ " if is_current else ""
                            btn_label = f"{prefix}P{problem.problem_number}: {problem.topic.replace('_', ' ').title()}"
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
