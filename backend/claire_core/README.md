# `claire_core` — the agent spine

This is the **canonical, tested core** of Claire's tutoring agent. It replaces
the earlier sprawl (three disconnected agent stacks, an open feedback loop, mock
internals, zero tests) with one small, coherent module that does the important
things correctly: **the math is decided deterministically, the teaching action
is chosen from a finite set and enforced, and every attempt writes back into the
student's mastery so the next problem adapts.**

Design rule: keep this package *small*. Everything here is either the state
machine, the classifier, the agent, storage ports, or the orchestrator. New
features attach to these seams — they do not add new parallel stacks.

---

## The three responsibilities

| Layer | Owns | Never does |
|-------|------|-----------|
| **Verifier** (`verifier.py`) | Is the answer correct? Symbolic/numeric equivalence. | Decide how to teach. |
| **Tutor Agent** (`agent.py`) | *Propose* a teaching action + message, given the grade, per-problem history, and mastery. | Override the verifier; touch storage. |
| **Orchestrator** (`loop.py`) | Fixed sequence: verify → decide → **enforce** → classify → persist → update mastery → recommend. | Let the LLM decide *whether* to persist. |

The agent proposes; a deterministic policy disposes. The write side (attempts,
mastery, teaching state) is executed by the orchestrator on every turn — it does
**not** depend on the LLM choosing to call a tool.

---

## The modules

| Module | What it is | LLM? | I/O? |
|--------|-----------|:----:|:----:|
| `state.py` | Domain models + the **enforcement state machine** (`enforce`) | no | no |
| `classify.py` | **Deterministic-first** error classifier (SymPy evidence → `MisconceptionType`) | no | no |
| `agent.py` | The **LLM layer**: `TutorAgent` + `StubTutorAgent` | yes | no |
| `persistence.py` | Storage **ports** + in-memory impls (`Attempt`/`Profile`/`TeachingState`) | no | in-mem |
| `loop.py` | `run_tutor_turn()` — the **closed loop** orchestrator | via agent | via stores |
| `tools.py` | LangChain `@tool`s for the (optional) ReAct `chat()` path | no | no |

Plus `persistence_sqlalchemy.py` — production adapters (Postgres/Neon, SQLAlchemy 2.x) for the same ports, swappable with no change to `loop.py`. Schema is managed by Alembic (`alembic/`, `db/`).

Reuses the genuinely-good existing assets: `verifier.py` (SymPy ground truth),
`student_profile_v2.py` (hierarchical mastery memory), `recommender_v2.py`
(what-to-study-next), `taxonomy/` (topic normalization).

---

## The state model

Four small, orthogonal enums (`state.py`) — deliberately not one mega-enum:

**`ProblemPhase`** — lifecycle of one problem:
`AWAITING_ATTEMPT → EVALUATING → TEACHING → RESOLVED` (or `ABANDONED`).
Grading is an *event*, not a phase.

**`GradeStatus`** — verifier verdict: `CORRECT · INCORRECT · UNVERIFIABLE`.

**`TutorAction`** — the mutually-exclusive moves (9):
`ASK_CLARIFICATION · IDENTIFY_ERROR · GIVE_HINT · EXPLAIN_CONCEPT ·
CHECK_INTERMEDIATE_STEP · SHOW_WORKED_EXAMPLE · SHOW_SOLUTION · CONFIRM_CORRECT ·
END_PROBLEM`.

**`HintLevel`** — hint depth, an escalation ladder:
`NONE → NUDGE → CONCEPT → NEXT_STEP → NEAR_SOLUTION → FULL_SOLUTION`.

**`MisconceptionType`** — `POWER_RULE_ERROR · CHAIN_RULE_OMISSION ·
PRODUCT_RULE_ERROR · ALGEBRA_ERROR · NOTATION_ERROR · CONCEPTUAL_CONFUSION ·
UNKNOWN`, mapped to the profile's coarse buckets (concept/algebra/careless).

**`TeachingState`** — per-problem memory that lets the *same* problem advance:
`attempt_count`, `hint_level`, `diagnosed_misconception`, `explained_concepts`,
`hints_given`, `actions_taken`, `last_action`, `last_question`, `used_hint`.

### The safety property: *the LLM proposes, the policy disposes*

`enforce(decision, grade, state)` is a pure function that clamps the agent's
proposed action to what is legal given **both** the grade and the teaching state:

| Situation | Rule |
|-----------|------|
| **Correct** | only `CONFIRM_CORRECT` / `END_PROBLEM` (never keep quizzing) |
| **Incorrect** | any teaching move except `CONFIRM_CORRECT` |
| **Unverifiable** | only `ASK_CLARIFICATION` / `GIVE_HINT` (never confirm, end, or reveal) |
| **Full solution** | gated: needs ≥ `SOLUTION_ATTEMPT_THRESHOLD` attempts *or* a near-solution hint already given |
| **Repeated hint** | force the hint level to escalate up the ladder |
| **Resolved / abandoned** | no further teaching — forced to `END_PROBLEM` |

So the tutor can't congratulate a wrong answer, keep drilling a right one, dump
the full solution on attempt one, or loop the same shallow hint. Each rule has
unit tests in `tests/test_core_state.py`.

