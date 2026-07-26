# Teaching-Eval Baseline Notes (Milestone A)

Companion to `AGENT_DEPTH_ROADMAP.md` §Milestone A. This is the reviewed baseline
that gates the start of Milestone B. It records (1) the **offline structural
baseline** (captured, deterministic), (2) the **procedure for the live
model-quality baseline** (an authorized LLM run — cost + API key), and (3) the
**recommended regression thresholds**, derived — not pre-set.

Harness entry point: `python -m benchmarks.teaching_eval.runner`.

---

## 1. What the harness measures

Each scenario is a scripted student journey over one problem, driven through the
**real canonical spine** with in-memory stores so `enforce` runs end-to-end:

- SUBMIT turns → `claire_core.run_tutor_turn` (real SymPy grading).
- REPLY turns → `claire_core.run_teaching_turn` (bounded one-hop tool loop).

Three independent scorers per trajectory:

| Scorer | Source | Role |
|--------|--------|------|
| **Structural invariants** | `runner.run_trajectory` (reads grade + `enforce` output) | **HARD gate** |
| **Answer-leak check** | `leak_check.answer_leaked` (reuses `benchmarks.evaluator.evaluate`) | **HARD gate** |
| **LLM-as-judge rubric** | `rubric.py` (v1) + `judge.py` (model ≠ tutor) | Reported, **not** gated pre-baseline |

Structural counters asserted per turn:
- `illegal_action` — enforced action ∉ `allowed_actions(grade)`.
- `correct_confirm_violation` — a CORRECT grade produced anything but confirm/end.
- `extra_tool_calls` — >1 `run_tool` in a teaching turn, or any in a grading turn.
- `finalize_tool_not_cleared` — a finalized decision still carried a `tool_request`.
- `leak` — a pre-solution tutor message symbolically equal to the official answer.

## 2. Scenario coverage (12 golden scenarios)

`wrong_then_right`, `correct_first_try`, `unverifiable_answer`,
`repeated_misconception`, `direct_answer_request`, `repeated_hint_escalation`,
`long_transcript_pressure`, `cross_session_history`, `tool_path_verify_step`,
`optimization_wrong_then_right`, `integration_correct_first`,
`integration_stuck_then_taught`.

These map onto the roadmap's required coverage: wrong→right; repeated
misconception; direct answer request (must not leak); already-correct first try;
repeated-hint escalation; long-transcript pressure; cross-session history (via the
persistent **profile** store reused across two fresh sessions — the per-problem
transcript is intentionally session-scoped); and the tool path (grade first, then
a teaching reply whose scripted proposal carries a `tool_request`).

## 3. Offline structural baseline (captured, deterministic)

Command: `python -m benchmarks.teaching_eval.runner --scripted-only`
(StubTutorAgent + StubJudge + scripted student — no network, identical every run).

| Metric | Value |
|--------|-------|
| Scenarios / turns | 12 / 31 |
| Terminal phase matched expected | 12 / 12 |
| Illegal actions | **0** |
| Correct-confirm violations | **0** |
| Extra tool calls | **0** |
| Finalize-not-cleared | **0** |
| Pre-solution leaks | **0** |
| **Hard gates pass** | **True** |

Model-quality numbers in the scripted scorecard are the StubJudge constant and
carry **no signal** — they exist only to exercise the schema. Real numbers come
from the live run (§4).

`tests/test_teaching_eval.py` locks these gates plus the detectors themselves
(a deliberately-leaking message is caught; `show_solution` is exempt; a scripted
illegal proposal is shown clamped by `enforce`; the tool path runs exactly one
tool; hints escalate across turns; cross-session mastery accumulates).

## 4. Live model-quality baseline — procedure (authorized run)

Requires `ANTHROPIC_API_KEY` and spends tokens, so it is a deliberate,
owner-authorized step, not part of CI.

```bash
# Real tutor (claire_core TutorAgent) + real judge on a DIFFERENT model.
python -m benchmarks.teaching_eval.runner --judge-model <opus-or-sonnet-3.7-snapshot>
# Optional: student voice via LLM personas (SUBMIT answers stay scripted):
python -m benchmarks.teaching_eval.runner --judge-model <id> --llm-student
```

The judge defaults to a model distinct from the tutor (`claude-sonnet-4-5`) to
reduce self-evaluation bias; override with `--judge-model` to the strongest
available distinct model for the archived baseline. The scorecard is written to
`benchmarks/results/teaching_eval_<ts>.json`.

**To complete the archived baseline, record here after the authorized run:**
- [ ] `benchmarks/results/teaching_eval_<ts>.json` path (the archived live scorecard).
- [ ] Tutor model + judge model ids actually used.
- [ ] Manual inspection of a representative sample (3–4 trajectories): are the
      judge's scores + evidence quotes defensible? Note any miscalibration.
- [ ] **Judge-reliability check:** re-run the judge on the same transcripts
      (≥2 repeats over a 4–5 scenario subset) and report per-dimension score
      stability (max spread / disagreement rate). Only trust dimensions that are
      stable across repeats.

## 5. Recommended regression thresholds (derived, not pre-set)

**Enforce now as hard CI gates (already green offline):**
- `illegal_action_count == 0`
- `correct_confirm_violation_count == 0`
- `extra_tool_call_count == 0`
- `finalize_tool_not_cleared_count == 0`
- `leak_count == 0` (on the scripted golden set)

These are safety properties of the deterministic spine and must never regress.
`runner.main()` already exits non-zero when any is violated.

**Model-quality thresholds — set from the live distribution, do NOT hard-code yet.**
Recommended method once §4 numbers exist:
1. Keep only judge dimensions that passed the reliability check.
2. For each kept dimension, set the regression floor at
   `mean − 1·stdev` (rounded down to the nearest 0.5) over the live baseline,
   as a **warn**, not a hard fail, until a second independent baseline confirms
   the distribution.
3. Treat `answer_leakage` as the exception: because the symbolic leak gate
   already covers it structurally, the judge's `answer_leakage` dimension is a
   cross-check — a divergence between the two is a signal to inspect, not a gate.

**Rationale for not pre-setting quality gates:** with only a StubJudge constant
captured, any model-quality floor would be arbitrary. Milestone B (context
engineering) is measured as *no unacceptable regression vs. this live baseline* —
so the live numbers must exist first. That is the STOP condition before B.

## 6. Known limitations (honest scope of the thin harness)

- The leak checker catches a tutor **stating** the answer (literal, symbolic, or a
  distinct bare numeric ≥ 2); it does not attempt to catch every paraphrase. Bare
  `0`/`1` numeric answers are intentionally not flagged to avoid false positives
  in calculus prose (`n−1`, `reduce by 1`).
- `count`-based tool assertions rely on wrapping `claire_core.tools.run_tool`;
  this is harness-only instrumentation and touches no production path.
- The scripted student is deterministic by design. `--llm-student` rewrites only
  REPLY text; SUBMIT answers stay scripted so grading stays deterministic.

---

**STOP (per roadmap).** Milestone B does not start until the §4 live baseline is
captured, the judge-reliability check is recorded, and §5 thresholds are reviewed.
