# Tutor Intervention Layers (L0 / L1 / L2)

> **Living doc.** This tracks the design, current state, and progress of Claire's
> tiered intervention system on the problem-practice page. Update the status table
> and progress log as work lands. Last updated: 2026-06-01.

---

## The Vision

Three escalating levels of teacher presence while a student works a problem:

| Level | Name | Trigger | Behavior |
|-------|------|---------|----------|
| **L0** | Always-on Teacher (Ambient) | Student opens problem | One quiet line at top of page. Makes the teacher *feel* present without interrupting. e.g. *"For this problem, the cosine inside the exponential is the main complication."* |
| **L1** | Nudge (Light Intervention) | Student idles, asks, or says "no idea" | Not a lecture. Surfaces the problem's key info or gives the **first-step scaffold**, or a guiding question. Student can ask back / interact, then keeps working. e.g. *"In implicit differentiation we isolate dy/dx — now try that on your problem."* |
| **L2** | Teaching Mode (Socratic) | L1 didn't unstick them | Problem shifts to left 1/3, Claire "whiteboards" on right 1/3. Socratic — student derives the answer; only spell out steps as a last resort. Returns to practice page when done. |

---

## Current State (audited 2026-06-01)

| Level | Component | Wired into page? | Content source | Real status |
|-------|-----------|------------------|----------------|-------------|
| **L0** | `web/src/components/claire/ClaireL0Strip.jsx` | ✅ Yes | **Hand-authored** static file `web/src/data/tutorAssets/l0Observations.js` | Works, but only ~4 problems have authored lines. The other ~756 render nothing. NOT model-generated. |
| **L1** | `web/src/components/claire/ClaireCorner.jsx` (NEW) | ✅ Yes — always-on bottom-right avatar | Live agent via `useClaireAgent` (latest Claire turn → bubble) | Built + wired 2026-06-01. Always-on persona; bubble auto-opens on reply and on a 75s idle-peek; escalate link → L2. (Old `ClaireL1Nudge.jsx` full-card shell is now superseded and unused.) |
| **L2** | `web/src/components/claire/PartTutorPanel.jsx` | ✅ Yes | Live agent via `useClaireAgent` / backend `tutor/` pipeline | Working. Page escalates **L0 → L2 directly** (skips L1). |

Orchestration today lives in `ProblemPractice.jsx`:
- `TutorLevel` enum has `L1_LIGHT_INTERVENTION` marked `// (future)`.
- State machine only ever uses `L0_AMBIENT` and `L2_TEACHING`.

### L1 UI direction (decided 2026-06-01)

L1 should **not** be the current full-width inline card. Instead: a small **persona /
avatar pinned to the bottom-right corner** of the page (chat-head style, like
Instagram/Snapchat DM bubbles). The L1 content appears in a **speech bubble** anchored to
that avatar. Quiet and peripheral by default; expands into the bubble when L1 fires. The
existing `ClaireL1Nudge.jsx` (full card) likely gets restyled or replaced to fit this
corner-bubble pattern. Escalation to L2 happens from inside the bubble.

---

## Key Architectural Insight — the "Problem Brief"

**Problem with L0 (the realization that motivated this doc):** A *useful* first-glance
hint requires the model to have **already solved the problem** and judged what's
pedagogically salient. With only the problem text as context, the model says generic /
random things. That's why L0 was hand-authored — it doesn't scale.

**This is a precompute problem, not a live-inference problem.**

**Solution — one shared artifact feeds all three levels.** Precompute, per problem
(offline, with SymPy as ground truth), a small **Problem Brief**:

```
ProblemBrief {
  main_complication: str   // → L0 strip (one line)
  first_step: str          // → L1 nudge scaffold
  key_formula: str         // → L1 / L2
  common_mistake: str      // → L0 / L1 / L2
  // (full worked solution stays in L2's live agent)
}
```

