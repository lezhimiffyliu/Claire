# Claire Design System v2

## Core Hook
**"Know what to study next."**

---

## Color Variables

```css
:root {
  /* Primary */
  --claire-navy: #0B1F3A;
  --claire-navy-light: #1A3A5C;
  --claire-navy-dark: #061425;

  /* Progress / Correct */
  --claire-teal: #2FBF9F;
  --claire-teal-light: #4DD4B4;
  --claire-teal-muted: rgba(47, 191, 159, 0.15);
  --claire-teal-shadow: #24997F;

  /* Background */
  --claire-bg: #F7F9FB;
  --claire-bg-card: #FFFFFF;
  --claire-bg-elevated: #FFFFFF;

  /* Neutral */
  --claire-gray-900: #1A1F26;
  --claire-gray-700: #4A5568;
  --claire-gray-500: #718096;
  --claire-gray-400: #A0AEC0;
  --claire-gray-300: #CBD5E0;
  --claire-gray-200: #E2E8F0;
  --claire-gray-100: #EDF2F7;

  /* Status */
  --claire-weak: #E85D5D;
  --claire-weak-bg: rgba(232, 93, 93, 0.08);
  --claire-strong: #2FBF9F;
  --claire-strong-bg: rgba(47, 191, 159, 0.08);
  --claire-next: #5B8DEF;
  --claire-next-bg: rgba(91, 141, 239, 0.08);
  --claire-locked: #A0AEC0;

  /* AI Thinking */
  --claire-ai-blue: #6B9FE8;
  --claire-ai-blue-bg: rgba(107, 159, 232, 0.1);
}
```

### Tailwind Config Extension
```js
colors: {
  navy: {
    DEFAULT: '#0B1F3A',
    light: '#1A3A5C',
    dark: '#061425',
  },
  teal: {
    DEFAULT: '#2FBF9F',
    light: '#4DD4B4',
    muted: 'rgba(47, 191, 159, 0.15)',
  },
  claire: {
    bg: '#F7F9FB',
    weak: '#E85D5D',
    strong: '#2FBF9F',
    next: '#5B8DEF',
    locked: '#A0AEC0',
    ai: '#6B9FE8',
  }
}
```

---

## Icon System

### Brand Mark: "Guided Path"
A path with nodes representing progress. Current node is highlighted with a subtle pen trace.

**SVG Sketch (simplified)**:
```
○───────●───────○───────○
        │
       ╱╲  (pen trace element)
```

- **Past nodes**: Solid teal circles (small)
- **Current node**: Larger teal circle with pulsing ring + pen trace
- **Future nodes**: Empty circles with gray stroke
- **Connecting line**: Dashed or dotted gray line

### Icon Variants

1. **Logo Mark**: Single highlighted node with minimal path fragment and pen trace
2. **Progress Indicator**: Linear path with node states
3. **Loading State**: Current node with ripple animation

### Forbidden Icons
- ❌ Robots / AI faces
- ❌ Lightbulbs
- ❌ Books / Graduation caps
- ❌ Clocks / Timers
- ❌ Generic checkmarks (use path node instead)

---

## Landing Structure

