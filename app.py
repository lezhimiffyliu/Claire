"""
Claire 2.0 - Streamlit Web Interface
Exam Preparation Agent with Teaching-First Approach
"""

import streamlit as st
from claire_agent import ClaireAgent

# Page config
st.set_page_config(
    page_title="Claire - Exam Prep",
    page_icon="",
    layout="wide"
)

# Initialize agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = ClaireAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

agent = st.session_state.agent

# Sidebar
with st.sidebar:
    st.markdown("## Claire 2.0")
    st.caption("Calculus Exam Preparation")

    st.divider()

    # User level
    level = st.selectbox(
        "Difficulty Level",
        options=["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(agent.user_level),
    )
    if level != agent.user_level:
        agent.user_level = level

    st.divider()

    # Available patterns
    with st.expander("Problem Patterns", expanded=False):
        from pattern_tools import get_available_patterns
        for pattern in get_available_patterns():
            st.markdown(f"- {pattern.replace('_', ' ').title()}")

    st.divider()

    # Status
    st.caption("System")
    col1, col2 = st.columns(2)
    col1.metric("Math", "SymPy", delta=None)
    col2.metric("AI", "Claude" if agent.executor else "Off", delta=None)

    st.divider()

    # Clear chat
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        agent.conversation_history = []
        agent.current_pattern = None
        agent.current_heuristic = None
        st.rerun()


def format_tool_name(tool_name: str) -> str:
    """Format tool name for display"""
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
    """Process query and return result with pattern/heuristic info."""
    with st.status("Processing...", expanded=False) as status:
        # Process through agent (handles pattern detection internally)
        result = agent.process_query(query)

        # Show pattern only for new questions (not continuations)
        if not result.get("is_continuation"):
            pattern = result.get("pattern")
            if pattern:
                st.markdown(f"**Detected Pattern:** {pattern.replace('_', ' ').title()}")

        # Show tool usage (if any)
        steps = result.get("intermediate_steps", [])
        if steps:
            tool_names = [format_tool_name(s.name) for s in steps if hasattr(s, "name")]
            if tool_names:
                st.caption(f"Tools used: {', '.join(tool_names)}")

        status.update(label="Ready", state="complete", expanded=False)

    return result


# Main area
if not st.session_state.messages:
    # Welcome screen
    st.markdown(
        """
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0;">Claire 2.0</h1>
        <p style="font-size: 1.2rem; color: #666; margin-top: 5px;">Calculus Exam Preparation</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Teaching philosophy
    st.markdown("""
    **Claire teaches problem-solving patterns, not just solutions.**

    When you enter a problem, Claire will:
    1. Detect the problem pattern
    2. Show you the solving heuristic
    3. Guide you through the first step
    4. Ask you to try the next step

    Claire will NOT give you the final answer directly.
    """)

    st.markdown("---")

    # Quick start examples
    st.markdown("#### Try an exam-style problem:")

    examples = [
        ("Optimization", "Find the dimensions of a rectangle with perimeter 100 that has maximum area"),
        ("Lagrange", "Maximize f(x,y) = xy subject to x + 2y = 10"),
        ("Related Rates", "A ladder 10 ft long rests against a wall. The bottom slides away at 2 ft/s. How fast is the top sliding down when the bottom is 6 ft from the wall?"),
        ("Integration", "Find the integral of x*e^x dx"),
        ("Limits", "Find the limit of (sin x)/x as x approaches 0"),
        ("Derivatives", "Find the derivative of ln(x^2 + 1)"),
    ]

    cols = st.columns(2)
    for i, (label, query) in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"{label}", key=f"example_{i}", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": query
                })
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
    # Chat mode
    st.markdown("## Claire 2.0")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message.get("content", ""))
            else:
                is_continuation = message.get("is_continuation", False)

                # 1. Pattern (only for new questions, not continuations)
                if not is_continuation:
                    pattern = message.get("pattern")
                    if pattern:
                        st.markdown(f"**Detected Pattern:** {pattern.replace('_', ' ').title()}")
                        st.markdown("---")

                    # 2. Heuristic summary (collapsible, only for new questions)
                    heuristic = message.get("heuristic")
                    if heuristic:
                        with st.expander("View Heuristic Template", expanded=False):
                            st.markdown(heuristic)

                # 3. Main response (teaching content)
                content = message.get("content", "")
                if isinstance(content, dict):
                    content = content.get("output", str(content))
                st.markdown(content, unsafe_allow_html=True)

                # 4. Tool calls (at the end, collapsed)
                steps = message.get("steps", [])
                if steps:
                    with st.expander("Calculations Used", expanded=False):
                        for step in steps:
                            if hasattr(step, "name") and hasattr(step, "content"):
                                tool_name = format_tool_name(step.name)
                                st.caption(f"**{tool_name}**")
                                content = step.content
                                if len(content) > 200:
                                    content = content[:200] + "..."
                                st.code(content, language="text")

# Chat input
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your question:",
        placeholder="Enter a calculus problem or answer Claire's question...",
        height=80,
        label_visibility="collapsed",
    )
    submit = st.form_submit_button("Submit", use_container_width=True)

if submit and user_input.strip():
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
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