- **L0** = render `main_complication`.
- **L1** = render `first_step` + a guiding question (+ `key_formula`).
- **L2** = use the whole brief as the Socratic skeleton for the live agent.

Result: L0 and L1 become **cheap reads of cached, verified content** instead of risky
live generation. L0 stops saying random things because the brief was authored by a model
that actually solved the problem.

---

## Recommended Build Order

1. **Wire L1 into `ProblemPractice`** (smallest real win — component already built).
   Add trigger logic (idle timer / "I'm stuck" / question intent) → show `ClaireL1Nudge`
   → escalate button → L2.
2. **Make L2 emit the Problem Brief** so we capture the artifact while the agent already
   has the solution in context.
3. **Build the offline Problem Brief precompute pipeline** (batch over the 760+ problems,
   SymPy-verified) and cache per problem.
4. **Rework L0** to read `main_complication` from the cached brief instead of the
   hand-authored file. Decide if L0 is still worth keeping once L1 is good.

---

## Open Questions / Issues

- [ ] Should L0 survive at all, or does a good L1 make it redundant? (Revisit after L1 is live.)
- [ ] L1 trigger policy: idle timeout (how many seconds?) + explicit "stuck" + question intent. What's the right idle threshold?
- [ ] Where does the Problem Brief live — new JSON next to each problem, a DB table, or generated into `tutorAssets/`?
- [ ] How do we QA brief quality at scale (760+ problems)? Spot-check? Verifier-gated?
- [ ] L1 content: precomputed brief vs. live-generated per student context? (Lean precomputed first.)

---

## Main-part assumption — deferred (future work)

