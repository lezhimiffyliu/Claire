# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claire ("Making Calculus Clear") is an AI-powered calculus teaching assistant built on LangChain's ReAct agent framework. It uses Claude Sonnet for reasoning and SymPy for symbolic mathematics, providing Socratic-style tutoring through both Web UI and CLI interfaces.

## Commands

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Run Web UI (recommended)
streamlit run app.py

# Or run CLI
python3 main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Configuration
Edit `.env` file to configure:
- `ANTHROPIC_API_KEY` - Required for Claire's AI capabilities (Claude Sonnet)

## Architecture

```
User Input → main.py (CLI) / app.py (Web)
                    ↓
            ClaireAgent.process_query()
                    ↓
            System Command Check
                    ↓
            AgentExecutor.invoke()
                    ↓
            ┌───────────────────────────────────────┐
            │         ReAct Loop                    │
            │  Thought → Action → Observation → ... │
            └───────────────────────────────────────┘
                    ↓                    ↓
            LangChain Tools          Claude Reasoning
            (SymPy-based)           (Socratic guidance)
                    ↓
            Final Response (dict)
            {output, intermediate_steps}
```

### Core Files

- **app.py** - Streamlit web UI with thought visualization
- **main.py** - CLI entry point
- **claire_agent.py** - LangChain ReAct agent, Socratic prompt, session management
- **sympy_tools.py** - LangChain @tool decorated SymPy functions
- **sympy_backup.py** - Legacy SymPy engine (reference)
- **knowledge_loader.py** - Embedded knowledge base (fallback)

### LangChain Tools

Five math tools available to the ReAct agent:

| Tool | Function | Description |
|------|----------|-------------|
| `calculate_derivative` | `diff()` | Differentiate expressions |
| `calculate_integral` | `integrate()` | Indefinite/definite integrals |
| `calculate_limit` | `limit()` | Limits with direction support |
| `solve_equation` | `solve()` | Solve equations for variables |
| `simplify_expression` | `simplify()` | Algebraic simplification |

### Agent Configuration

```python
AgentExecutor(
    agent=create_react_agent(llm, tools, prompt),
    tools=CLAIRE_TOOLS,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
    return_intermediate_steps=True
)
```

### Socratic System Prompt

The agent is configured with a Socratic teaching prompt that:
- Never gives direct numerical answers
- Uses tools to verify calculations internally
- Guides students with questions based on tool observations
- Adapts language to student level (beginner/intermediate/advanced)
- Responds in the same language as the student's question

## Key Implementation Details

- **LLM**: Claude Sonnet via `langchain-anthropic`
- **Session history**: Last 10 messages in `ClaireAgent.conversation_history`
- **Return type**: `process_query()` returns `dict` with `output` and `intermediate_steps`
- **System commands**: `help`, `examples`, `capabilities`, `status`, `level`, `clear`, `reset`, `/study`
- **Guided Learning Mode** (`/study`): Default ON - enables Socratic teaching style
- **Thought visualization**: Streamlit UI shows agent's thinking process via `st.status`

## Dependencies

Core LangChain stack:
- `langchain>=0.2.0`
- `langchain-core>=0.2.0`
- `langchain-anthropic>=0.1.0`

Math and utilities:
- `sympy>=1.12`
- `streamlit>=1.28.0`
- `python-dotenv>=1.0.0`
