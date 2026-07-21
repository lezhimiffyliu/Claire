# `claire_core` — the agent spine

This is the **canonical, tested core** of Claire's tutoring agent. It exists to
replace the earlier sprawl (three disconnected agent stacks, an open feedback
loop, mock internals, zero tests) with one small, coherent, fully-tested module
that does the important thing correctly: **it closes the adaptive loop.**

Design rule: keep this package *small*. Everything here is either the state
machine, the agent, storage ports, or the orchestrator. New features attach to
these seams — they do not add new parallel stacks.

---

## The 5 modules

| Module | What it is | Depends on | LLM? | I/O? |
|--------|-----------|-----------|:----:|:----:|
| `state.py` | Domain models + the **enforcement state machine** | pydantic | no | no |
| `tools.py` | LangChain `@tool`s wrapping the SymPy verifier + heuristics | `verifier`, `pattern_tools` | no | no |
| `agent.py` | The **LLM layer**: `TutorAgent` (LangGraph) + `StubTutorAgent` | langchain, langgraph | yes | no |
| `persistence.py` | Storage **ports** (`AttemptStore`, `ProfileStore`) + in-memory impls | `student_profile_v2` | no | in-mem |
| `loop.py` | `run_tutor_turn()` — the **closed loop** orchestrator | all of the above + `verifier`, `recommender_v2` | via agent | via stores |

Plus `persistence_supabase.py` — production adapters for the same ports (RLS Supabase + `attempt_tracker`), swappable with no change to `loop.py`.

It reuses your genuinely-good existing assets rather than reinventing them:
`verifier.py` (SymPy ground truth), `student_profile_v2.py` (mastery memory),
`recommender_v2.py` (what-to-study-next), `pattern_tools.py` (heuristics).

---

## The states

Two enums drive everything (`state.py`):

**`SessionPhase`** — where one problem sits:
`AWAITING_ATTEMPT → GRADED → TEACHING → RESOLVED`

**`TutorAction`** — the mutually-exclusive moves the tutor can make:
`CONFIRM_CORRECT_AND_STOP · GIVE_HINT · GIVE_FEEDBACK · ASK_CLARIFICATION · SHOW_SOLUTION`

### The core safety property: *the LLM proposes, the verifier disposes*

The agent may *suggest* an action, but the SymPy verifier's grade is **ground
truth**. `enforce()` clamps the action to the legal set for that grade:

| Verifier grade | Legal actions | Default |
|----------------|---------------|---------|
| **correct** | `confirm_correct_and_stop` only | confirm |
| **incorrect** | hint / feedback / clarify / solution (never "confirm correct") | feedback |
| **uncertain** | clarify / hint | clarify |

So the tutor can never congratulate a wrong answer or keep quizzing a right one
— the exact bug the old (dead) orchestrator was meant to prevent but never
actually wired. Here it is a pure function with 11 unit tests.

---

## The data flow — one graded turn

```
run_tutor_turn(problem, attempt, user_id, workspace_id, agent, stores)
   │
   1. verify_answer()            ──►  Grade   (SymPy = ground truth)
   2. agent.decide()             ──►  TeachingDecision (proposed)
   3. enforce(decision, grade)   ──►  TeachingDecision (legal)
   4. attempt_store.record()     ──►  attempt_id      ★ WRITE SIDE — closes loop
   5. profile.record_attempt()
      profile_store.save()       ──►  mastery updated ★ WRITE SIDE
   6. recommend_problems_for_api ──►  next problems (now data-informed)
   │
   └─►  TutorTurnResult(grade, decision, phase, attempt_id, recommendations)
```

Steps 4–5 are the fix for the project's #1 gap. Previously nothing wrote
attempts back, so every student looked brand-new forever and all the
personalization starved. Now a single call persists the outcome and the *next*
recommendation reflects it.

---

## Usage

```python
from claire_core import (
    Problem, StudentAttempt, TutorAgent, run_tutor_turn,
    InMemoryAttemptStore, InMemoryProfileStore,
)

problem = Problem(
    id="q1", text="Find the derivative of x^3.",
    official_answer="3x^2", topic="derivatives",
    subtopic="power_rule", problem_type="derivative", course="124",
)

result = run_tutor_turn(
    problem=problem,
    attempt=StudentAttempt(problem_id="q1", answer="2*x"),
    user_id="u1", workspace_id="w1",
    agent=TutorAgent(),                 # or StubTutorAgent() for no-LLM
    attempt_store=InMemoryAttemptStore(),
    profile_store=InMemoryProfileStore(),
)
print(result.decision.action, result.decision.message)
print(result.recommendations)
```

For production, swap the stores:
```python
from claire_core.persistence_supabase import SupabaseAttemptStore, SupabaseProfileStore
```

Run the offline demo (no API key needed):
```bash
python -m claire_core.demo
```

---

## Tests

```bash
pytest tests/test_core_state.py tests/test_core_loop.py tests/test_core_agent.py
```

- `test_core_state.py` — pure enforcement machine (11 tests, no deps)
- `test_core_loop.py` — the **closed loop** with the real verifier + real
  profile + in-memory stores + stub agent (7 tests). Proves persistence and
  mastery update actually happen.
- `test_core_agent.py` — agent wiring offline; the one live-LLM test is skipped
  unless `ANTHROPIC_API_KEY` is set.

The LLM is never called in the default suite, so it is fast and deterministic.

---

## How to continue (roadmap)

Ordered by leverage. Each item attaches to an existing seam.

1. **Wire `run_tutor_turn` into the API.** Replace the ad-hoc grading in the
   mobile-upload handler (`api.py`, where `is_correct` is already computed) and
   `/chat` with a call to `run_tutor_turn` using the Supabase stores. This lights
   up recommendations, roadmap-state, and cross-session memory — all already
   built and currently starving for data.
2. **Retire the 3 old agent stacks.** Point `/chat`, `/api/claire/agent`, and
   `/api/tutor/respond` at `TutorAgent`, then delete `claire_agent_old.py` and
   collapse `tutor/pipeline.py` into this core.
3. **Real error-type classification.** Today `error_type` on wrong answers comes
   from the agent's self-report. Add a small classifier (concept/algebra/logic/
   careless) — the profile already tracks these counts and boosts on them.
4. **Real retrieval.** `tutor/retrieval.py` uses hash pseudo-embeddings over 10
   chunks. Replace with pgvector over the 760-problem corpus and expose it as a
   third agent tool.
5. **Swap the model layer.** `agent.py` is the only file that imports
   `langchain_anthropic`. Moving off LangChain (e.g. to the native SDK) touches
   this one file; `loop.py` and everything below are LLM-agnostic.
6. **Session state machine.** `SessionPhase` is defined but the multi-turn
   `TEACHING` loop (follow-up hints until resolved) isn't orchestrated yet —
   build it on top of `TutorAgent.chat()`.
```
