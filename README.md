<p align="center">
  <img src="https://img.shields.io/badge/📐_Claire-Calculus_Cram-blue?style=for-the-badge" alt="Claire"/>
</p>

<h1 align="center">Claire</h1>
<p align="center"><strong>Making Calculus Clear</strong></p>

<p align="center">
  <a href="https://claire101.ai">
    <img src="https://img.shields.io/badge/🚀_Try_it_Live-claire101.ai-FF4B4B?style=for-the-badge" alt="Live Demo"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Sonnet_4-orange.svg" alt="Claude"/>
  <img src="https://img.shields.io/badge/LangChain-ReAct-green.svg" alt="LangChain"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT"/>
</p>

---

## ✨ What is Claire?

**Claire** is an AI calculus tutor that learns from *your* course materials and teaches you how to solve problems — not just the answers.

```
📄 Upload past exams     →     🔍 Claire extracts problems     →     🎯 Practice with guidance
```

Unlike generic AI tutors, Claire knows exactly what's on **your** exam.

---

## 🎮 Features

| | Feature | Description |
|---|---------|-------------|
| 📋 | **Placement Test** | Quick diagnostic to find your level |
| 📄 | **PDF Upload** | Upload past exams, notes, practice sets |
| 🏷️ | **Smart Labels** | Auto-tags: `Double Integral` `Lagrange` `Chain Rule` |
| 📊 | **Difficulty Rating** | 🟢 Easy · 🟡 Medium · 🔴 Hard |
| 🎓 | **Socratic Teaching** | Teaches formulas first, then guides you step-by-step |
| 💾 | **Session Persistence** | Refresh the page? Your progress is saved! |

---

## 🚀 Try It Now

### Option 1: Use Online (Recommended)
👉 **[claire101.ai](https://claire101.ai)**

No installation needed. Just upload your materials and start practicing.

### Option 2: Run Locally

```bash
git clone https://github.com/lezhimiffyliu/Claire.git
cd Claire
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key" > .env
streamlit run app.py
```

---

## 📖 How It Works

### 1️⃣ Take the Placement Test
Quick 5-question diagnostic to assess your calculus level.

### 2️⃣ Upload Your Materials
Drop in PDFs of past exams, practice problems, or lecture notes. Claire extracts every problem with:
- Source citation: *"SP18 Midterm 2 Problem 5"*
- Categories: `Optimization` `Polar Coordinates`
- Difficulty: Easy / Medium / Hard

### 3️⃣ Practice with Guidance

```
You: "Let's do Problem 3"

Claire: "This is a constrained optimization problem.

        📝 Key formula (memorize this!):
        D = f_xx · f_yy - (f_xy)²

        • D > 0 and f_xx > 0 → minimum
        • D > 0 and f_xx < 0 → maximum
        • D < 0 → saddle point

        Now, compute D with the given values. What do you get?"
```

Claire teaches the **method**, not just the answer.

---

## 🧠 Supported Topics

| Category | Topics |
|----------|--------|
| **Optimization** | Critical points, second derivative test, Hessian |
| **Constrained Optimization** | Lagrange multipliers, boundary analysis |
| **Integration** | Double/triple integrals, polar, spherical, cylindrical |
| **Derivatives** | Chain rule, partial derivatives, gradients |
| **Related Rates** | Time-dependent problems |
| **Limits** | L'Hôpital's rule, indeterminate forms |

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|------------|
| **AI Agent** | LangChain + LangGraph (ReAct) |
| **LLM** | Claude Sonnet 4 |
| **Math Engine** | SymPy |
| **PDF Parser** | PyMuPDF |
| **Frontend** | Streamlit |
| **Deployment** | Streamlit Cloud |

---

## 📁 Project Structure

```
Claire/
├── app.py                 # Streamlit UI
├── claire_agent.py        # ReAct teaching agent
├── placement_test.py      # Diagnostic test
├── session_store.py       # Session persistence
├── question_bank.py       # Problem extraction
├── pattern_tools.py       # Pattern detection
├── heuristics/            # Solving templates
│   ├── optimization.md
│   ├── integration.md
│   └── ...
└── tests/
```

---

## 📜 License

MIT License — use it, fork it, improve it.

---

<p align="center">
  <strong>Claire</strong> — <em>Calculus Cram</em>
  <br>
  Made with ❤️ for students who want to actually learn
</p>
