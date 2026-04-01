<p align="center">
  <img src="https://img.shields.io/badge/📐_Claire-Calculus_Cram-blue?style=for-the-badge" alt="Claire"/>
</p>

<h1 align="center">Claire</h1>
<p align="center"><strong>Your AI study partner for calculus exam week.</strong></p>

<p align="center">
  <a href="https://claire101.ai">
    <img src="https://img.shields.io/badge/🚀_Try_it_Live-claire101.ai-FF4B4B?style=for-the-badge" alt="Live Demo"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Sonnet_4-orange.svg" alt="Claude"/>
  <img src="https://img.shields.io/badge/LangChain-ReAct-green.svg" alt="LangChain"/>
  <img src="https://img.shields.io/badge/Streamlit-Cloud-red.svg" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT"/>
</p>

---

## What is Claire?

Most students cram for calc exams by re-reading notes or hoping ChatGPT explains it well enough. Claire is different.

**Upload your actual past exams and lecture notes. Claire reads them, figures out what your professor tests the most, diagnoses where you're weak, and then guides you through exactly those problems — step by step, at your level.**

It's not a chatbot. It's a study system built around your specific exam.

---

## How it works

```
1. Upload your materials (past exams, notes, syllabus)
          │
          ▼
2. Take a 5-minute diagnostic
   Claire figures out if you're:
   🌱 Shaky on fundamentals
   📚 Know basics, but make method errors
   🚀 Strong — just need speed and pattern recognition
          │
          ▼
3. Get a personalized practice queue
   Problems ranked by: weak topics × exam frequency × point value
          │
          ▼
4. Practice with step-by-step guidance
   Claire teaches the method, not just the answer
   Language adapts to your level automatically
```

---

## Features

### 🎯 Diagnostic — Know Where You Stand
5 multiple-choice questions, ~5 minutes. Uses your actual uploaded materials when available. Identifies weak topics across 20+ calculus subjects (u-substitution, Lagrange multipliers, series convergence, double integrals…).

### 🚨 Exam Panic Mode
Upload your past exams → Claire instantly tells you:
- Which topics appear most (these are almost certainly on your exam)
- What to study first given how many days you have left
- Quick-reference solving steps for each high-frequency topic

### 📚 Smart Problem Bank
Claire extracts every problem from your PDFs with source citations ("SP18 Midterm 2, Problem 5"), labels by topic and difficulty, and ranks them based on your diagnostic results.

### 🧑🏫 Adaptive Teaching
Claire never just gives you the answer. She teaches the method first, then guides you to apply it — using language calibrated to your level:
- **Beginner**: plain words, intuition-first, analogies, every step explained
- **Intermediate**: method selection, common traps, guided reasoning
- **Advanced**: concise, strategy-focused, pattern recognition drills

### 💾 Session Persistence
Your materials, diagnostic results, and progress are saved automatically. Refresh the page, come back tomorrow — everything's still there. No account required.

### 🔄 Model Tiering
First 5 queries use Claude Sonnet (premium). Subsequent queries automatically switch to DeepSeek — still solid, just faster and free. Optional upgrade for continued Claude access.

---

## Try it now

👉 **[claire101.ai](https://claire101.ai)** — no installation, no account required.

Upload any calc PDF and see how it works in under 2 minutes.

---

## Run locally

```bash
git clone https://github.com/lezhimiffyliu/Claire.git
cd Claire

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your keys
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "DEEPSEEK_API_KEY=sk-..." >> .env

streamlit run app.py
```

Open `http://localhost:8501`.

---

## Supported topics

Calc I · Calc II · Calc III across:

Derivatives · Chain Rule · Implicit Differentiation · Related Rates · Optimization · Critical Points · L'Hôpital's Rule · U-Substitution · Integration by Parts · Partial Fractions · Trig Substitution · Improper Integrals · Volume (Disk/Shell) · Arc Length · Series Convergence · Power Series · Taylor/Maclaurin Series · Partial Derivatives · Gradient · Directional Derivatives · Lagrange Multipliers · Double Integrals · Triple Integrals · Green's Theorem · Stokes' Theorem

---

## Tech stack

| Layer | Tech |
|-------|------|
| AI Agent | LangChain + LangGraph (ReAct) |
| LLMs | Claude Sonnet 4 (premium) + DeepSeek (base) |
| Math Engine | SymPy |
| PDF Parser | PyMuPDF |
| Topic Detection | Custom LLM-based classifier (20+ topics) |
| Frontend | Streamlit |
| Auth | Google OAuth via Supabase |
| Session Storage | URL-keyed JSON + Supabase |
| Deployment | Streamlit Cloud → claire101.ai |

---

## Project structure

```
Claire/
├── app.py                  # Main UI — all screens and routing
├── claire_agent.py         # Adaptive ReAct teaching agent
├── placement_test.py       # Diagnostic quiz + scoring + topic tracking
├── exam_panic.py           # Exam Panic Mode — cram plan generator
├── exam_mode.py            # Exam simulation (timed, scored)
├── exam_parser.py          # PDF exam extraction + problem parsing
├── question_bank.py        # Problem bank with source citations
├── exam_context.py         # Uploaded materials context manager
├── session_store.py        # Session persistence (URL-based)
├── quota.py                # Usage quota (anon + logged-in tiers)
├── practice_planner.py     # Problem prioritization by weak topics
├── topics/
│   ├── topic_detector.py   # LLM-based fine-grained topic classification
│   ├── heuristic_loader.py # Maps topics → solving strategy templates
│   └── calculus_topics.md  # Topic taxonomy
├── heuristics/             # Solving strategy templates per topic
│   ├── optimization.md
│   ├── u_substitution.md
│   ├── integration_by_parts.md
│   ├── lagrange_multipliers.md
│   └── ...
└── tests/
```

---

## License

MIT — use it, fork it, build on it.

---

<p align="center">
  <strong>Claire</strong> — Built for students who have a week and need to make it count.
  <br>
  <a href="https://claire101.ai">claire101.ai</a>
</p>
