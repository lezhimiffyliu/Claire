"""
Claire - Making Calculus Clear
Calculus Cram: Exam prep powered by AI
"""

import streamlit as st
from claire_agent import ClaireAgent
from exam_context import analyze_files, ExamContext

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

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        agent.conversation_history = []
        st.rerun()


# ============================================================
# SHOW PROBLEM DIALOG IF SELECTED
# ============================================================
if st.session_state.selected_problem:
    show_problem_detail(st.session_state.selected_problem)

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
# MAIN AREA
# ============================================================

# Header
if not st.session_state.messages:
    st.markdown("## Claire")
    st.caption("Making Calculus Clear · Calculus Cram")
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
    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


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
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            result = agent.process_query(prompt)
        st.markdown(result["output"])

    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
