# Claire Agent — Technical-Depth Roadmap (Context Management + Long-Term Memory)

## Context (why this exists)

Claire is a 秋招 AI-Agent portfolio project. The backend spine (`claire_core`) is
solid and deterministic (verifier = ground truth; `enforce()` clamps the LLM's
proposed action to a legal set), but the *agent-engineering* surface a recruiter
looks for is thin: context is bounded by naive fixed FIFO caps (no token budget,
no summarization, no relevance selection), long-term memory is only numeric
mastery (no episodic/semantic recall), and there is **no way to measure teaching
quality** — only answer-correctness benchmarks. The goal is to add real technical
depth in **context management** and **long-term memory**, and to make each change
**measurable**, without weakening the deterministic safety property.

Execution order (owner-approved): **A** thin teaching-trajectory eval → **B**
context engineering → **C** reflection-based long-term memory on plain Postgres →
**D** lightweight observability. **Strictly incremental: implement, test, review,
and STOP at each milestone before starting the next.** This document is a plan
only — no implementation is authorized by writing it.

---

## Thin runtime audit (verified against the repo, not remembered)

Purpose: confirm the real path this work attaches to. This is a note + invariants,
**not** a Phase-0 cleanup project.

### Verified typed-answer call chain (grading)
`POST /api/attempt` (`api.py:629`) → `submit_attempt` (`api.py:630`):
1. identity from a **verified Clerk JWT only** — `get_optional_identity` (`api.py:641`); anonymous ⇒ Null stores, `persisted=False`.
2. problem loaded server-side — `_load_core_problem` (`api.py:595`, called `:663`); official answer never trusted from client.
3. stores chosen by auth — `_attempt_stores` (`api.py:555`, called `:675`): authed ⇒ SQLAlchemy (Postgres), anon ⇒ Null.
4. LLM layer built by `_build_tutor_agent` (`api.py:548`); real `TutorAgent` (swappable/stubbable).
5. **`run_tutor_turn`** (`api.py:680` → `claire_core/loop.py:160`).

### Verified teaching-reply call chain (multi-turn dialogue)
`POST /api/attempt/continue` (`api.py:749`) → `continue_teaching` (`api.py:750`) →
**`run_teaching_turn`** (`api.py:782` → `claire_core/loop.py:273`). No grading, no
new attempt row, no mastery change; original verdict carried as background.

### Where each responsibility lives (the seams new work attaches to)
- **Prompt construction:** `claire_core/agent.py` — `_turn_prompt` (`:108`, grading), `_teaching_prompt` (`:187`, teaching), section builders `_state_block`/`_transcript_block`/`_evidence_block`, `SYSTEM_PROMPT` (`:38`). Profile digest: `_profile_summary` (`claire_core/loop.py:113`).
- **enforce (authoritative):** `state.py:enforce` (`:423`) + `allowed_actions` (`:362`). Grade from `verifier.py`.
- **advance (state mutation):** `state.py:TeachingState.advance` (`:315`) + `register_attempt` (`:305`).
- **persistence:** `run_tutor_turn` writes attempt (`loop.py:199`), profile (`:227`), teaching state (`:230`); `run_teaching_turn` saves state (`:365`, redirect path `:343`).
- **tool execution (one-hop, teaching only):** `run_teaching_turn` calls `run_tool` (`loop.py:318`, `tools.py:89`) at most once; `TutorAgent.propose(allow_tools=…)` (`agent.py:282`) finalizes and **clears any tool_request when `allow_tools=False`** (`agent.py:328`).
- **best-effort I/O template:** `_recommend` (`loop.py:147-157`) wraps optional work in try/except → `[]`. **This is the mandatory pattern for all new optional I/O (compaction, memory, tracing).**