The practice page used to assume that, for a multi-part problem, **one part is the
"main" question and the rest are scaffolding/warm-up** (the previous heuristic picked
part *b* — `mainQuestionIndex = parts.length > 1 ? 1 : 0`). The UI reflected this with:
a larger/highlighted progress dot + a "main" caption, a "Main Question" badge and
"Warm-up" label on the part header, and a right-sidebar tip ("Part (a) helps you build
up to the main question…").

**Status: deferred.** The direction is promising — a real curriculum often has a
culminating part with earlier parts as scaffolds — but the *b-is-always-main* heuristic
is too crude (the main part isn't always b; some problems have no single "main" part).
For now **all parts are presented as equal peers**: uniform progress dots, identical part
badge, no main/warm-up annotations, and the warm-up tip removed.

When we revisit this, do it properly:
- Derive the main part from real structure (problem metadata / the offline Problem Brief),
  not a positional guess.
- Decide whether "main vs. scaffold" is even the right model, or if parts should stay
  peers with per-part difficulty/role hints instead.
- Re-introduce the visual emphasis (dot size, badge, sidebar guidance) only once the
  designation is trustworthy.

Removed UI lives in `web/src/components/dashboard/ProblemPractice.jsx` git history; a
breadcrumb comment near the old `mainQuestionIndex` points back here.

---

## Adaptive path vs. forced path — deferred (future work)

**Problem.** A multi-part problem (a → b → c) is not one-size-fits-all. Different students
should move through it differently:

| Student | Ideal route |
|---------|-------------|
| Weak | `a → b → c` (full scaffold, in order) |
| Strong | jump straight to `b` |
| Stronger | jump straight to `c` |
| Teacher view | system recommends the next best step |

A single hard-coded **"Next Part"** button forces everyone down `a → b → c`. That's wrong
for strong students and ignores what we know about the learner.

**Direction.** The system should offer a **recommended path**, not a forced one:

- The student can **always click any part** directly (already shipped — the progress
  dots are clickable, see `handleSelectPart` in `ProblemPractice.jsx`).
- The **default action button gives exactly one recommended next move** — a single
  **"Continue"** that resolves to the right target for *this* student (e.g. start at `a`,
  or skip to `b`/`c`), instead of a literal "Next Part."
- One recommended action only. Avoid three competing nav buttons (Next / Skip / Show
  answer) fighting each other — that's the clutter we just removed.

**Why one button + free navigation is the right shape.** Flexible (click any part) *and*
guided (the default is always a confident single recommendation). The recommendation
carries the adaptivity; the clickable dots carry the freedom.

**What's needed to build it:**
- A recommendation function: `recommendNextPart(student, problem, progress) → partIndex`
  (or "done"). Inputs: diagnostic skill level / mastery (`student_profile_v2`), per-part
  difficulty/role, and what they've already completed correctly this session.
- Replace the `handleNextStep` "always +1" logic with "go to the recommended part."
- Relabel the primary button **"Continue"** and have it call the recommender; keep the
  clickable dots as the manual override.
- Likely ties into the **Problem Brief** (per-part `first_step` / difficulty) and the
  deferred **main-part** designation above — the recommender needs to know each part's
  role to route a strong student to the culminating part.

**Status: deferred.** Today the flow is still linear (`handleNextStep` advances by +1) and
the primary button is the per-step continue. Ship the recommender once we have reliable
per-part difficulty/role metadata and a student skill signal to key off.

---

## Progress Log

- **2026-06-01** — Audited current state. Found: L0 hand-authored (~4 problems), L1 built but unwired with no content pipeline, L2 wired and working (L0→L2 skips L1). Defined the "Problem Brief" unifying architecture. Created this doc.
- **2026-06-01 (fix)** — Added a **charitable-parsing** system prompt (`PLANNER_SYSTEM`) to `tutor/teaching_planner.py`, applied to every planner call (stuck/hint/followup). Reads plain-text math calculator-style, doesn't nitpick notation when meaning is clear, and — key case — when a student omits denominator/numerator grouping (types `1/x+1` for `1/(x+1)`) and context implies the grouped form, treats the math idea as correct with a light "add parentheses" reminder instead of marking it wrong. Only asks for clarification when both readings are genuinely plausible. (Covers the typed L1 path; the handwriting-upload path is SymPy-verified separately.)
- **2026-06-01 (bugfix)** — Fixed L1 multi-turn **memory loss**. Root cause: `useClaireAgent` built the recent-thread context with `msg.content?.text`, but `teaching_card`/`teaching_action` events store their text in `concept_bridge`/`next_micro_step`, so every prior Claire turn serialized to `''` → the agent saw a blank conversation and restarted ("let's start fresh"). Added `extractEventText()` to serialize all event types, widened the window to 8 turns, dropped blank turns, and stopped double-recording the user message in `handleCornerRespond`. **Still open:** plain-text math notation is read pedantically — a student typing `1/(x+1)` / "1 over x+1" can be misparsed as `1/x + 1` and "corrected" though the math is right. That's a backend teaching-prompt tuning issue (be charitable about typed notation), not yet addressed.
- **2026-06-01 (fix)** — L1 bubble content corrected. It no longer shows a generic greeting + canned "I'm stuck / hint" chips (that was just copied chat). Now, when the bubble opens (idle-peek or click), it fetches a real **L1 nudge** via the `student_stuck` action → backend `teaching_card` (`concept_bridge` + `next_micro_step` + `quick_replies`): clarifies the problem / gives the first-step scaffold or a guiding question, never a full solution. The text input stays so the student can interact after reading the nudge. Avatar + bubble visuals unchanged. `nudgeRequestedRef` prevents re-fetching on reopen.
- **2026-06-01** — Decided L1 UI = always-on bottom-right persona (chat-head + speech bubble). Built `ClaireCorner.jsx` and wired it into `ProblemPractice`: always visible (except exam/upload), bubble opens on new reply + 75s idle-peek, content = live agent (latest Claire turn), "I need more help →" escalates to L2. Made the top `ClaireResponseStrip` ambient-only (L0 observation) so the corner is the single conversation surface. Web build passes. **Still pending:** real "Problem Brief" content pipeline (corner currently uses live generation, not precomputed briefs), and the idle-peek is presence-only (no proactive backend nudge yet).
