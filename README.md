# ∫ Claire — Making Calculus Clear

> An AI-powered Socratic calculus tutor built with LangChain ReAct agents, Claude Sonnet, and SymPy.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-ReAct_Agent-green.svg)](https://langchain.com/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- <p align="center">
  <img src="docs/demo.gif" alt="Claire Demo" width="700"/>
</p> -->

## 🎯 The Problem

Traditional calculus tutoring tools fall into two extremes:
- **Calculators** (Wolfram Alpha, Symbolab): Give answers instantly, but students don't learn
- **Static tutorials**: Explain concepts, but can't adapt to individual questions

**Claire bridges this gap** — an AI tutor that *guides* students through problems using the Socratic method, never giving direct answers but asking the right questions to build understanding.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎓 **Socratic Teaching** | Guides with questions instead of giving answers |
| 🧠 **ReAct Reasoning** | Visible thought process: Thought → Action → Observation |
| 📐 **Symbolic Math** | Exact calculus via SymPy (derivatives, integrals, limits) |
| 🎚️ **Adaptive Levels** | Beginner / Intermediate / Advanced difficulty |
| 🌐 **Bilingual** | Responds in English or Chinese based on input |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│              (Streamlit Web UI / CLI)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ClaireAgent                               │
│         LangGraph ReAct Agent + Socratic Prompt              │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Claude    │   │   SymPy     │   │  Knowledge  │
│   Sonnet    │   │   Tools     │   │    Base     │
│ (Reasoning) │   │   (Math)    │   │ (Concepts)  │
└─────────────┘   └─────────────┘   └─────────────┘
```

### Why This Architecture?

| Decision | Reasoning |
|----------|-----------|
| **LangChain ReAct** | Separates reasoning (LLM) from computation (tools) — more reliable than pure LLM math |
| **Claude Sonnet** | Best balance of reasoning quality and cost; excels at following complex prompts |
| **SymPy Tools** | Symbolic computation guarantees mathematical correctness |
| **Socratic Prompt** | Pedagogically proven method; forces guidance over answers |

## 🛠️ Tech Stack

- **Agent Framework**: LangChain + LangGraph (ReAct pattern)
- **LLM**: Claude Sonnet (Anthropic)
- **Math Engine**: SymPy (symbolic computation)
- **Web UI**: Streamlit
- **Language**: Python 3.11+

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/lezhimiffyliu/Claire.git
cd Claire

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
```

## 💡 How It Works

### Example Interaction

**Student**: "What is the derivative of x³?"

**Claire** (internally uses `calculate_derivative` tool, gets `3x²`):

> Great question! You're looking at a polynomial function $f(x) = x^3$.
>
> When we take derivatives of polynomial terms, there's a specific rule that applies here. Looking at the exponent 3, what operation do you think we need to perform with it?
>
> 💡 Hint: Think about what the power rule says about exponents...
>
> Give it a try and let me know what you get!

### The ReAct Loop

```
Question: "Find the integral of sin(x)"
    │
    ▼
Thought: "I should calculate this integral to guide the student"
    │
    ▼
Action: calculate_integral("sin(x)", "x")
    │
    ▼
Observation: "Result: -cos(x) + C"
    │
    ▼
Thought: "Now I'll guide the student toward this answer"
    │
    ▼
Final Answer: [Socratic guidance without revealing -cos(x)]
```

## 📁 Project Structure

```
claire/
├── app.py              # Streamlit web interface
├── main.py             # CLI entry point
├── claire_agent.py     # LangChain ReAct agent core
├── sympy_tools.py      # @tool decorated math functions
├── knowledge_loader.py # Embedded calculus knowledge base
├── requirements.txt    # Dependencies
└── tests/              # Unit tests (pytest)
```

## 🎓 Learning Outcomes

Building Claire taught me:

1. **LLM Agent Design** — How to architect systems where LLMs reason and tools execute
2. **Prompt Engineering** — Crafting prompts that enforce specific behaviors (Socratic method)
3. **Symbolic Math** — Integrating SymPy for reliable mathematical computation
4. **Tool Abstraction** — Designing clean interfaces between LLM reasoning and external tools

## 📈 Future Roadmap

- [ ] Multi-step problem solving with memory
- [ ] Step-by-step solution visualization
- [ ] Practice problem generation
- [ ] Learning progress tracking
- [ ] PDF export of solutions

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Claire — Making Calculus Clear</b><br>
  Built using LangChain, Claude, and SymPy
</p>