### Which stacks serve live / compatibility traffic (do NOT touch)
- **Canonical (target of all new work):** `/api/attempt` + `/api/attempt/continue` → `claire_core`.
- **Compatibility already on the spine:** handwritten mobile upload `_mobile_teaching_result` (`api.py:~975`) routes through `run_tutor_turn` (`:1064`) with Null stores. In scope only if a change breaks its contract.
- **Legacy, OUT OF SCOPE:** `/chat` (`claire_agent_old.py`), `/api/tutor/respond` (`tutor/` pipeline), `agent/claire_agent.py`. `tutor/retrieval.py` contains a **mock hash-embedding** retriever — a dead-end parallel stack; **do not build memory/retrieval there.**

### Audit conclusion
`claire_core` behind `/api/attempt*` **is the correct path**. Legacy stacks are not
touched by A–D. No migration/unification/refactor of `agent/` or `tutor/` is in scope.

### Testable invariants captured now (become permanent regression gates)
Per graded/teaching turn, for the canonical loop:
1. **One teaching move per user message** — exactly one enforced `TeachingDecision` returned.
2. **≤1 tool execution per turn** — `run_tool` invoked at most once (grading turn: zero).
3. **Finalization cannot trigger another tool** — after `propose(allow_tools=False)`, `decision.tool_request is None`.
4. **enforce authoritative** — returned `action ∈ allowed_actions(grade, state)`; a CORRECT grade ⇒ action ∈ {CONFIRM_CORRECT, END_PROBLEM}.
5. **State advances at most once** — `advance` called once on the normal path, **zero** on the `redirect_to_submit` path (documented exception).
6. **Grade/allowed-actions untouched by context/memory** — those come only from `verifier.py` + `state.py`.
7. **Optional-step failures never break the request** — any new I/O degrades to a safe default (per `_recommend`).

---

