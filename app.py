"""
Claire 2.0 - Streamlit Web Interface
Unified Exam Preparation: Upload Materials → Detect Patterns → Guided Practice
"""

import streamlit as st
from claire_agent import ClaireAgent
from exam_context import analyze_files, ExamContext

# Page config
st.set_page_config(
    page_title="Claire - Exam Prep",
    page_icon="",
    layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = ClaireAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "exam_context" not in st.session_state:
    st.session_state.exam_context = ExamContext()

agent = st.session_state.agent


# ============================================================
# SIDEBAR: Course Materials & Settings
# ============================================================
with st.sidebar:
    st.markdown("## Claire 2.0")
    st.caption("Exam Preparation Agent")

    st.divider()

    # Course Materials Section
    st.markdown("### Course Materials")
    st.caption("Upload notes, exams, or paste text")

    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="PDF, TXT, or MD files (lecture notes, practice exams, etc.)"
    )

    pasted_notes = st.text_area(
        "Or paste notes",
        placeholder="Paste syllabus, review topics, or exam problems...",
        height=100,
        label_visibility="collapsed"
    )

    if st.button("Analyze Materials", use_container_width=True):
        files = []

        # Process uploaded files
        for f in uploaded_files or []:
            try:
                file_bytes = f.getvalue()
                files.append((f.name, file_bytes))
            except Exception:
                pass

        # Process pasted notes
        if pasted_notes.strip():
            files.append(("pasted_notes.txt", pasted_notes.encode("utf-8")))

        if files:
            with st.spinner("Analyzing..."):
                context = analyze_files(files)
                st.session_state.exam_context = context
                agent.set_exam_context(context)

            q_count = context.get_question_count()
            if q_count > 0:
                st.success(f"Found {q_count} questions")
            else:
                st.success(f"Analyzed {len(files)} files")
            st.rerun()
        else:
            st.warning("Add materials first")

    # Show detected patterns and questions if context exists
    exam_context = st.session_state.exam_context
    if exam_context.has_context():
        st.divider()

        # Show question count
        if exam_context.has_questions():
            st.markdown(f"### {exam_context.get_question_count()} Questions")
            counts = exam_context.question_bank.get_pattern_counts()
            for pattern, count in sorted(counts.items(), key=lambda x: -x[1])[:4]:
                st.caption(f"{pattern.replace('_', ' ').title()}: {count}")
        else:
            st.markdown("### Detected Patterns")
            for p in exam_context.detected_patterns[:4]:
                with st.container():
                    st.markdown(f"**{p.name.replace('_', ' ').title()}**")
                    st.caption(f"{', '.join(p.evidence[:3])}")

        if st.button("Clear Materials", use_container_width=True):
            st.session_state.exam_context = ExamContext()
            agent.clear_exam_context()
            st.rerun()

    st.divider()

    # Settings
    level = st.selectbox(
        "Difficulty",
        options=["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(agent.user_level),
    )
    if level != agent.user_level:
        agent.user_level = level

    st.divider()

    # Clear chat
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        agent.conversation_history = []
        agent.current_pattern = None
        agent.current_heuristic = None
        st.rerun()


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def format_tool_name(tool_name: str) -> str:
    name_map = {
        "calculate_derivative": "Derivative",
        "calculate_integral": "Integral",
        "calculate_limit": "Limit",
        "solve_equation": "Solve",
        "simplify_expression": "Simplify",
        "get_heuristic": "Heuristic",
    }
    return name_map.get(tool_name, tool_name)


def process_and_display(query: str):
    with st.status("Processing...", expanded=False) as status:
        result = agent.process_query(query)

        if not result.get("is_continuation"):
            pattern = result.get("pattern")
            if pattern:
                # Check if pattern is in exam context
                exam_patterns = [p.name for p in st.session_state.exam_context.detected_patterns]
                if pattern in exam_patterns:
                    st.markdown(f"**Pattern:** {pattern.replace('_', ' ').title()} *(from your materials)*")
                else:
                    st.markdown(f"**Pattern:** {pattern.replace('_', ' ').title()}")

        steps = result.get("intermediate_steps", [])
        if steps:
            tool_names = [format_tool_name(s.name) for s in steps if hasattr(s, "name")]
            if tool_names:
                st.caption(f"Tools: {', '.join(tool_names)}")

        status.update(label="Done", state="complete", expanded=False)

    return result


# ============================================================
# MAIN AREA
# ============================================================

# Header with context indicator
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("## Claire 2.0")
with col2:
    if exam_context.has_context():
        st.success(f"{len(exam_context.detected_patterns)} patterns loaded")

# Show welcome or chat
if not st.session_state.messages:
    # Welcome screen
    st.markdown("---")

    # Different welcome based on whether context is loaded
    if exam_context.has_context():
        # Check if we have extracted questions
        if exam_context.has_questions():
            st.markdown("### Your Question Bank")
            st.markdown(f"**{exam_context.get_question_count()}** questions extracted from your materials")

            # Show questions grouped by pattern
            bank = exam_context.question_bank
            for pattern in bank.get_patterns()[:4]:
                questions = bank.get_by_pattern(pattern)
                with st.expander(f"**{pattern.replace('_', ' ').title()}** ({len(questions)} questions)", expanded=False):
                    for i, q in enumerate(questions[:5]):
                        st.markdown(f"{i+1}. {q.text[:150]}..." if len(q.text) > 150 else f"{i+1}. {q.text}")

            st.markdown("---")
            st.markdown("### Practice from Your Materials")
            st.caption("Click a pattern to practice with questions from your course")

            cols = st.columns(2)
            for i, pattern in enumerate(bank.get_patterns()[:4]):
                questions = bank.get_by_pattern(pattern)
                if questions:
                    with cols[i % 2]:
                        if st.button(f"{pattern.replace('_', ' ').title()} ({len(questions)})", key=f"bank_{i}", use_container_width=True):
                            # Use actual question from bank
                            q = questions[0]
                            st.session_state.messages.append({"role": "user", "content": q.text})
                            result = process_and_display(q.text)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result.get("output", ""),
                                "pattern": result.get("pattern"),
                                "heuristic": result.get("heuristic"),
                                "steps": result.get("intermediate_steps", []),
                                "is_continuation": result.get("is_continuation", False),
                            })
                            st.rerun()

        else:
            # No questions extracted, show pattern-based view
            st.markdown("### Your Exam Focus Areas")
            st.markdown("Based on your uploaded materials, focus on these patterns:")

            cols = st.columns(min(3, len(exam_context.detected_patterns[:3])))
            for i, p in enumerate(exam_context.detected_patterns[:3]):
                with cols[i]:
                    st.markdown(f"**{p.name.replace('_', ' ').title()}**")
                    st.caption(p.priority)

            st.markdown("---")
            st.markdown("### Practice These Patterns")

            pattern_examples = {
                "optimization": "Find the dimensions of a rectangle with perimeter 100 that has maximum area",
                "constrained_optimization": "Maximize f(x,y) = xy subject to x + 2y = 10",
                "related_rates": "A ladder 10 ft long rests against a wall. The bottom slides away at 2 ft/s. How fast is the top sliding down when the bottom is 6 ft from the wall?",
                "derivatives": "Find the derivative of ln(x^2 + 1)",
                "integration": "Find the integral of x*e^x dx",
                "limits": "Find the limit of (sin x)/x as x approaches 0",
            }

            cols = st.columns(2)
            for i, p in enumerate(exam_context.detected_patterns[:4]):
                example = pattern_examples.get(p.name, f"Practice {p.name} problem")
                with cols[i % 2]:
                    if st.button(p.name.replace('_', ' ').title(), key=f"pattern_{i}", use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": example})
                        result = process_and_display(example)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result.get("output", ""),
                            "pattern": result.get("pattern"),
                            "heuristic": result.get("heuristic"),
                            "steps": result.get("intermediate_steps", []),
                            "is_continuation": result.get("is_continuation", False),
                        })
                        st.rerun()

    else:
        # No context - show general welcome
        st.markdown("""
        **Claire teaches problem-solving patterns, not just solutions.**

        **Quick Start:**
        1. Upload course materials in sidebar (optional but recommended)
        2. Claire detects which patterns are likely on your exam
        3. Practice problems with step-by-step guidance
        4. Learn reusable heuristics for each pattern type

        **Or just ask a calculus problem directly.**
        """)

        st.markdown("---")
        st.markdown("### Try an Example")

        examples = [
            ("Optimization", "Find the dimensions of a rectangle with perimeter 100 that has maximum area"),
            ("Lagrange", "Maximize f(x,y) = xy subject to x + 2y = 10"),
            ("Related Rates", "A ladder 10 ft long rests against a wall. The bottom slides away at 2 ft/s. How fast is the top sliding down when the bottom is 6 ft from the wall?"),
            ("Integration", "Find the integral of x*e^x dx"),
        ]

        cols = st.columns(2)
        for i, (label, query) in enumerate(examples):
            with cols[i % 2]:
                if st.button(label, key=f"example_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": query})
                    result = process_and_display(query)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.get("output", ""),
                        "pattern": result.get("pattern"),
                        "heuristic": result.get("heuristic"),
                        "steps": result.get("intermediate_steps", []),
                        "is_continuation": result.get("is_continuation", False),
                    })
                    st.rerun()