---

## The data flow — one graded turn

```
run_tutor_turn(problem, attempt, user_id, workspace_id, agent, stores)
   │
   1. verify_answer()                 ──►  Grade   (SymPy = ground truth)
   2. state = load(); register_attempt()    (per-problem teaching memory)
   3. profile = load(); summarize for the agent
   4. agent.decide(problem, attempt, grade, state, summary)  ──► proposed
   5. enforce(proposed, grade, state) ──►  TeachingDecision (legal, escalated)
   6. classify_math_error()           ──►  MisconceptionType (deterministic-first,
                                            agent self-report only as fallback)
   7. state.advance(decision, grade)        (attempt count, hint level, phase)
   8. attempt_store.record()          ──►  attempt_id      ★ WRITE SIDE
   9. profile.record_attempt(used_hint=…); profile_store.save()  ★ WRITE SIDE
  10. teaching_state_store.save()      ──►  next turn resumes here
  11. recommend_problems_for_api()     ──►  next problems (now data-informed)
   │
   └─►  TutorTurnResult(grade, decision, phase, hint_level, misconception,
                        attempt_id, recommendations)
```

Steps 8–10 are the write side. Because verification, enforcement,
classification, persistence, mastery update and recommendation are all
deterministic, the whole turn is unit-testable with `StubTutorAgent` and
in-memory stores — no LLM, no Supabase.

---

## Usage

```python
from claire_core import (
    Problem, StudentAttempt, TutorAgent, run_tutor_turn,
    InMemoryAttemptStore, InMemoryProfileStore, InMemoryTeachingStateStore,
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
    teaching_state_store=InMemoryTeachingStateStore(),
)
print(result.decision.action, result.hint_level, result.misconception)
print(result.recommendations)
```

For production, swap the stores (no change to `loop.py`):
```python
from claire_core.persistence_sqlalchemy import (
    SQLAlchemyAttemptStore, SQLAlchemyProfileStore, SQLAlchemyTeachingStateStore,
)
```

Run the offline demo (no API key needed):
```bash
python -m claire_core.demo
```

---

## Tests

```bash
pytest tests/test_core_state.py tests/test_core_loop.py \
       tests/test_core_agent.py tests/test_core_classify.py
```

- `test_core_state.py` — the enforcement machine: grade rules, solution gate,
  hint escalation, resolved-lock, `TeachingState.advance` (20 tests, no deps).
- `test_core_loop.py` — the **closed loop** with the real verifier + real
  profile + real classifier + in-memory stores + stub agent. Proves persistence,
  mastery update, teaching-state advance, and hint-dependency all happen.
- `test_core_classify.py` — deterministic error classification.
- `test_core_agent.py` — agent wiring offline; the one live-LLM test is skipped
  unless `ANTHROPIC_API_KEY` is set.

The LLM is never called in the default suite, so it is fast and deterministic.

---

## How to continue (roadmap)

Ordered by leverage. Each item attaches to an existing seam.

1. ~~**Wire `run_tutor_turn` into the API.**~~ ✅ Done — `POST /api/attempt`
   wraps `run_tutor_turn` (SQLAlchemy stores + Clerk identity); the typed-practice
   frontend (`ProblemPractice.jsx`) grades through it, and the **mobile-upload
   handler** (`/api/mobile/.../upload`) now routes its handwritten-grading turn
   through `run_tutor_turn` too (`api._mobile_teaching_result`, ephemeral stores)
   — the old hand-rolled enforce is gone. The dead `/api/claire/agent` endpoint
   was removed. Still separate (not grading, kept intentionally): the dialogue
   layer `/chat` + `/api/tutor/respond` (`tutor/` pipeline).
2. ~~**Real retrieval.**~~ ✅ First cut — `retrieve_teaching_example(topic,
   error_type, course)` (`claire_core/problem_retrieval.py`) does keyword/topic
   ranking over the `problems/*.json` corpus and is registered in `TUTOR_TOOLS`.
   Next: swap keyword matching for real embeddings behind the same signature.
3. ~~**Multi-turn `TEACHING` loop.**~~ ✅ Done — `run_teaching_turn` (loop.py)
   is the follow-up dialogue turn: it carries the original verdict as background
   (never re-grades), lets the agent make **at most one tool call and one move**
   via a bounded `tool_request` hop (`TutorAgent.propose` → `tools.run_tool` →
   finalize), then `enforce → advance → save`. Per-problem `TeachingState` now
   holds a bounded `transcript` + structured `evidence`. Exposed at
   `POST /api/attempt/continue`; a pasted final answer returns `redirect_to_submit`
   so the frontend uses `/api/attempt` (verifier stays the sole answer authority).
   The orphaned `chat()` ReAct loop is intentionally NOT on this path.
4. **Sharper classification.** `classify.py` is conservative (sign/constant-factor
   → `ALGEBRA_ERROR`; clean missing factor → `CHAIN_RULE_OMISSION`; else
   `UNKNOWN`). Add step-level evidence via `verify_intermediate_step` to
   distinguish power-rule vs chain-rule vs product-rule reliably.
5. **Swap the model layer.** `agent.py` is the only file importing
   `langchain_anthropic`; `loop.py` and below are LLM-agnostic.