## Dependencies between milestones
- **A** depends on nothing (pure offline harness; production code unchanged).
- **B** depends on **A** (A is B's regression gate + baseline). B is the technical centerpiece.
- **C** depends on **A** (measure memory on/off) and integrates through **B**'s context seam (recall injected as an optional context section). Build C after B.
- **D** depends on **B** (reuses the token counter) and instruments A/B/C. Build last.
- Each milestone ends at an explicit STOP; the next begins only after review.

---

## Milestone A — Thin teaching-trajectory evaluation harness

**Objective.** An offline harness that drives the *real* canonical loop with a
simulated student over 10–15 curated scenarios, and scores each trajectory with
(1) a **symbolic answer-leak check** reusing `benchmarks/evaluator.py`, (2)
structural assertions on the invariants above, and (3) an independently-authored
**LLM-as-judge** rubric. Output is a machine-readable scorecard. **No production
code changes.**

**Exact files (new unless noted).**
- `benchmarks/teaching_eval/__init__.py`
- `benchmarks/teaching_eval/scenarios.py` — `TeachingScenario` dataclass + `GOLDEN_SCENARIOS` (10–15). Fields: `id`, `problem: claire_core.state.Problem`, `student_turns: list[str]` (scripted), `persona: str`, `expected_terminal_phase`, `official_answer` (leak target), optional `scripted_agent: list[TeachingDecision]` for tool/edge cases.
- `benchmarks/teaching_eval/simulated_student.py` — `SimulatedStudent`: **scripted by default** (deterministic, no network); optional `--llm-student` persona mode behind a flag.
- `benchmarks/teaching_eval/leak_check.py` — `answer_leaked(tutor_messages, official_answer) -> (bool, str)`: for each tutor message before RESOLVED, extract candidate expressions and call **`benchmarks/evaluator.py:evaluate()`**; a hint symbolically equivalent to the official answer (when action ≠ SHOW_SOLUTION) is a leak.
- `benchmarks/teaching_eval/rubric.py` — **independently written, versioned** judge rubric (`RUBRIC_VERSION = "v1"`), NOT a copy of `SYSTEM_PROMPT`. Dimensions (structured output, each with a required 1-line evidence quote): `math_correctness`, `pedagogical_appropriateness`, `socratic_behavior`, `repetition`, `history_utilization`, `answer_leakage`.
- `benchmarks/teaching_eval/judge.py` — `judge_trajectory(scenario, transcript) -> JudgeVerdict`; real judge uses a **different model than the tutor** (reduce self-eval bias); CI uses a `StubJudge`.
- `benchmarks/teaching_eval/runner.py` — `run_trajectory`, `run_suite` (writes `benchmarks/results/teaching_eval_<ts>.json`), `main()` (`--limit`, `--scripted-only`, `--llm-student`, `--judge-model`). Drives **both** `run_tutor_turn` (first graded attempt) and `run_teaching_turn` (follow-ups) with **in-memory stores** so `enforce` runs end-to-end.
- `tests/test_teaching_eval.py` — CI-safe (StubTutorAgent + StubJudge, no network).

**Runtime integration point.** None in production. The harness *consumes* the spine
through `TutorAgentProtocol` (`agent.py:54`), the in-memory stores
(`persistence.py:68-118`), and the public `run_tutor_turn`/`run_teaching_turn`.

**Invariants that must remain true.** Harness cannot mutate grade/enforce; it only
reads results + `TeachingState`. The structural invariants (1–5, 7 above) are
asserted per turn inside `run_trajectory` and in `tests/test_teaching_eval.py`.

**Scenario coverage (initial 10–15).** wrong→right; repeated misconception;
direct request for the answer (must not leak); already-correct first answer;
repeated-hint-risk (hint must escalate); long-transcript pressure (many turns);
cross-session history — **exercised via the persistent profile store reused across
two runs** (per-problem transcript is intentionally session-scoped, see conflicts);
tool path — **grade, then a teaching reply whose scripted `propose_returns`
includes a `tool_request`** (only `run_teaching_turn` supports tools).

**Tests.** `pytest tests/test_teaching_eval.py` green (schema of scorecard;
`leak_check` catches a deliberately-leaking stub message; structural invariants
hold; a scripted illegal proposal is shown to be clamped by `enforce`). Core suite
stays green: `pytest tests/test_core_*.py`.

**Measurable completion criteria.** (a) `python -m benchmarks.teaching_eval.runner
--scripted-only` produces a scorecard JSON with per-scenario dimension scores +
leak flag + terminal phase; (b) a **baseline run with the real `TutorAgent` + real
judge** is captured and archived; (c) a short `baseline_notes.md`: manual
inspection of a representative sample, a judge-reliability check (re-run judge on a
subset, report score stability / disagreement), and **recommended regression
thresholds derived from the observed distribution** — NOT pre-set.
**Immediately enforce as hard gates only the structural invariants** (illegal-action
rate = 0, extra-tool-call rate = 0, leak rate on scripted scenarios = 0).
Model-quality scores (socratic/pedagogy/…) are **reported, not gated**, until a
baseline exists.

**Explicit non-goals.** No general-purpose eval platform; no large synthetic
scenario generation; no production instrumentation; no prompt/model changes; no
hard model-quality thresholds pre-baseline.

**STOP.** Do not start B until the baseline scorecard + `baseline_notes.md` +
threshold recommendation exist and are reviewed.

---

## Milestone B — Context engineering (the technical centerpiece)

**Objective.** Replace the fixed FIFO caps with a **token-budgeted context
assembler** that distinguishes and prioritizes context sections, compacts safely,
selects historical evidence deterministically, and emits **provenance** (what was
included/dropped and why) — provably bounding token growth without unacceptable
teaching-quality regression (measured via A).

**Distinct context sections (explicit priorities).**
1. authoritative state (phase, grade status, hint level) — highest priority, never dropped.
2. recent raw dialogue (last k verbatim turns).
3. structured rolling summary (older turns compacted).
4. selected historical evidence (`EvidenceRecord`s chosen by relevance).
5. student profile / recalled learnings (advisory; C plugs in here).

**Exact files.**
- `claire_core/context.py` (new):
  - `count_tokens(text) -> int` — approximate estimator (documented; see conflicts).
  - `ContextBudget` (max_tokens, per-section reserves/priorities) + `CONTEXT_FLAGS` (feature flags for ablation: `compaction`, `evidence_selection`).
  - `assemble_teaching_context(state, profile_summary, current_message, budget, flags) -> AssembledContext` (rendered blocks **+ provenance**: included/dropped sections, token counts).
  - `compact_transcript(entries, model=None) -> str` — rolling summary; **optional LLM call that degrades to FIFO on failure** (per `_recommend`).
  - `select_evidence(records, query, k) -> list[EvidenceRecord]` — **deterministic** scoring (recency + keyword overlap with `current_message`, reusing `problem_retrieval`'s scoring idea). No embeddings.
- `claire_core/agent.py` — `_transcript_block` (`:168`) and `_evidence_block` (`:175`) delegate to `context.assemble_teaching_context`; `_teaching_prompt` signature unchanged.
- `claire_core/state.py` — additive `TeachingState` fields: `rolling_summary: str = ""`, `summarized_turns: int = 0`. Keep `TRANSCRIPT_CAP`/`EVIDENCE_CAP` as hard safety ceilings; compact *before* the cap bites. **No migration** (round-trips via the `state_data` JSON blob).
- `tests/test_context.py` (new).

**Runtime integration point.** Prompt assembly inside `TutorAgent.propose/decide`
via the section builders. The assembler shapes **model input only**; it never
touches grade/enforce/advance.

**Invariants that must remain true.** All A-invariants hold. Assembler output tokens
≤ `budget.max_tokens - reserve`. Compaction/selection failures fall back to today's
FIFO behavior (safe default). Context module must not import `enforce`/
`allowed_actions`/`verifier` (add an import-boundary test).

**Tests.** `count_tokens` monotonic; `assemble_teaching_context` respects the budget
on a synthetic 20-turn transcript; compaction preserves the last k verbatim turns;
ablation flags toggle sections; provenance lists dropped sections; **rerun the A
harness — structural gates stay green and model-quality scores do not regress vs.
the A baseline.**

**Measurable completion criteria.** An **ablation table** comparing at least:
(i) FIFO baseline, (ii) token-budgeted, (iii) token-budgeted + compaction +
selection — reporting tokens/turn (mean, p95), teaching-quality scores, and leak
rate. Success = **bounded assembled-token growth as transcript grows 4→20 turns,
with no unacceptable quality regression** (threshold from A's baseline).

**Explicit non-goals.** No embeddings/vector search; no semantic relevance
(deterministic only); no memory writes (that's C); no model/prompt-content redesign
beyond section assembly.

**STOP.** Do not start C until the ablation table exists and shows bounded token
growth without regression, reviewed.

---

## Milestone C — Reflection-based long-term memory (plain Postgres)

**Objective.** A durable, cross-session **student-learning lifecycle** — the
technical story is the pipeline, not retrieval infra: *episode evidence → candidate
reflection → validation → dedup → consolidation → confidence update → conflict
handling → selective recall → measured effect on future teaching.*

**Learning kinds (minimum).** concept mastery/gap; recurring misconception;
effective/ineffective teaching strategy.

**Exact files.**
- `claire_core/reflection.py` (new):
  - `Learning` dataclass (user_id, course, topic, kind, text, confidence, support_count, status, created_at, updated_at, source_problem_id).
  - `propose_learnings(state, profile, problem, model=None) -> list[Learning]` — from episode evidence at a terminal boundary; **optional LLM call, degrades to []**.
  - `validate(cands) -> list[Learning]` — drop empty/overlong/non-actionable.
  - `consolidate(store, cands) -> None` — dedup by `(user_id, course, topic, kind, normalized_text)`; on match bump `support_count`/`confidence`; **conflict handling** (contradictory learning on same topic/kind) reconciled by recency + confidence; keep durable learnings **separate from ordinary problem retrieval**.
  - `retrieve_learnings(store, user_id, problem, k=3) -> list[Learning]` — advisory recall by topic/keyword + confidence.
- `claire_core/persistence.py` — add a `LearningStore` **port** (4th port) + `InMemoryLearningStore` + `NullLearningStore`.
- `claire_core/persistence_sqlalchemy.py` + `db/models.py` + `alembic/versions/0002_add_learnings.py` — a normal `student_learnings` table (down_revision `"0001_initial"`). **No pgvector.**
- `claire_core/loop.py` — a **guarded** consolidation step (try/except → no-op, per `_recommend`) fired **only when `state.phase` becomes RESOLVED/ABANDONED** in `run_tutor_turn` (after `advance`, `:196`) and `run_teaching_turn` (after `advance`, `:358`); recall injected **through B's context seam** as the advisory "recalled learnings" section (NOT inlined into the unguarded `_profile_summary`).
- `tests/test_reflection.py` (new).

**Runtime integration point.** Write side: terminal-phase hook in both loop
functions (guarded, skipped for Null store / anonymous). Read side: an optional
context section via `claire_core/context.py`.

**Invariants that must remain true.** All A/B invariants. Recall is **advisory
only** — it may shape model input but must **never override current evidence,
grade, or deterministic state**. Reflection runs **only at resolved/abandoned**,
never per raw message. Anonymous path (Null store) writes/recalls nothing. All
memory I/O guarded → failures never break the teaching request.

**Tests.** `propose_learnings` on a RESOLVED state yields ≥1 candidate;
`consolidate` dedups + bumps confidence; conflict reconciliation picks the
higher-confidence/newer learning; `retrieve_learnings` recalls a topically-matching
learning; Null store is a strict no-op; a throwing store does not break
`run_tutor_turn`. Rerun A harness: structural gates green.

**Measurable completion criteria.** A **memory on/off comparison** via A: same
scenarios with recall injected vs. not, reporting `history_utilization` /
`pedagogical_appropriateness` deltas and token cost of the recalled section. Success
= a **measured, non-negative effect** with bounded added tokens; if effect is
neutral, the lifecycle + safety story still stands (report honestly).

**Explicit non-goals.** No pgvector; no embedding-based dedup/recall; no embedding
the problem corpus; no knowledge-graph memory; recall never gates enforcement.

**STOP.** Do not start D until the memory on/off table exists and safety
no-op/guard tests pass, reviewed.

---

## Milestone D — Lightweight observability (mechanism-focused)

**Objective.** A small custom tracer that records structured operational data per
turn and a report script — chosen over importing a large platform to *show the
mechanism*.

**Exact files.**
- `claire_core/tracing.py` (new): `@traced("stage")` / context manager recording `{turn_id, stage, prompt_version, context_version, tokens_in, tokens_out, latency_ms, model, selected_context_sections, recalled_learning_ids + reasons, proposed_action, enforced_action, state_transition, degraded_path}`. **First version writes JSONL** (or the existing logging path) — a DB table (`0003_add_traces`) only if reporting actually needs it. **No hidden chain-of-thought stored.**
- `claire_core/loop.py` — wrap `decide`/`propose` calls (`:186`, teaching propose) and `run_tool` (`:318`); reuse `context.count_tokens` from B; token→cost via a per-model rate table.
- `scripts/trace_report.py` (new): mean & p95 tokens, mean & p95 latency, est. cost/turn, grouped by experiment variant.
- `tests/test_tracing.py` (new).

**Runtime integration point.** Thin wrappers around existing agent/tool calls in
the loop; purely additive.

**Invariants.** Tracing is best-effort — a throwing tracer never breaks the loop
(assert). No CoT persisted. `proposed_action` vs `enforced_action` recorded so
enforcement overrides are visible.

**Tests.** A full `run_tutor_turn` emits spans with non-null latency + token counts;
a throwing tracer still completes the turn; report script runs over a harness run.

**Measurable completion criteria.** `python scripts/trace_report.py` prints p50/p95
tokens, p50/p95 latency, and $/turn, broken down by variant — a **trace + cost
report** artifact.

**Explicit non-goals.** No LangSmith/large platform required (optional
`LANGCHAIN_TRACING_V2` toggle only); no metrics dashboard/alerting; no CoT storage;
no perf tuning.

**STOP.** Roadmap complete after D's report artifact is reviewed.

---

## Portfolio artifacts (one measured output per milestone)
A: baseline scorecard + reliability note · B: context ablation table · C: memory
on/off comparison · D: trace + cost report. **No public website / frontend redesign
during A–D.** The project story is backed by measured results, not predetermined claims.

## Risks & safe-degradation rules
- **Deterministic spine is the crown jewel.** Context/memory may shape *model input
  and the profile/recall sections only* — never grade, `allowed_actions`, `enforce`,
  or the once-per-turn `advance`. Enforce via import-boundary tests + the A
  structural gates in CI.
- **Every new optional step (compaction, memory, tracing) follows the `_recommend`
  pattern** (`loop.py:147-157`): try/except → safe default; anonymous/Null path =
  no-op.
- **Judge reliability / self-eval bias** — independently authored rubric, a
  different model for the judge than the tutor, evidence-per-score, a reliability
  check before trusting model-quality numbers; structural gates carry CI regardless.
- **Token-count accuracy** — the estimator is approximate for Claude; budgeting is a
  relative bound, reported as such.
- **Cost/infra** — A/B/D need no new infra; C adds one normal Postgres table (no
  pgvector). LLM calls in A (real-judge runs), B (compaction), C (reflection) are
  offline/optional and degrade safely.

## Deferred (explicit non-goals for A–D)
pgvector; embedding-based memory retrieval; embedding the full corpus; multi-agent
architecture; autonomous planning loops; fine-tuning; knowledge-graph memory;
replacing deterministic enforcement with LLM decisions; large-scale synthetic
scenario generation; migrating/retiring legacy `agent/`/`tutor/` stacks; major
frontend work.

---

## Do the owner's constraints conflict with the repo? (with smallest adjustments)

1. **"State advances once" vs. reality.** `run_tutor_turn` calls both
   `register_attempt` (`state.py:305`) and `advance` (`:315`); the
   `redirect_to_submit` path in `run_teaching_turn` calls `advance` **zero** times.
   *Adjustment:* restate the invariant as "**exactly one enforced `advance` per
   turn on the normal path; zero on the redirect path**" (documented). Not a code
   conflict — a precision fix so the regression assertion is truthful.

2. **"Context/memory failures never break the request" vs. unguarded
   `_profile_summary`.** `_profile_summary` (`loop.py:113`) is not try/except-wrapped
   because it does no I/O today; memory recall adds I/O. *Adjustment:* memory recall
   must be a **separate guarded step** (per `_recommend`) injected via B's context
   seam — **do not inline recall into `_profile_summary`**. Reflected in C.

3. **"Cross-session history" scenario vs. session-scoped transcript.** Per-problem
   `TeachingState` (transcript/evidence) is scoped by
   `(user_id, problem_id, attempt_session_id)` and a fresh session id is minted per
   problem — so the *transcript* is intentionally not cross-session. *Adjustment:*
   the cross-session eval scenario exercises the **persistent profile store (and, in
   C, learnings)** reused across two harness runs, not the per-problem transcript.
   Reflected in A.

4. **"Tool path" scenario vs. where tools run.** Tools execute only in
   `run_teaching_turn` (`loop.py:318`), never in the grading turn. *Adjustment:*
   tool-path scenarios must **grade first (`run_tutor_turn`), then drive a teaching
   reply** whose scripted `propose_returns` includes a `tool_request`. Reflected in A.

5. **Token counting exactness.** No native offline Claude tokenizer. *Adjustment:*
   `count_tokens` is an **approximate estimator** (heuristic/tiktoken), documented;
   Anthropic's network `count_tokens` is intentionally avoided in the deterministic
   assembler. Reflected in B.

6. **"Confidence/conflict handling" without embeddings.** On plain Postgres, dedup
   and conflict detection use **deterministic keys + normalized text**, not semantic
   similarity. *Adjustment:* scope C's dedup/conflict to key/string matching;
   semantic dedup is deferred with the rest of embeddings. Reflected in C.

No constraint is blocked by the architecture; all six are handled by small,
documented adjustments rather than silently accepted.
