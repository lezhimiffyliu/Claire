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

_What is actually wired today. The canonical grading/teaching path is the
`claire_core` spine behind `POST /api/attempt`; the older stacks are quarantined
under `legacy/` (see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md))._

| Layer | Tech |
|-------|------|
| **LLM orchestration** | LangChain + `langchain-anthropic` + LangGraph (canonical `claire_core` spine). Native Anthropic SDK in the legacy stacks. |
| **Models** | Claude Sonnet for canonical grading/teaching; tiered Haiku→Sonnet→Opus routing in the legacy tutor pipeline. |
| **Vision** | Gemini (handwriting extraction, `app/grading/vision_analyzer.py`) |
| **Math verification** | SymPy — ground truth (`app/grading/verifier.py`) |
| **API** | FastAPI, `uvicorn api:app` (`api.py` is the composition root) |
| **Persistence** | Postgres (Neon in prod, local Postgres in dev, in-memory SQLite in tests) via SQLAlchemy 2.x + Alembic; local SQLite for usage/quota |
| **Auth** | Clerk (canonical `/api/attempt`, RS256 JWT via JWKS); Supabase JWT in legacy `/chat` + mobile upload |
| **Payments & quota** | Stripe checkout + usage quota (`app/integrations/`) |
| **Frontend** | Vite + React 18 + Tailwind + Framer Motion |
| **Math rendering** | KaTeX |
| **Storage** | Supabase (handwriting image storage) |
| **Deployment** | `Procfile: uvicorn api:app` (Heroku-style) |

---

## Architecture

Full detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The canonical graded
turn runs through the deterministic `claire_core` spine — **the LLM proposes a
teaching action, a deterministic policy (`enforce()`) disposes.**

```
Frontend (web/) — ProblemPractice.jsx → attemptApi.js (Clerk token)
     │
     ▼
POST /api/attempt            (api.py) → claire_core.run_tutor_turn
POST /api/attempt/continue   (api.py) → claire_core.run_teaching_turn
     │
     ▼
  verify (app/grading/verifier.py — SymPy, GROUND TRUTH)
    → load state / profile
    → TutorAgent.propose        (claire_core/agent.py — the only LLM layer)
    → state.enforce()           (claire_core/state.py — clamp to a legal action)
    → classify → advance → persist (SQLAlchemy; anon ⇒ in-memory)
    → recommend                 (app/learning/recommender_v2.py)
```

So the tutor structurally can't congratulate a wrong answer, dump the full solution
on attempt one, or repeat a shallow hint. The whole loop is unit-testable with no
LLM and no DB.

This is the **one** teaching path. Full map in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Project Structure

```
calculus/
├── backend/                 # Python service — run everything from here
│   ├── api.py               #   FastAPI app + composition root (uvicorn api:app)
│   ├── claire_core/         #   ★ canonical, tested teaching spine (verify → propose → enforce → persist)
│   ├── app/
│   │   ├── auth/            #   Supabase JWT verification (canonical identity)
│   │   ├── grading/        #   verifier (SymPy = ground truth), vision_analyzer, grader
│   │   ├── content/        #   problem_loader, pattern_tools
│   │   ├── teaching/       #   student profile, recommender, roadmap, remediation
│   │   ├── integrations/   #   stripe_checkout, quota, mobile_upload
│   │   └── persistence/    #   SQLAlchemy models + engine (Postgres/Neon)
│   ├── alembic/             #   schema migrations
│   ├── benchmarks/          #   teaching-eval harness + answer evaluator
│   ├── problems/            #   curated UW exam problem JSON (loaded at runtime)
│   └── tests/               #   pytest suite (all green)
├── frontend/                # Vite + React (Dashboard, ProblemPractice, onboarding)
├── data/uw/                 # UW exam source dataset (gitignored; see data/uw/README.md)
├── scripts/                 # offline utilities (scripts/data/uw/ = the data pipeline)
└── docs/ARCHITECTURE.md     # canonical request path + package map
```

There are no parallel/legacy stacks and no compatibility shims — this is the single
current application. Auth is **Supabase**; persistence is **Postgres/Neon + Alembic**.

---

## Run Locally

**Backend** (one command to serve):

```bash
cd backend
python -m venv venv && source venv/bin/activate   # first time
pip install -r requirements.txt                   # first time
# .env: ANTHROPIC_API_KEY, GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
uvicorn api:app --reload --port 8000
```

**Frontend** (one command to serve):

```bash
cd frontend
npm install        # first time
npm run dev
```

Tests: `cd backend && pytest`.

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
