# Claire — Making Calculus Clear

> Upload your course materials. Practice with AI guidance. Ace your exam.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-ReAct_Agent-green.svg)](https://langchain.com/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://www.anthropic.com/)

## What is Claire?

**Claire** is an AI calculus tutor that learns from *your* course materials.

```
Upload past exams, notes, syllabus
         │
         ▼
┌─────────────────────────────────┐
│  Claire extracts problems       │
│  Detects patterns & difficulty  │
│  Links to solving strategies    │
└─────────────────────────────────┘
         │
         ▼
"Let's practice SP18 Midterm 2 Problem 5..."
```

Unlike generic tutors, Claire knows exactly what's on *your* exam.

## Features

| Feature | Description |
|---------|-------------|
| **PDF Upload** | Upload past exams, practice sets, lecture notes |
| **Smart Extraction** | Auto-extracts problems with source citations |
| **Category Labels** | Double Integral, Lagrange Multipliers, Chain Rule, etc. |
| **Difficulty Rating** | Easy / Medium / Hard based on problem analysis |
| **Pattern Teaching** | Teaches reusable solving strategies, not just answers |
| **Step-by-Step Guidance** | Socratic method — guides you through each step |

## Quick Start

```bash
# Clone
git clone https://github.com/lezhimiffyliu/Claire.git
cd Claire

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
echo "ANTHROPIC_API_KEY=your_key" > .env

# Run
streamlit run app.py
```

## How It Works

### 1. Upload Materials
Upload your PDFs (past exams, practice problems, notes). Claire extracts all calculus problems.

### 2. Browse Problems
Each problem shows:
- **Source**: "SP18 Midterm 2 Problem 5"
- **Categories**: `Double Integral` `Polar Coordinates`
- **Difficulty**: 🟢 Easy / 🟡 Medium / 🔴 Hard

### 3. Practice with Guidance
Ask Claire to help with any problem. She'll:
1. Identify the problem type
2. Explain the solving strategy
3. Guide you step-by-step
4. Ask you to try each step

```
You: "Let's do Problem 3"

Claire: "This is from SP18 Midterm 2 — a constrained optimization problem.

        We'll use Lagrange multipliers:
        1. Identify f(x,y) and constraint g(x,y) = c
        2. Set up ∇f = λ∇g
        3. Solve the system

        What's the objective function here?"
```

## Supported Problem Types

| Pattern | Topics |
|---------|--------|
| **Optimization** | Max/min, critical points, second derivative test |
| **Constrained Optimization** | Lagrange multipliers, boundary analysis |
| **Integration** | Double/triple integrals, polar/spherical coordinates |
| **Derivatives** | Chain rule, partial derivatives, gradients |
| **Related Rates** | Time-dependent problems |
| **Limits** | L'Hôpital's rule, indeterminate forms |

## Project Structure

```
Claire/
├── app.py              # Streamlit web UI
├── claire_agent.py     # ReAct agent with teaching prompt
├── question_bank.py    # Problem extraction & classification
├── exam_context.py     # Course material analysis
├── pattern_tools.py    # Pattern detection + heuristics
├── sympy_tools.py      # SymPy math verification
├── heuristics/         # Solving strategy templates
│   ├── optimization.md
│   ├── constrained_optimization.md
│   ├── integration.md
│   └── ...
└── tests/
```

## Tech Stack

- **Agent**: LangChain + LangGraph (ReAct)
- **LLM**: Claude Sonnet
- **Math**: SymPy
- **PDF**: PyMuPDF
- **UI**: Streamlit

## License

MIT License

---

**Claire** — *Calculus Cram*
