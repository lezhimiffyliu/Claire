# Claire — Making Calculus Clear

> Upload your course materials. Take a quick diagnostic. Practice smarter. Ace your exam.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-ReAct_Agent-green.svg)](https://langchain.com/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://www.anthropic.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b.svg)](https://streamlit.io/)

## What is Claire?

**Claire** is an AI calculus tutor built for exam prep. Upload your course materials (past exams, lecture notes, syllabus), take a 5-minute diagnostic, and Claire will guide your practice based on where you actually need help — not a generic curriculum.

```
Upload past exams + notes
         │
         ▼
5-minute diagnostic quiz
(5 multiple-choice questions)
         │
         ▼
Claire knows your weak spots
Prioritizes practice problems by:
  · Your weak topics
  · Problem frequency across exams
  · Point values
         │
         ▼
Step-by-step guided practice
(adapts language to your level)
```

## Features

### 🎯 Adaptive Diagnostic
- 5 multiple-choice questions, ~5 minutes
- Covers your actual uploaded materials (or standard Calc I/II/III if no upload)
- Identifies 3 student profiles: **Foundations need work** / **Basics but shaky** / **Strong, needs speed**
- Tracks weak topics (Derivatives, Integration, Lagrange Multipliers, etc.)

### 📂 Smart Material Upload
- Upload PDFs, TXT, or Markdown files (past exams, notes, syllabus)
- Auto-extracts problems with source citations (e.g. "SP18 Midterm 2 Problem 5")
- Labels by category (Double Integral, Polar Coordinates, Chain Rule…) and difficulty (🟢🟡🔴)

### 📊 Practice Prioritization
After the diagnostic, Claire ranks your uploaded problems by:
1. **Weak topic match** — problems in areas you got wrong come first
2. **Exam frequency** — topics that appear across multiple past exams = higher weight on your real exam
3. **Point value** — high-point problems surface to the top

### 🧑‍🏫 Level-Adaptive Teaching
- **Beginner**: plain language, intuition-first, every step explained, analogies
- **Intermediate**: method selection, common traps, guided reasoning
- **Advanced**: concise, strategy-focused, pattern recognition, exam speed

### 💾 Session Persistence
Your uploaded materials, diagnostic results, and practice queue are saved automatically. Refresh the page — everything's still there. Bookmark the URL (`?s=your-session-id`) to restore your session on any device.

## Quick Start

```bash
git clone https://github.com/lezhimiffyliu/Claire.git
cd Claire

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "ANTHROPIC_API_KEY=your_key_here" > .env

streamlit run app.py
```

Open `http://localhost:8501` — you're in.

## How It Works

### 1. Upload (optional but recommended)
Upload your PDFs. Claire extracts every problem, labels it by topic and difficulty, and builds a searchable practice bank.

### 2. Diagnostic
5 questions, 5 minutes. Claire figures out whether you're:
- Shaky on fundamentals (will explain everything from scratch)
- Know the basics but make method errors (will focus on strategy)
- Solid but need speed (will drill patterns and edge cases)

### 3. Practice
Claire shows a prioritized list of problems from your materials. Click any problem and she'll guide you step-by-step via Socratic dialogue — asking questions, giving hints, never just handing you the answer.

```
You: "Let's do Problem 3"

Claire: "This is from SP18 Midterm 2 — constrained optimization.

        We'll use Lagrange multipliers. Here's the setup:
          ∇f = λ∇g, plus the constraint g(x,y) = c

        What's the objective function f(x,y) in this problem?"
```

## Supported Problem Types

| Pattern | Topics Covered |
|---------|---------------|
| **Optimization** | Max/min, critical points, second derivative test, closed interval method |
| **Constrained Optimization** | Lagrange multipliers, boundary analysis |
| **Integration** | u-sub, integration by parts, partial fractions, double/triple integrals |
| **Derivatives** | Chain rule, product/quotient rule, implicit, partial derivatives |
| **Related Rates** | Time-dependent geometric problems |
| **Limits** | L'Hôpital's rule, standard limits, indeterminate forms |
| **Series** | Convergence tests, power series, radius of convergence |
| **Multivariable** | Gradient, directional derivatives, polar/cylindrical/spherical coordinates |

## Project Structure

```
Claire/
├── app.py                # Streamlit UI + diagnostic flow
├── claire_agent.py       # ReAct agent — adaptive teaching prompt
├── placement_test.py     # Diagnostic questions + scoring + topic tracking
├── practice_planner.py   # Problem prioritization (weak topics × frequency × points)
├── session_store.py      # URL-based session persistence (no login required)
├── question_bank.py      # PDF extraction + problem classification
├── exam_context.py       # Course material analysis
├── pattern_tools.py      # Pattern detection + heuristic loading
├── sympy_tools.py        # SymPy math verification tools
├── api.py                # FastAPI backend (rate-limited API endpoint)
├── heuristics/           # Solving strategy templates per topic
│   ├── optimization.md
│   ├── constrained_optimization.md
│   ├── integration.md
│   ├── derivatives.md
│   ├── limits.md
│   └── related_rates.md
└── tests/
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent** | LangChain + LangGraph (ReAct) |
| **LLM** | Claude Sonnet (Anthropic) |
| **Math** | SymPy |
| **PDF parsing** | PyMuPDF |
| **UI** | Streamlit |
| **API** | FastAPI + SQLite (rate limiting) |
| **Session** | JSON files + URL session ID |

## Roadmap

- [ ] User accounts (Google / Apple / Email sign-in)
- [ ] Free tier (DeepSeek) + paid tier (Claude) model routing
- [ ] School-specific question banks (NYU, Columbia…)
- [ ] Timed practice mode (exam simulation)
- [ ] Progress tracking across sessions

## License

MIT License

---

*Built for students who have a week to prepare and need to make it count.*