else:
    # Chat mode - display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message.get("content", ""))
            else:
                is_continuation = message.get("is_continuation", False)

                if not is_continuation:
                    pattern = message.get("pattern")
                    if pattern:
                        # Highlight if pattern is from exam context
                        exam_patterns = [p.name for p in exam_context.detected_patterns]
                        if pattern in exam_patterns:
                            st.info(f"Pattern: **{pattern.replace('_', ' ').title()}** — *This pattern is in your exam materials*")
                        else:
                            st.markdown(f"**Pattern:** {pattern.replace('_', ' ').title()}")
                        st.markdown("---")

                    heuristic = message.get("heuristic")
                    if heuristic:
                        with st.expander("View Heuristic Template", expanded=False):
                            st.markdown(heuristic)

                content = message.get("content", "")
                if isinstance(content, dict):
                    content = content.get("output", str(content))
                st.markdown(content, unsafe_allow_html=True)

                steps = message.get("steps", [])
                if steps:
                    with st.expander("Calculations", expanded=False):
                        for step in steps:
                            if hasattr(step, "name") and hasattr(step, "content"):
                                tool_name = format_tool_name(step.name)
                                st.caption(f"**{tool_name}**")
                                tool_content = step.content
                                if len(tool_content) > 200:
                                    tool_content = tool_content[:200] + "..."
                                st.code(tool_content, language="text")


# ============================================================
# CHAT INPUT
# ============================================================
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your question:",
        placeholder="Enter a calculus problem or answer Claire's question...",
        height=80,
        label_visibility="collapsed",
    )
    submit = st.form_submit_button("Submit", use_container_width=True)

if submit and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    result = process_and_display(user_input)
    st.session_state.messages.append({
        "role": "assistant",
        "content": result.get("output", ""),
        "pattern": result.get("pattern"),
        "heuristic": result.get("heuristic"),
        "steps": result.get("intermediate_steps", []),
        "is_continuation": result.get("is_continuation", False),
    })
    st.rerun()
