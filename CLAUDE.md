# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Claire** is an AI calculus tutor that learns from students' course materials. It extracts problems from uploaded PDFs, detects patterns, and teaches solving strategies step-by-step.

**Key features:**
- PDF upload → auto-extract problems with source citations
- Smart labels: categories (Double Integral, Lagrange, etc.) + difficulty
- Pattern-based teaching with heuristic templates
- Socratic guidance, not direct answers

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run Web UI
streamlit run app.py

# Run tests
pytest tests/

# Run CLI (legacy)
python3 main.py
```

## Architecture

```
PDF Upload
     │
     ▼
┌─────────────────┐
│ question_bank.py│  ← Extract problems, detect categories/difficulty
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ exam_context.py │  ← Analyze materials, build question bank
└────────┬────────┘
         │
         ▼
User selects problem
         │
         ▼
┌─────────────────┐
│ detect_pattern()│  ← Classify problem type
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ get_heuristic() │  ← Load solving template
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ReAct Agent   │  ← Claude + SymPy tools
└────────┬────────┘
         │
         ▼
   Guided Response
```

## Core Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit web UI with problem browser |
| `claire_agent.py` | ReAct agent with teaching prompt |
| `question_bank.py` | Problem extraction, categories, difficulty |
| `exam_context.py` | Course material analysis |
| `pattern_tools.py` | Pattern detection + heuristic retrieval |
| `sympy_tools.py` | SymPy math tools |
| `heuristics/*.md` | Markdown solving templates |

## Question Bank

`question_bank.py` handles:

- **PDF extraction**: PyMuPDF for text extraction
- **Problem parsing**: Regex patterns for "Problem 1", "Q2", etc.
- **Category detection**: Auto-detect topics like "Double Integral", "Lagrange Multipliers"
- **Difficulty estimation**: Easy/Medium/Hard based on text analysis

Key class:
```python
@dataclass
class Question:
    id: str                 # Hash ID
    text: str               # Full problem text
    source: str             # Filename
    problem_id: str         # "Problem 1", "Q2"
    pattern: str            # optimization, integration, etc.
    categories: list        # ["Double Integral", "Polar Coordinates"]
    difficulty: str         # easy, medium, hard
```

## Pattern Detection

`detect_pattern()` classifies problems into 6 types:

| Pattern | Keywords |
|---------|----------|
| `optimization` | maximize, minimize, largest, smallest |
| `constrained_optimization` | subject to, constraint, Lagrange |
| `related_rates` | rate of change, how fast, per second |
| `derivatives` | derivative, d/dx, differentiate |
| `integration` | integral, antiderivative, ∫ |
| `limits` | limit, approaches, L'Hôpital |

## Category Labels

User-friendly labels detected from problem text:

- Double Integral, Triple Integral
- Polar Coordinates, Spherical Coordinates
- Lagrange Multipliers
- Chain Rule, Product Rule, Quotient Rule
- Partial Derivatives, Gradient
- Taylor Series, U-Substitution, Integration by Parts
- And more...

## Heuristic Files

Located in `heuristics/` directory. Each contains:
- Pattern recognition tips
- Decision tree
- Solving template (numbered steps)
- Common mistakes

## Agent Behavior

The system prompt enforces:

1. **Use loaded materials** - Access problems directly, cite sources
2. **Pattern teaching** - Explain problem type and strategy
3. **Step-by-step guidance** - Guide through each step
4. **Socratic questions** - Ask student to try each step
5. **No direct answers** - Teach the method, not the result

## UI Components

- **Sidebar**: File upload, problem list with View buttons
- **Problem dialog**: Full text, categories, difficulty, Practice button
- **Chat**: Main conversation area
- **IME handling**: JavaScript for Chinese input composition

## Key Implementation Details

- **LLM**: Claude Sonnet via `langchain-anthropic`
- **PDF**: PyMuPDF (`fitz`)
- **Session history**: Last 20 messages
- **Continuation detection**: `_is_student_answer()` detects follow-up answers

## Dependencies

- `langchain`, `langchain-anthropic`, `langgraph`
- `sympy`
- `streamlit`
- `pymupdf`
- `python-dotenv`
