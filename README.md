<p align="center">
  <img src="https://img.shields.io/badge/📐_Claire-Calculus_Tutor-blue?style=for-the-badge" alt="Claire"/>
</p>

<h1 align="center">Claire</h1>
<p align="center"><strong>AI calculus tutor that teaches UW students step-by-step using real past exam problems, with phone-based handwriting grading.</strong></p>

<p align="center">
  <a href="https://claire101.ai">
    <img src="https://img.shields.io/badge/🚀_Try_it_Live-claire101.ai-FF4B4B?style=for-the-badge" alt="Live Demo"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Haiku_|_Sonnet_|_Opus-orange.svg" alt="Claude"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688.svg" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Supabase-Auth_+_Storage-3ECF8E.svg" alt="Supabase"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT"/>
</p>

---

## What is Claire?

Most students cram for calc exams by re-reading notes or hoping ChatGPT explains it well enough. Claire is different.

**Claire teaches you step-by-step through real UW exam problems using Socratic dialogue. When you're stuck, she guides you — never just gives the answer. Upload your handwritten work via phone camera and get instant feedback.**

---

## Features

### 📚 Real UW Exam Problem Bank
86 past exams from Math 124/125/126 (2018-2025). Every problem has source citation ("Au24 Final Q5"), topic labels, and difficulty rating.

### 🧑‍🏫 Socratic Teaching
Claire never dumps the answer. She teaches the method first, then guides you through each step:
- "I'm stuck" → Claire gives the next micro-step, not the full solution
- Wrong answer → Claire identifies the error type and hints at the fix
- Correct → Claire confirms and moves to the next part

### 📱 Handwriting Grading via Phone
Scan QR → snap photo of your work → instant grading:
- **Gemini Vision** extracts your handwritten math
- **SymPy** verifies correctness mathematically
- Claire explains where you went wrong (if needed)

### 🎯 Adaptive Difficulty
5-minute diagnostic identifies your level:
- 🌱 **Building Foundations** — needs basics review
- 📈 **Exam Ready** — knows concepts, needs practice
- 🏆 **4.0 Candidate** — ready for hard problems

### 🧠 Multi-Model Intelligence
| Model | Role |
|-------|------|
| **Haiku** | Fast intent classification (< 100ms) |
| **Sonnet** | Response generation, teaching dialogue |
| **Opus** | Complex reasoning: answer verification, strategic teaching decisions |

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **LLM Orchestration** | Native Anthropic SDK (no LangChain) |
| **Models** | Claude Haiku → Sonnet → Opus (tiered routing) |
| **Vision** | Gemini Flash (handwriting OCR) |
| **Math Verification** | SymPy |
| **API** | FastAPI + SQLite (rate limiting, thread persistence) |
| **Frontend** | Vite + React 18 + Tailwind + Framer Motion |
| **Math Rendering** | KaTeX |
| **Auth & Storage** | Supabase (Google OAuth, image storage) |
| **Deployment** | Heroku (API) |

---

## Architecture

```
Student message
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  tutor/pipeline.py — Main orchestration                     │
├─────────────────────────────────────────────────────────────┤
│  1. response_cache.py  → Check semantic cache (skip LLM?)   │
│  2. classifier.py      → Haiku: intent + concept + language │
│  3. retrieval.py       → Search teaching chunks (mock/pgvector) │
│  4. strategist.py      → Decide: Sonnet or Opus?            │
│  5. adapter.py         → Sonnet: generate response          │
│     └─ OR teaching_planner.py → Opus: complex teaching      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
  Claire response (say / ask_back / concept_card)
```

### When does Opus activate?

| Trigger | Why |
|---------|-----|
| `check_answer` intent | Need to verify correctness |
| `ask_next_step` intent | Need teaching path decision |
| Low retrieval score | No good teaching chunks found |
| Student confused 3+ times | Need better strategy |
| Low classification confidence | Uncertain intent |

---

## Project Structure

```
Claire/
├── api.py                  # FastAPI backend (chat, mobile upload, recommendations)
├── tutor/                  # Teaching pipeline (Phase 5)
│   ├── pipeline.py         # Main orchestration
│   ├── classifier.py       # Haiku: intent/concept classification
│   ├── retrieval.py        # Teaching chunk search (mock embedding)
│   ├── strategist.py       # Sonnet vs Opus routing
│   ├── adapter.py          # Sonnet: response generation
│   ├── teaching_planner.py # Task-based Socratic actions
│   └── response_cache.py   # Semantic caching
├── agent/                  # Native Anthropic SDK agent
│   ├── claire_agent.py     # Multi-model orchestration
│   ├── prompts.py          # System prompts
│   └── teaching_tools.py   # Tool schemas + execution
├── problems/               # 86 UW exam JSON files (Math 124/125/126)
├── web/                    # Vite + React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── claire/     # TutorThread, WorkAreaCard, ClairePanel
│   │   │   ├── dashboard/  # Dashboard, ProblemPractice
│   │   │   └── onboarding/ # Diagnostic flow
│   │   ├── context/        # AuthContext, ClaireContext
│   │   └── api/            # chatApi, mobileUploadApi, supabaseApi
│   └── package.json
├── vision_analyzer.py      # Gemini Vision: handwriting extraction
├── verifier.py             # SymPy: answer verification
├── mobile_upload.py        # QR session management
├── problem_loader.py       # Load problems from JSON
└── Procfile                # Heroku deployment
```

---

## Run Locally

```bash
git clone https://github.com/yourusername/Claire.git
cd Claire

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=...

# Start API
uvicorn api:app --reload --port 8000

# Frontend (new terminal)
cd web
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Supported Topics

**Calc I** · Derivatives · Chain Rule · Implicit Differentiation · Related Rates · Optimization · L'Hôpital's Rule

**Calc II** · U-Substitution · Integration by Parts · Partial Fractions · Trig Sub · Improper Integrals · Volumes · Arc Length · Series · Taylor/Maclaurin

**Calc III** · Partial Derivatives · Gradient · Directional Derivatives · Lagrange Multipliers · Double/Triple Integrals · Polar/Cylindrical Coordinates

---

## License

MIT

---

<p align="center">
  <strong>Claire</strong> — AI calculus tutor with real UW exam problems and Socratic teaching.
  <br>
  <a href="https://claire101.ai">claire101.ai</a>
</p>