### Above Fold
```
┌─────────────────────────────────────────────────────────────┐
│  [Claire Logo]                              [Get Started →] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     Know what to study next.                               │
│                                                             │
│     Stop guessing. Get a clear path to your target grade.  │
│                                                             │
│     [ START DIAGNOSTIC ]                                    │
│                                                             │
│     ┌────────────────────────────────────┐                 │
│     │   DIAGNOSTIC PREVIEW CARD          │                 │
│     │   ○ Weak: Implicit Differentiation │                 │
│     │   ● Next: Related Rates            │                 │
│     │   ○ Strong: Chain Rule             │                 │
│     └────────────────────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Value Props (3 cards, horizontal)
```
┌──────────────────┬──────────────────┬──────────────────┐
│   5-MIN SCAN     │   CLEAR PATH     │   REAL EXAMS     │
│   ────────────   │   ────────────   │   ────────────   │
│   Find weak      │   See what to    │   760+ UW past   │
│   spots fast     │   study next     │   exam problems  │
└──────────────────┴──────────────────┴──────────────────┘
```

### No animations, no mascots, no testimonials.

---

## Core UI Components

### 1. Diagnostic Result Panel

**Layout**: Status-first. Show what's weak/strong/next immediately.

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR DIAGNOSIS                                  Math 125   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ WEAK ──────────────────────────────────────────────┐   │
│  │  Implicit Differentiation                           │   │
│  │  You missed the chain rule step on y terms          │   │
│  │  [Start fixing →]                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ NEXT ──────────────────────────────────────────────┐   │
│  │  Related Rates                                      │   │
│  │  Prerequisite for optimization problems             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ STRONG ────────────────────────────────────────────┐   │
│  │  Chain Rule · Power Rule · Basic Limits             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Status Badge Styles**:
- WEAK: Red border-left, subtle red bg, red text label
- NEXT: Blue border-left, subtle blue bg, blue text label
- STRONG: Teal border-left, subtle teal bg, teal text label
- LOCKED: Gray, no interaction

### 2. Roadmap View

**Layout**: Vertical path with nodes. Current position is clear.

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR PATH TO 3.5+                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ● Limits & Continuity ────────────────── ✓ DONE        │
│     │                                                       │
│     ● Chain Rule ─────────────────────────── ✓ DONE        │
│     │                                                       │
│     ◉ Implicit Differentiation ───────────── ◀ YOU ARE HERE│
│     │   └─ 3 problems remaining                            │
│     │                                                       │
│     ○ Related Rates ──────────────────────── NEXT          │
│     │                                                       │
│     ○ Optimization ───────────────────────── LOCKED        │
│     │                                                       │
│     ○ L'Hôpital's Rule ───────────────────── LOCKED        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Node States**:
- DONE: Solid teal, checkmark
- CURRENT: Teal with pulse ring, marker text
- NEXT: Empty circle, blue tint on hover
- LOCKED: Gray, 60% opacity

### 3. Practice Panel

**Layout**: Problem as focal point. Status bar at top.

```
┌─────────────────────────────────────────────────────────────┐
│  Implicit Differentiation                    Problem 2/6   │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 33%         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MATH 125 · FINAL 2023 · MEDIUM                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  Find dy/dx if:                                     │   │
│  │                                                     │   │
│  │       x² + y² = 25                                  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📷 Upload your work                                │   │
│  │  or                                                 │   │
│  │  [ Show me the approach ]                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**AI Feedback State** (after upload):
```
┌─────────────────────────────────────────────────────────────┐
│  ┌─ AI ANALYSIS ───────────────────────────────────────┐   │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (thinking...)  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ CLAIRE'S FEEDBACK ─────────────────────────────────┐   │
│  │  Your differentiation of x² is correct.             │   │
│  │                                                     │   │
│  │  ⚠ But when you differentiated y², you forgot      │   │
│  │    to multiply by dy/dx (chain rule).              │   │
│  │                                                     │   │
│  │  [ Try again with this hint ]                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Button System

### Primary Button (Navy)
```css
.btn-primary {
  background: var(--claire-navy);
  color: white;
  box-shadow: 0 3px 0 0 var(--claire-navy-dark);
}
.btn-primary:active {
  transform: translateY(3px);
  box-shadow: none;
}
```

### Secondary Button (Teal)
```css
.btn-secondary {
  background: var(--claire-teal);
  color: white;
  box-shadow: 0 3px 0 0 var(--claire-teal-shadow);
}
```

### Ghost Button (for less emphasis)
```css
.btn-ghost {
  background: transparent;
  color: var(--claire-navy);
  border: 2px solid var(--claire-gray-300);
}
```

---

## Typography

### Font Stack
```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

### Scale
- **H1 (Landing)**: 48px / 700 / -0.02em
- **H2 (Section)**: 24px / 600 / -0.01em
- **H3 (Card title)**: 18px / 600 / 0
- **Body**: 16px / 400 / 0
- **Caption**: 14px / 500 / 0
- **Label**: 12px / 600 / 0.05em (uppercase)

---

## Card System

### Status Card
```css
.status-card {
  background: var(--claire-bg-card);
  border-radius: 12px;
  border-left: 4px solid var(--status-color);
  padding: 16px 20px;
}
.status-card.weak { --status-color: var(--claire-weak); }
.status-card.next { --status-color: var(--claire-next); }
.status-card.strong { --status-color: var(--claire-strong); }
```

### Problem Card
```css
.problem-card {
  background: var(--claire-bg-card);
  border: 1px solid var(--claire-gray-200);
  border-radius: 12px;
  padding: 24px;
}
```

---

## Animation Guidelines

1. **Minimal motion**: Only status changes get transitions
2. **Duration**: 150-200ms max
3. **Easing**: `ease-out` for exits, `ease-in-out` for state changes
4. **No**: Bounces, springs, floating elements, confetti, mascot animations
5. **Yes**: Progress bar fills, node state changes, card reveals

---

## Design Validation Checklist

Before shipping any screen, ask:

- [ ] Can user see their weak spots in <3 seconds?
- [ ] Is next action obvious without reading?
- [ ] Does it feel like an analysis panel (not a game)?
- [ ] Zero Duolingo green (#58cc02)?
- [ ] Zero robot/lightbulb/book icons?
- [ ] Core hook visible: "Know what to study next"?
