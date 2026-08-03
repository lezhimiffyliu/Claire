# Claire — Architecture

One application: an AI calculus tutor. Typed answers are graded by a symbolic
verifier and taught through a deterministic teaching loop. This document is the map
a new engineer reads first.

## Top-level layout

```
calculus/
├── backend/                 # the Python service (run everything from here)
│   ├── api.py               #   FastAPI app + composition root (uvicorn api:app)
│   ├── app/
│   │   ├── auth/            #   Supabase JWT verification (canonical identity)
│   │   ├── grading/        #   verifier (SymPy = ground truth), vision, grader
│   │   ├── content/        #   problem loading + pattern detection
│   │   ├── teaching/       #   mastery profile, recommender, roadmap, remediation
│   │   ├── integrations/   #   Stripe checkout, quota, mobile QR upload
│   │   ├── persistence/    #   SQLAlchemy models + engine/session (Postgres/Neon)
│   │   └── config.py       #   env-based secrets helper
│   ├── claire_core/         #   the canonical, tested teaching spine (see its README)
│   ├── alembic/             #   DB migrations
│   ├── benchmarks/          #   teaching-eval harness + answer evaluator
│   ├── problems/            #   curated UW exam problem JSON (loaded at runtime)
│   └── tests/               #   pytest suite (all green)
├── frontend/                # Vite + React app (Dashboard, ProblemPractice, onboarding)
├── data/uw/                 # UW exam source dataset (gitignored; see its README)
├── scripts/                 # offline utilities (incl. scripts/data/uw/ pipeline)
└── docs/
```

## Canonical request path (the whole app in one flow)

```
frontend/ (ProblemPractice.jsx)
  → api/attemptApi.js  (submitAttempt / continueTeaching; Supabase Bearer token)
        │
        ▼
POST /api/attempt            (backend/api.py) → claire_core.run_tutor_turn
POST /api/attempt/continue   (backend/api.py) → claire_core.run_teaching_turn
        │
        ▼
  verify (app/grading/verifier.py — SymPy, GROUND TRUTH)
    → load state / profile   (app/persistence + app/teaching)
    → TutorAgent.propose      (claire_core/agent.py — the only LLM layer)
    → state.enforce()         (claire_core/state.py — clamp to a legal action)
    → classify → advance → persist   (Postgres via SQLAlchemy; anon ⇒ in-memory)
    → recommend               (app/teaching/recommender_v2.py)
```

**The LLM proposes a teaching action; a deterministic policy (`enforce()`)
disposes.** So the tutor structurally cannot confirm a wrong answer, dump the full
solution on attempt one, or repeat a shallow hint. The loop is unit-testable with no
LLM and no DB. See `backend/claire_core/README.md` for the full contract.

## Authentication (Supabase)

- The frontend authenticates with **Supabase** (Google OAuth). `api/authToken.js`
  sends the Supabase session access token as a `Bearer` token.
- The backend verifies that token in `app/auth/api_auth.py` (`get_optional_auth` →
  `verify_jwt`, via the Supabase client). `/api/attempt*` resolve identity **only**
  from the verified token — never from a header/body field.
- **Authenticated** requests persist to Postgres; **anonymous** requests are graded
  but not persisted (in-memory/Null stores). Proven by
  `tests/test_api_attempt_persistence.py::test_supabase_authenticated_request_is_not_anonymous`.

> Auth (Supabase, who the user is) is separate from persistence (Postgres/Neon +
> Alembic, where attempts/mastery are stored). Supabase here is an identity provider,
> not the app database.

### Note on Clerk

An earlier migration toward Clerk was started and **removed** in this cleanup — it
was never wired (no `@clerk` package, no provider) and every request fell back to
Supabase anyway. Supabase is the single, working auth. Clerk remains only a possible
future direction; there is no dead Clerk code left in the app.

## Persistence

Postgres (Neon in prod, local Postgres in dev, in-memory SQLite in tests) via
SQLAlchemy 2.x. Schema is Alembic-managed (`backend/alembic/`, run from `backend/`).
Models live in `backend/app/persistence/`.

## What is deliberately NOT here (removed in the reduction)

The repo previously carried several parallel historical stacks; all were deleted (not
quarantined): the legacy Socratic agent (`/chat`, `claire_agent_old`), the semantic
tutor pipeline (`/api/tutor/respond`, `tutor/`, `agent/`), thread persistence
(`/api/claire/thread/*`), the Streamlit app and its coupling, Supabase Edge
Functions + SQL migrations, `archive/`/`_archive/`, and modules unreachable from the
canonical path (`question_bank`, `exam_context`, `sympy_tools`, `quota`, the
Streamlit auth module). There are **no compatibility shims** — the codebase is the
one current application.

## Known gap

There is currently **no Stripe webhook** in the backend (it was a Supabase Edge
Function that was removed). Checkout works (`/api/checkout`), but subscription
activation via webhook must be re-implemented in `backend/api.py` before Stripe goes
live. `app/integrations/quota.py`'s Pro check reads the Supabase `payments` table
directly.
