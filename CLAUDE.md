# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Claire 2.0 is an AI-powered calculus **exam preparation agent**. It teaches problem-solving **patterns** and **heuristics**, not just solutions. Built on LangChain ReAct agents with Claude Sonnet and SymPy.

**Key difference from generic tutors:**
- Generic tutor: problem → answer
- Claire: problem → pattern → heuristic → guided steps → understanding

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run Web UI
streamlit run app.py

# Run CLI
python3 main.py
```

## Architecture

```
Problem Input
      │
      ▼
detect_pattern()        ← Rule-based classification
      │
      ▼
get_heuristic()         ← Load markdown template
      │
      ▼
ReAct Agent             ← Teaching-first prompt
      │
      ▼
Guided Response
(Pattern → Heuristic → Step 1 → Question)
```

## Core Files

| File | Purpose |
|------|---------|
| `claire_agent.py` | ReAct agent with teaching-first prompt |
| `pattern_tools.py` | Pattern detection + heuristic retrieval |
| `sympy_tools.py` | SymPy math tools (5 tools) |
| `heuristics/*.md` | Markdown solving templates |
| `app.py` | Streamlit web UI |
| `main.py` | CLI entry point |

## Tools (6 total)

| Tool | Source | Purpose |
|------|--------|---------|
| `calculate_derivative` | sympy_tools.py | Differentiation |
| `calculate_integral` | sympy_tools.py | Integration |
| `calculate_limit` | sympy_tools.py | Limits |
| `solve_equation` | sympy_tools.py | Equations |
| `simplify_expression` | sympy_tools.py | Simplification |
| `get_heuristic` | pattern_tools.py | Load solving template |

## Pattern Detection

`detect_pattern()` classifies problems into 6 types:

| Pattern | Keywords |
|---------|----------|
| `optimization` | maximize, minimize, largest, smallest |
| `constrained_optimization` | subject to, constraint, Lagrange |
| `related_rates` | rate of change, how fast, per second |
| `derivatives` | derivative, d/dx, differentiate |
| `integration` | integral, antiderivative, ∫ |
| `limits` | limit, approaches, L'Hopital |

## Heuristic Files

Located in `heuristics/` directory:

```
heuristics/
├── optimization.md
├── constrained_optimization.md
├── related_rates.md
├── derivatives.md
├── integration.md
└── limits.md
```

Each file contains:
- Pattern recognition tips
- Decision tree
- Solving template (numbered steps)
- Common mistakes

## Agent Behavior

The system prompt enforces:

1. **Show pattern first** - Always start with detected pattern
2. **Show heuristic** - Present the solving template
3. **Guide step by step** - Only guide through Step 1
4. **Ask questions** - End with a question for the student
5. **Minimize tool calls** - Only use SymPy for verification
6. **No direct answers** - Teach the method, not the result

## Key Implementation Details

- **LLM**: Claude Sonnet via `langchain-anthropic`
- **Session history**: Last 20 messages
- **Continuation detection**: `_is_student_answer()` detects follow-up answers
- **Return type**: `process_query()` returns dict with `output`, `pattern`, `heuristic`, `is_continuation`

## System Commands

| Command | Action |
|---------|--------|
| `help` | Show help |
| `patterns` | List available patterns |
| `status` | System status |
| `clear` | Clear conversation |
| `level <level>` | Set beginner/intermediate/advanced |

## Dependencies

- `langchain`, `langchain-anthropic`, `langgraph`
- `sympy`
- `streamlit`
- `python-dotenv`
