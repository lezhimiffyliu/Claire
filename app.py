"""
Claire Streamlit Web Interface
"""
import streamlit as st
from claire_agent import ClaireAgent

# Page config
st.set_page_config(
    page_title="Claire - Making Calculus Clear",
    page_icon="∫",
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
    st.markdown("## ∫ Claire: Your Clear Calculus Companion")
    st.caption("Making Calculus Clear")

    st.divider()

    # Study mode toggle
    study_mode = st.toggle(
        "📖 Guided Learning",
        value=agent.guided_mode,
        help="Socratic method - I'll guide you with questions"
    )
    if study_mode != agent.guided_mode:
        agent.guided_mode = study_mode

    # User level
    level = st.selectbox(
        "Level",
        options=["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(agent.user_level)
    )
    if level != agent.user_level:
        agent.user_level = level

    st.divider()

    # Status
    st.caption("System Status")
    col1, col2 = st.columns(2)
    col1.metric("Math", "SymPy ✓", delta=None)
    col2.metric("AI", "GPT ✓" if agent.ai_client else "Limited", delta=None)

    st.divider()

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        agent.conversation_history = []
        st.rerun()

# Main area
if not st.session_state.messages:
    # Welcome screen - show when no messages
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0;">∫ Claire</h1>
        <p style="font-size: 1.2rem; color: #666; margin-top: 5px;">Making Calculus Clear</p>
    </div>
    """, unsafe_allow_html=True)

    # Math capabilities showcase
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 2rem;">d/dx</div>
            <div style="font-weight: bold;">Derivatives</div>
            <div style="font-size: 0.85rem; color: #666;">Chain rule, product rule, implicit differentiation</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 2rem;">∫</div>
            <div style="font-weight: bold;">Integrals</div>
            <div style="font-size: 0.85rem; color: #666;">Definite, indefinite, techniques</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 2rem;">lim</div>
            <div style="font-weight: bold;">Limits</div>
            <div style="font-size: 0.85rem; color: #666;">L'Hôpital's rule, continuity</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 2rem;">Σ</div>
            <div style="font-weight: bold;">Series</div>
            <div style="font-size: 0.85rem; color: #666;">Convergence, Taylor series</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick start examples
    st.markdown("#### Try asking:")

    examples = [
        ("Derivative of x³+2x", "Calculate the derivative of x^3 + 2x"),
        ("∫ sin(x) dx", "What is the integral of sin(x)?"),
        ("lim sin(x)/x", "Find the limit of sin(x)/x as x approaches 0"),
        ("What is chain rule?", "Explain the chain rule with examples"),
        ("Solve x²-5x+6=0", "Solve x^2 - 5x + 6 = 0"),
        ("Teach integration", "Teach me integration by parts step by step"),
    ]

    cols = st.columns(3)
    for i, (label, query) in enumerate(examples):
        with cols[i % 3]:
            if st.button(label, key=f"example_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": query})
                with st.spinner("Thinking..."):
                    response = agent.process_query(query)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

else:
    # Chat mode - show messages
    st.markdown("## ∫ Claire")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

# Chat input
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your question:",
        placeholder="Ask me about derivatives, integrals, limits, or any calculus concept...",
        height=80,
        label_visibility="collapsed"
    )
    submit = st.form_submit_button("Ask Claire", use_container_width=True)

if submit and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Calculating..."):
        response = agent.process_query(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
