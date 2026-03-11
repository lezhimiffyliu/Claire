# Claire 2.0 — Calculus Exam Preparation Agent

> AI-powered exam prep that teaches problem-solving **patterns**, not just solutions.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-ReAct_Agent-green.svg)](https://langchain.com/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://www.anthropic.com/)

## The Problem

Most AI tutors work like this:
```
Student asks problem → AI gives answer
```

This doesn't help students **learn**. On exam day, they're stuck.

**Claire works differently:**
```
Problem → Pattern Detection → Heuristic Template → Step-by-step Guidance
```

Claire teaches **reusable solving strategies**, so students can tackle any problem of the same type.

## Core Concept

```
┌─────────────────────────────────────────────────────────┐
│  "Maximize xy subject to x + 2y = 10"                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Pattern: Constrained Optimization                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Heuristic Template:                                     │
│  1. Identify objective f(x,y) and constraint g(x,y)=c   │
│  2. Set up Lagrange system: ∇f = λ∇g                    │
│  3. Solve 3 equations for x, y, λ                       │
│  4. Evaluate and compare                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  "Let's start with Step 1.                               │
│   What is the objective function in your problem?"       │
└─────────────────────────────────────────────────────────┘
```

## Features

| Feature | Description |
|---------|-------------|
| **Pattern Detection** | Automatically classifies problems (optimization, related rates, etc.) |
| **Heuristic Library** | Markdown-based solving templates for each pattern |
| **Guided Teaching** | Step-by-step guidance with questions, not direct answers |
| **SymPy Verification** | Exact symbolic math when computation is needed |

## Supported Patterns

| Pattern | Example |
|---------|---------|
| `optimization` | "Find dimensions that maximize area" |
| `constrained_optimization` | "Maximize f(x,y) subject to g(x,y)=c" |
| `related_rates` | "How fast is the water level rising?" |
| `derivatives` | "Find the derivative of ln(x²+1)" |
| `integration` | "Integrate x·eˣ dx" |
| `limits` | "Find lim(sin x / x) as x→0" |

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

## Architecture

```
Problem Input
      │
      ▼
┌─────────────────┐
│ detect_pattern()│  ← Rule-based keyword matching
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ get_heuristic() │  ← Load markdown template
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ReAct Agent   │  ← Claude + SymPy tools
│  (Teaching Mode)│
└────────┬────────┘
         │
         ▼
   Guided Response
   (Pattern → Template → Steps → Questions)
```

## Project Structure

```
claire/
├── app.py              # Streamlit web UI
├── claire_agent.py     # ReAct agent with teaching prompt
├── pattern_tools.py    # Pattern detection + heuristic retrieval
├── sympy_tools.py      # SymPy math tools
├── heuristics/         # Markdown solving templates
│   ├── optimization.md
│   ├── constrained_optimization.md
│   ├── related_rates.md
│   ├── derivatives.md
│   ├── integration.md
│   └── limits.md
└── main.py             # CLI entry point
```

## Example Interaction

**Student:** "Find the maximum area of a rectangle with perimeter 20"

**Claire:**
> **Pattern:** Optimization
>
> **Heuristic Template:**
> - Set up objective function to maximize
> - Find derivative, set equal to zero
> - Solve for critical points
> - Use second derivative test
>
> **Let's Begin:**
> We need to set up our objective function first. Let's call the sides x and y.
>
> **Your Turn:**
> What expression represents the area A in terms of x and y?

**Student:** "A = xy"

**Claire:**
> Good! Now we need to use the constraint. The perimeter is 20, so 2x + 2y = 20.
>
> **Your Turn:**
> Can you solve for y in terms of x, so we can write A as a function of one variable?

## Tech Stack

- **Agent**: LangChain + LangGraph (ReAct)
- **LLM**: Claude Sonnet
- **Math**: SymPy
- **UI**: Streamlit
- **Language**: Python 3.11+

## License

MIT License

---

**Claire 2.0** — Teaching patterns, not just solutions.
