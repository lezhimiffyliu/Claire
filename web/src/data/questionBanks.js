/**
 * Adaptive Diagnostic Question Bank — v2
 *
 * Design principles:
 *   1. ALEKS Knowledge Space Theory — minimum questions to locate user in knowledge graph
 *   2. Duolingo "Quick Win" — first question is genuinely trivial, builds confidence
 *   3. Real adaptive branching — the path through the test depends on answers
 *   4. UI never exposes branching — user always sees "Question N of 4"
 *
 * Tier system (each tier is a gateway, not just a difficulty label):
 *   T1 Foundation — pre-calc fluency, 2-second answer expected
 *   T2 Concept    — scenario-based conceptual understanding, NO calculation
 *   T3 UW Exam    — method recognition on UW midterm style problems
 *   T4 Elite      — "4.0 separator", catches reflexive mistakes from strong students
 *
 * Adaptive branching (replaces fixed 4-question set):
 *
 *   Q1: T1 main
 *     ├─ correct → Q2: T2 main
 *     └─ wrong   → Q2: T1 recovery (second chance, same tier)
 *
 *   Q2: T2 main / T1 recovery
 *     ├─ correct → Q3: T3 main
 *     └─ wrong   → Q3: T2 simplified (protect confidence)
 *
 *   Q3: T3 main / T2 simplified
 *     ├─ correct → Q4: T4 elite (challenge)
 *     └─ wrong   → Q4: T3 guided (method given, asks for execution)
 *
 *   Q4: dynamic based on running performance
 */

// =============================================================================
// TIER METADATA
// =============================================================================

export const TIER_INFO = {
  1: { name: 'Foundation', skill: 'Pre-calc Fluency',     color: '#2FBF9F' },
  2: { name: 'Concept',    skill: 'Core Understanding',   color: '#5B8DEF' },
  3: { name: 'UW Exam',    skill: 'Exam Execution',       color: '#0B1F3A' },
  4: { name: 'Elite',      skill: '4.0 Separator',        color: '#1A3A5C' },
}

// =============================================================================
// INLINE SVG HELPERS
// Returned as `svg` field on questions. Frontend should render with
// dangerouslySetInnerHTML or an SVG component. Always uses viewBox so it scales.
// =============================================================================

const SVG = {
  // Two perpendicular vectors (Math 126 T1)
  perpendicularVectors: `
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" style="max-width:240px">
      <defs>
        <marker id="arr1" markerWidth="10" markerHeight="10" refX="9" refY="3"
                orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#1cb0f6"/>
        </marker>
        <marker id="arr2" markerWidth="10" markerHeight="10" refX="9" refY="3"
                orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#ff9600"/>
        </marker>
      </defs>
      <line x1="100" y1="100" x2="100" y2="100" stroke="#ccc" stroke-width="1"/>
      <!-- vector a: pointing right -->
      <line x1="100" y1="100" x2="170" y2="100" stroke="#1cb0f6" stroke-width="3"
            marker-end="url(#arr1)"/>
      <text x="175" y="95" font-size="16" font-weight="bold" fill="#1cb0f6">a</text>
      <!-- vector b: pointing up -->
      <line x1="100" y1="100" x2="100" y2="30" stroke="#ff9600" stroke-width="3"
            marker-end="url(#arr2)"/>
      <text x="105" y="30" font-size="16" font-weight="bold" fill="#ff9600">b</text>
      <!-- right-angle marker -->
      <path d="M 100 90 L 110 90 L 110 100" fill="none" stroke="#999" stroke-width="1.5"/>
    </svg>
  `,

  // f'(x) sign chart: positive then negative at x=2 (Math 124 T2)
  derivativeSignChange: `
    <svg viewBox="0 0 320 180" xmlns="http://www.w3.org/2000/svg" style="max-width:360px">
      <!-- axes -->
      <line x1="20" y1="90" x2="300" y2="90" stroke="#333" stroke-width="1.5"/>
      <line x1="20" y1="20" x2="20" y2="160" stroke="#333" stroke-width="1.5"/>
      <text x="305" y="95" font-size="13" fill="#333">x</text>
      <text x="10" y="18" font-size="13" fill="#333">y</text>
      <!-- f'(x) curve: starts positive, crosses zero at x=2, becomes negative -->
      <path d="M 30 40 Q 90 40 160 90 Q 230 140 290 145"
            fill="none" stroke="#1cb0f6" stroke-width="3"/>
      <!-- x = 2 marker -->
      <line x1="160" y1="85" x2="160" y2="95" stroke="#333" stroke-width="2"/>
      <text x="155" y="110" font-size="13" fill="#333">2</text>
      <!-- label the curve -->
      <text x="240" y="160" font-size="14" font-weight="bold" fill="#1cb0f6">y = f'(x)</text>
      <!-- annotations -->
      <text x="60" y="35" font-size="12" fill="#58cc02">f' &gt; 0</text>
      <text x="220" y="135" font-size="12" fill="#ff4b4b">f' &lt; 0</text>
    </svg>
  `,

  // |x| graph for T4 trap question (Math 124)
  absoluteValueGraph: `
    <svg viewBox="0 0 240 180" xmlns="http://www.w3.org/2000/svg" style="max-width:280px">
      <line x1="20" y1="150" x2="220" y2="150" stroke="#333" stroke-width="1.5"/>
      <line x1="120" y1="20" x2="120" y2="170" stroke="#333" stroke-width="1.5"/>
      <text x="225" y="155" font-size="13" fill="#333">x</text>
      <text x="125" y="18" font-size="13" fill="#333">y</text>
      <!-- |x| graph -->
      <path d="M 30 60 L 120 150 L 210 60" fill="none" stroke="#ce82ff" stroke-width="3"/>
      <!-- highlight the corner -->
      <circle cx="120" cy="150" r="5" fill="#ff4b4b"/>
      <text x="130" y="170" font-size="13" fill="#333">x = 0</text>
      <text x="170" y="50" font-size="14" font-weight="bold" fill="#ce82ff">y = |x|</text>
    </svg>
  `,

  // Riemann sum / accumulation visual (Math 125 T2)
  accumulationVisual: `
    <svg viewBox="0 0 320 180" xmlns="http://www.w3.org/2000/svg" style="max-width:360px">
      <line x1="20" y1="150" x2="300" y2="150" stroke="#333" stroke-width="1.5"/>
      <line x1="40" y1="20" x2="40" y2="160" stroke="#333" stroke-width="1.5"/>
      <text x="305" y="155" font-size="13" fill="#333">t (min)</text>
      <text x="10" y="20" font-size="11" fill="#333">r(t)</text>
      <!-- rate curve: increasing then steady -->
      <path d="M 40 130 Q 100 100 160 70 Q 220 60 280 60"
            fill="none" stroke="#1cb0f6" stroke-width="3"/>
      <!-- shaded area from 0 to 5 -->
      <path d="M 40 150 L 40 130 Q 100 100 160 70 Q 220 60 280 60 L 280 150 Z"
            fill="#1cb0f6" fill-opacity="0.18"/>
      <text x="120" y="115" font-size="13" fill="#1cb0f6" font-weight="bold">total water?</text>
      <!-- t markers -->
      <line x1="40" y1="148" x2="40" y2="155" stroke="#333" stroke-width="1.5"/>
      <text x="36" y="170" font-size="12" fill="#333">0</text>
      <line x1="280" y1="148" x2="280" y2="155" stroke="#333" stroke-width="1.5"/>
      <text x="276" y="170" font-size="12" fill="#333">5</text>
    </svg>
  `,

  // Disk region for polar coordinates (Math 126 T3)
  diskRegion: `
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" style="max-width:240px">
      <line x1="20" y1="100" x2="180" y2="100" stroke="#333" stroke-width="1.5"/>
      <line x1="100" y1="20" x2="100" y2="180" stroke="#333" stroke-width="1.5"/>
      <text x="183" y="105" font-size="13" fill="#333">x</text>
      <text x="105" y="20" font-size="13" fill="#333">y</text>
      <!-- disk x^2 + y^2 <= 4, radius 2 in graph units, scale = 30px/unit -->
      <circle cx="100" cy="100" r="60" fill="#ff9600" fill-opacity="0.25"
              stroke="#ff9600" stroke-width="2.5"/>
      <text x="115" y="95" font-size="14" font-weight="bold" fill="#ff9600">R</text>
      <text x="40" y="175" font-size="13" fill="#333">x² + y² ≤ 4</text>
    </svg>
  `,

  // Level curves with gradient arrow (Math 126 T2 — replaces "hiking" prose)
  gradientOnLevelCurves: `
    <svg viewBox="0 0 260 200" xmlns="http://www.w3.org/2000/svg" style="max-width:300px">
      <defs>
        <marker id="grad-arr" markerWidth="10" markerHeight="10" refX="9" refY="3"
                orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#ce82ff"/>
        </marker>
      </defs>
      <!-- nested level curves (simulating a hill) -->
      <ellipse cx="130" cy="100" rx="100" ry="70" fill="none" stroke="#aaa" stroke-width="1.5"/>
      <ellipse cx="130" cy="100" rx="75"  ry="50" fill="none" stroke="#aaa" stroke-width="1.5"/>
      <ellipse cx="130" cy="100" rx="50"  ry="32" fill="none" stroke="#aaa" stroke-width="1.5"/>
      <ellipse cx="130" cy="100" rx="25"  ry="16" fill="none" stroke="#aaa" stroke-width="1.5"/>
      <!-- labels for level values -->
      <text x="35"  y="100" font-size="11" fill="#666">f=1</text>
      <text x="62"  y="100" font-size="11" fill="#666">f=2</text>
      <text x="86"  y="100" font-size="11" fill="#666">f=3</text>
      <text x="115" y="103" font-size="11" fill="#666">f=4</text>
      <!-- a point P on a level curve -->
      <circle cx="180" cy="100" r="4" fill="#333"/>
      <text x="186" y="96" font-size="13" font-weight="bold" fill="#333">P</text>
      <!-- candidate gradient direction (the correct one: outward = uphill is FALSE here;
           outward goes to LOWER level curves, so this graphic shows ∇f pointing INWARD
           toward the peak) -->
      <line x1="180" y1="100" x2="148" y2="100" stroke="#ce82ff" stroke-width="3"
            marker-end="url(#grad-arr)"/>
      <text x="148" y="92" font-size="13" font-weight="bold" fill="#ce82ff">∇f</text>
      <text x="20" y="190" font-size="12" fill="#666">Level curves of f(x,y); peak at center</text>
    </svg>
  `,
}

// =============================================================================
// MATH 124 — Differential Calculus
// =============================================================================

const MATH_124 = [
  // ---------- T1: Foundation ----------
  {
    id: 'm124_t1_main',
    tier: 1,
    role: 'main',
    topic: 'Basic Derivatives',
    taxonomyTopic: 'derivative_rules',
    skill: 'Power Rule',
    question: '$\\displaystyle\\frac{d}{dx}\\left(x^{2}\\right) = \\;?$',
    options: ['$x$', '$2x$', '$2x^{2}$', '$x^{2}$'],
    correct: 1,
    explanation: 'Power rule: bring the exponent down, reduce by 1.',
    skillGap: 'derivative_rules',
  },
  {
    id: 'm124_t1_recovery',
    tier: 1,
    role: 'recovery',
    topic: 'Basic Derivatives',
    taxonomyTopic: 'derivative_rules',
    skill: 'Constant Rule',
    question: '$\\displaystyle\\frac{d}{dx}(7) = \\;?$',
    options: ['$7$', '$1$', '$0$', '$7x$'],
    correct: 2,
    explanation: 'The derivative of any constant is 0 — constants don\'t change.',
    skillGap: 'derivative_rules',
  },

  // ---------- T2: Concept (visual, no calculation) ----------
  {
    id: 'm124_t2_main',
    tier: 2,
    role: 'main',
    topic: 'Derivative Interpretation',
    taxonomyTopic: 'curve_analysis',
    skill: 'First Derivative Test (visual)',
    question: 'The graph below shows $y = f\'(x)$. What happens to the **original function** $f(x)$ at $x = 2$?',
    svg: SVG.derivativeSignChange,
    options: [
      '$f$ has a local minimum',
      '$f$ has an inflection point',
      '$f$ has a local maximum',
      '$f$ is undefined at $x = 2$',
    ],
    correct: 2,
    explanation: '$f\'$ goes from positive to negative at $x=2$, so $f$ goes from increasing to decreasing — a local maximum.',
    skillGap: 'curve_analysis',
  },
  {
    id: 'm124_t2_simplified',
    tier: 2,
    role: 'simplified',
    topic: 'Derivative Interpretation',
    taxonomyTopic: 'curve_analysis',
    skill: 'Sign of Derivative',
    question: 'If $f\'(x) > 0$ on an interval, then on that interval $f(x)$ is:',
    options: ['Decreasing', 'Increasing', 'Constant', 'Concave up'],
    correct: 1,
    explanation: 'Positive derivative means the function is going up — that\'s the definition of increasing.',
    skillGap: 'curve_analysis',
  },

  // ---------- T3: UW Exam ----------
  {
    id: 'm124_t3_main',
    tier: 3,
    role: 'main',
    topic: 'Differentiation',
    taxonomyTopic: 'derivative_rules',
    skill: 'Composite Function Recognition',
    question: 'You need to differentiate $f(x) = e^{\\sin(x)}$. Which is the **outermost** rule you apply first?',
    options: [
      'Product rule',
      'Power rule',
      'Quotient rule',
      'Chain rule (derivative of $e^{u}$)',
    ],
    correct: 3,
    explanation: 'Outer function is $e^{(\\cdot)}$, inner is $\\sin x$. Chain rule: $(e^{u})\' = e^{u}\\cdot u\'$.',
    skillGap: 'derivative_rules',
  },
  {
    id: 'm124_t3_guided',
    tier: 3,
    role: 'guided',
    topic: 'Differentiation',
    taxonomyTopic: 'derivative_rules',
    skill: 'Chain Rule Execution',
    question: 'Using the chain rule on $f(x) = (3x + 1)^{4}$, the derivative is $4(3x+1)^{3} \\cdot \\square$. What goes in $\\square$?',
    options: ['$1$', '$3$', '$3x + 1$', '$3x$'],
    correct: 1,
    explanation: 'The "inner" function is $3x + 1$, whose derivative is $3$. Chain rule multiplies by this.',
    skillGap: 'derivative_rules',
  },

  // ---------- T4: Elite (4.0 separators) ----------
  {
    id: 'm124_t4_main',
    tier: 4,
    role: 'main',
    topic: 'Differentiability',
    taxonomyTopic: 'curve_analysis',
    skill: 'Differentiability vs Extrema',
    question: 'Consider $f(x) = |x|$ at $x = 0$ (graph below). Which statement is correct?',
    svg: SVG.absoluteValueGraph,
    options: [
      '$f\'(0) = 0$, because $x = 0$ is a minimum',
      '$x = 0$ is not a local extremum, since $f$ isn\'t differentiable there',
      '$f\'(0) = 1$',
      '$f\'(0)$ does **not exist**, but $x = 0$ is still a local minimum',
    ],
    correct: 3,
    explanation: 'Sharp corner → derivative undefined. But extrema can still occur at points where $f\'$ doesn\'t exist (these are called critical points too). The 3.5 trap: assuming $f\' = 0$ is required for an extremum.',
    skillGap: 'curve_analysis',
  },
  {
    id: 'm124_t4_alt',
    tier: 4,
    role: 'main',
    topic: 'Implicit Differentiation',
    taxonomyTopic: 'implicit_differentiation',
    skill: 'When dy/dx Has y in It',
    question: 'You differentiate $x^{2} + y^{2} = 25$ implicitly and find $\\frac{dy}{dx} = -\\frac{x}{y}$. At the point $(0, 5)$, what is $\\frac{dy}{dx}$?',
    options: [
      'Undefined (vertical tangent)',
      '$-1$',
      '$0$ (horizontal tangent)',
      'Cannot evaluate without more info',
    ],
    correct: 2,
    explanation: '$-x/y = -0/5 = 0$. The 3.5 trap: students panic when $y$ is in the denominator and forget to actually plug in. At the top of the circle, the tangent is horizontal, which matches $dy/dx = 0$.',
    skillGap: 'implicit_differentiation',
  },
]

// =============================================================================
// MATH 125 — Integral Calculus
// =============================================================================

const MATH_125 = [
  // ---------- T1: Foundation ----------
  {
    id: 'm125_t1_main',
    tier: 1,
    role: 'main',
    topic: 'Basic Antiderivatives',
    taxonomyTopic: 'antiderivatives_and_riemann_sums',
    skill: 'Reverse Power Rule',
    question: '$\\displaystyle\\int x \\, dx = \\;?$',
    options: [
      '$x^{2} + C$',
      '$1 + C$',
      '$\\dfrac{x^{2}}{2} + C$',
      '$\\dfrac{x}{2} + C$',
    ],
    correct: 2,
    explanation: 'Reverse power rule: add 1 to the exponent, divide by the new exponent.',
    skillGap: 'antiderivatives_and_riemann_sums',
  },
  {
    id: 'm125_t1_recovery',
    tier: 1,
    role: 'recovery',
    topic: 'Basic Antiderivatives',
    taxonomyTopic: 'antiderivatives_and_riemann_sums',
    skill: 'Antiderivative of Constant',
    question: '$\\displaystyle\\int 3 \\, dx = \\;?$',
    options: ['$3 + C$', '$\\dfrac{3}{x} + C$', '$0 + C$', '$3x + C$'],
    correct: 3,
    explanation: 'The antiderivative of a constant $k$ is $kx + C$.',
    skillGap: 'antiderivatives_and_riemann_sums',
  },

  // ---------- T2: Concept (scenario, not formula recitation) ----------
  {
    id: 'm125_t2_main',
    tier: 2,
    role: 'main',
    topic: 'Integral as Accumulation',
    taxonomyTopic: 'fundamental_theorem_of_calculus',
    skill: 'Interpreting Integrals in Context',
    question: 'Water flows into a tank at a rate $r(t)$ liters per minute (graph below). How much water enters from $t = 0$ to $t = 5$?',
    svg: SVG.accumulationVisual,
    options: [
      '$r(5) - r(0)$',
      '$\\displaystyle\\int_{0}^{5} r(t)\\,dt$',
      '$r\'(5)$',
      '$5 \\cdot r(5)$',
    ],
    correct: 1,
    explanation: 'A rate, integrated over time, gives total accumulation. The shaded area under $r(t)$ from 0 to 5 is exactly the total water added.',
    skillGap: 'fundamental_theorem_of_calculus',
  },
  {
    id: 'm125_t2_simplified',
    tier: 2,
    role: 'simplified',
    topic: 'Integral as Accumulation',
    taxonomyTopic: 'antiderivatives_and_riemann_sums',
    skill: 'Integral as Area',
    question: 'For a positive continuous function $f(x)$ on $[a, b]$, the value of $\\displaystyle\\int_{a}^{b} f(x)\\,dx$ represents:',
    options: [
      'The area under the curve from $a$ to $b$',
      'The slope of $f$ at $x = b$',
      'The maximum value of $f$',
      'The length of the curve',
    ],
    correct: 0,
    explanation: 'For a positive function, the definite integral is geometrically the area trapped between the curve and the x-axis.',
    skillGap: 'antiderivatives_and_riemann_sums',
  },

  // ---------- T3: UW Exam ----------
  {
    id: 'm125_t3_main',
    tier: 3,
    role: 'main',
    topic: 'Integration Techniques',
    taxonomyTopic: 'partial_fractions',
    skill: 'Method Selection',
    question: 'Which technique is the best fit for $\\displaystyle\\int \\frac{3x + 5}{x^{2} + 4x + 3}\\,dx$?',
    options: [
      'U-substitution with $u = x^{2} + 4x + 3$',
      'Integration by parts',
      'Partial fractions',
      'Trig substitution',
    ],
    correct: 2,
    explanation: 'Denominator factors as $(x+1)(x+3)$. Numerator is **not** a multiple of the derivative $2x+4$, so u-sub fails. Partial fractions is the standard route.',
    skillGap: 'partial_fractions',
  },
  {
    id: 'm125_t3_guided',
    tier: 3,
    role: 'guided',
    topic: 'Integration Techniques',
    taxonomyTopic: 'substitution',
    skill: 'U-Substitution Setup',
    question: 'For $\\displaystyle\\int 2x \\cdot e^{x^{2}}\\,dx$, you choose $u = x^{2}$. Then $du = \\;?$',
    options: [
      '$x\\,dx$',
      '$2\\,dx$',
      '$x^{2}\\,dx$',
      '$2x\\,dx$',
    ],
    correct: 3,
    explanation: 'Differentiate $u = x^{2}$: $du/dx = 2x$, so $du = 2x\\,dx$. This makes the integral become $\\int e^{u}\\,du$.',
    skillGap: 'substitution',
  },

  // ---------- T4: Elite (4.0 separators) ----------
  {
    id: 'm125_t4_main',
    tier: 4,
    role: 'main',
    topic: 'Improper Integrals',
    taxonomyTopic: 'improper_integrals',
    skill: 'Necessary vs Sufficient',
    question: 'For the harmonic series $\\displaystyle\\sum_{n=1}^{\\infty} \\frac{1}{n}$, we have $\\lim_{n\\to\\infty} \\frac{1}{n} = 0$. Therefore:',
    options: [
      'The series converges, since the terms go to 0',
      'The series **diverges** (the limit being 0 is not enough to conclude convergence)',
      'The series converges by the $p$-test',
      'You cannot determine convergence without more information',
    ],
    correct: 1,
    explanation: '$a_n \\to 0$ is **necessary** for convergence but not **sufficient**. The harmonic series is the canonical counterexample: terms shrink, sum still diverges. The 3.5 trap: confusing the divergence test (a one-way arrow) with a convergence test.',
    skillGap: 'improper_integrals',
  },
  {
    id: 'm125_t4_alt',
    tier: 4,
    role: 'main',
    topic: 'Improper Integrals',
    taxonomyTopic: 'improper_integrals',
    skill: 'Discontinuity Inside Bounds',
    question: 'A student computes $\\displaystyle\\int_{-1}^{1} \\frac{1}{x^{2}}\\,dx$ as $\\left[-\\frac{1}{x}\\right]_{-1}^{1} = -1 - 1 = -2$. What\'s wrong?',
    options: [
      'Nothing — the answer is correct',
      'The antiderivative should be $\\ln|x|$',
      'The bounds need to be reversed',
      'The integrand is undefined at $x = 0$, so this is an improper integral that actually diverges',
    ],
    correct: 3,
    explanation: '$1/x^{2}$ blows up at $x = 0$, which is **inside** $[-1, 1]$. You must split at the discontinuity and take limits — and both halves diverge. Getting a negative answer for a strictly positive integrand should have been the giveaway. This is a textbook 3.5 trap.',
    skillGap: 'improper_integrals',
  },
]

// =============================================================================
// MATH 126 — Multivariable Calculus & Series
// =============================================================================

const MATH_126 = [
  // ---------- T1: Foundation (visual, not memorization) ----------
  {
    id: 'm126_t1_main',
    tier: 1,
    role: 'main',
    topic: 'Vectors',
    taxonomyTopic: 'vectors_and_geometry',
    skill: 'Geometric Reading',
    question: 'Looking at the two vectors below, they are:',
    svg: SVG.perpendicularVectors,
    options: ['Parallel', 'Equal', 'Perpendicular', 'Both zero'],
    correct: 2,
    explanation: 'They meet at a right angle (90°), so they\'re perpendicular (also called orthogonal). For such vectors, $\\vec{a}\\cdot\\vec{b} = 0$.',
    skillGap: 'vectors_and_geometry',
  },
  {
    id: 'm126_t1_recovery',
    tier: 1,
    role: 'recovery',
    topic: 'Vectors',
    taxonomyTopic: 'vectors_and_geometry',
    skill: 'Vector Addition',
    question: 'If $\\vec{u} = \\langle 1, 2\\rangle$ and $\\vec{v} = \\langle 3, 4\\rangle$, then $\\vec{u} + \\vec{v} = \\;?$',
    options: [
      '$\\langle 3, 8\\rangle$',
      '$\\langle 4, 8\\rangle$',
      '$\\langle 2, 2\\rangle$',
      '$\\langle 4, 6\\rangle$',
    ],
    correct: 3,
    explanation: 'Vector addition is component-wise: $\\langle 1+3,\\, 2+4\\rangle = \\langle 4, 6\\rangle$.',
    skillGap: 'vectors_and_geometry',
  },

  // ---------- T2: Concept (no calculation, tests understanding) ----------
  {
    id: 'm126_t2_main',
    tier: 2,
    role: 'main',
    topic: 'Multivariable Calculus',
    taxonomyTopic: 'multivariable_optimization',
    skill: 'Critical Point Classification (Second Derivative Test)',
    question: 'At point $(1, 2)$, the function $f(x,y)$ satisfies $f_x = 0$ and $f_y = 0$. The second partials are $f_{xx} = 2$, $f_{yy} = 8$, $f_{xy} = 5$. What type of point is $(1, 2)$?',
    options: [
      'Local minimum',
      'Saddle point',
      'Local maximum',
      'Cannot be determined',
    ],
    correct: 1,
    explanation: 'The discriminant $D = f_{xx} \\cdot f_{yy} - (f_{xy})^2 = 2 \\cdot 8 - 25 = -9 < 0$, so it\'s a saddle point. The 3.5 trap: seeing $f_{xx} > 0$ and $f_{yy} > 0$ and concluding "local min" without checking the mixed partial.',
    skillGap: 'multivariable_optimization',
  },
  {
    id: 'm126_t2_simplified',
    tier: 2,
    role: 'simplified',
    topic: 'Multivariable Calculus',
    taxonomyTopic: 'partial_derivatives',
    skill: 'Partial Derivative Meaning',
    question: 'For $f(x, y)$, the partial derivative $\\dfrac{\\partial f}{\\partial x}$ measures:',
    options: [
      'How $f$ changes as both $x$ and $y$ vary',
      'The total change in $f$',
      'How $f$ changes as $x$ varies, with $y$ held constant',
      'The slope of a level curve',
    ],
    correct: 2,
    explanation: 'A partial derivative isolates one variable: you freeze the others and ask how $f$ responds to changes in just that one.',
    skillGap: 'partial_derivatives',
  },

  // ---------- T3: UW Exam ----------
  {
    id: 'm126_t3_main',
    tier: 3,
    role: 'main',
    topic: 'Double Integrals',
    taxonomyTopic: 'polar_coordinates',
    skill: 'Coordinate Choice',
    question: 'You need to compute $\\displaystyle\\iint_{R} f(x,y)\\,dA$ over the disk $R$ shown below. Which coordinate system gives the simplest bounds?',
    svg: SVG.diskRegion,
    options: [
      'Cartesian with $x$ outer, $y$ inner',
      'Spherical coordinates',
      'Polar coordinates: $0 \\leq r \\leq 2$, $0 \\leq \\theta \\leq 2\\pi$',
      'Cylindrical coordinates',
    ],
    correct: 2,
    explanation: 'Circular symmetry → polar. The bounds become rectangular in $(r, \\theta)$, whereas Cartesian gives $\\sqrt{}$-bounds. Don\'t forget the Jacobian: $dA = r\\,dr\\,d\\theta$.',
    skillGap: 'polar_coordinates',
  },
  {
    id: 'm126_t3_guided',
    tier: 3,
    role: 'guided',
    topic: 'Double Integrals',
    taxonomyTopic: 'double_integrals',
    skill: 'Polar Jacobian',
    question: 'When converting a double integral to polar coordinates, $dA$ becomes:',
    options: ['$dr\\,d\\theta$', '$r\\,dr\\,d\\theta$', '$r^{2}\\,dr\\,d\\theta$', '$\\dfrac{1}{r}\\,dr\\,d\\theta$'],
    correct: 1,
    explanation: 'The Jacobian for polar conversion is $r$, so $dA = r\\,dr\\,d\\theta$. Forgetting this $r$ is the most common polar mistake on UW exams.',
    skillGap: 'double_integrals',
  },

  // ---------- T4: Elite (4.0 separators) ----------
  {
    id: 'm126_t4_main',
    tier: 4,
    role: 'main',
    topic: 'Constrained Optimization',
    taxonomyTopic: 'multivariable_optimization',
    skill: 'What Lagrange Actually Gives',
    question: 'You apply Lagrange multipliers to maximize $f$ subject to $g = c$, and solve $\\nabla f = \\lambda\\nabla g$ to find three points $A$, $B$, $C$ all satisfying this. The maximum is:',
    options: [
      'Always point $A$ (the first one found)',
      'The point where $\\lambda$ is largest',
      'Always exists at every Lagrange point',
      'Whichever of $A$, $B$, $C$ gives the **largest value of $f$** — Lagrange only finds candidates',
    ],
    correct: 3,
    explanation: 'Lagrange equations identify **candidate** points (analogous to critical points). You still have to evaluate $f$ at each candidate and compare. The 3.5 trap: stopping after solving $\\nabla f = \\lambda\\nabla g$ and assuming you\'re done.',
    skillGap: 'multivariable_optimization',
  },
  {
    id: 'm126_t4_alt',
    tier: 4,
    role: 'main',
    topic: 'Taylor Polynomials',
    taxonomyTopic: 'taylor_polynomials_and_series',
    skill: 'Error Bound (Taylor\'s Inequality)',
    question: 'You approximate $e^{0.1}$ using the degree-2 Taylor polynomial $T_2(x)$ of $f(x) = e^x$ centered at $x = 0$. According to Taylor\'s Inequality, the error bound $|R_2(0.1)|$ is:',
    options: [
      '$\\dfrac{1}{3!}(0.1)^3$',
      '$\\dfrac{M}{3!}\\,|0.1|^3$, where $M$ is an upper bound for $|f\'\'\'(x)|$ on $[0, 0.1]$',
      '$\\dfrac{f\'\'\'(0)}{3!}(0.1)^3$',
      '$0$, because $e^x$ is analytic and equals its Taylor series',
    ],
    correct: 1,
    explanation: 'Taylor\'s Inequality: $|R_n(x)| \\leq \\frac{M}{(n+1)!}|x-a|^{n+1}$, where $M$ must be an **upper bound** for $|f^{(n+1)}|$ on the interval, not a point value. The 3.5 trap: writing $1$ instead of $M$, or using $f\'\'\'(0)$ (a specific value) instead of an upper bound. "$e^x$ is analytic" is irrelevant — $T_2$ is a finite approximation with nonzero error.',
    skillGap: 'taylor_polynomials_and_series',
  },
]

// =============================================================================
// QUESTION BANKS (export)
// =============================================================================

export const QUESTION_BANKS = {
  math124: MATH_124,
  math125: MATH_125,
  math126: MATH_126,
}

// =============================================================================
// ADAPTIVE BRANCHING ENGINE
// =============================================================================

/**
 * Pick a question by tier + role, excluding already-asked IDs.
 * If multiple matches exist, pick randomly for replay variety.
 */
function pickQuestion(course, tier, role, askedIds) {
  const bank = QUESTION_BANKS[course] || []
  // First try exact tier+role match
  const exact = bank.filter(
    (q) => q.tier === tier && q.role === role && !askedIds.includes(q.id)
  )
  if (exact.length > 0) {
    return exact[Math.floor(Math.random() * exact.length)]
  }
  // Fallback 1: same tier, any role
  const sameTier = bank.filter(
    (q) => q.tier === tier && !askedIds.includes(q.id)
  )
  if (sameTier.length > 0) {
    return sameTier[Math.floor(Math.random() * sameTier.length)]
  }
  // Fallback 2: walk down tiers until we find any unused question
  for (let t = tier - 1; t >= 1; t--) {
    const lower = bank.filter((q) => q.tier === t && !askedIds.includes(q.id))
    if (lower.length > 0) {
      return lower[Math.floor(Math.random() * lower.length)]
    }
  }
  // Fallback 3: walk up tiers
  for (let t = tier + 1; t <= 4; t++) {
    const higher = bank.filter((q) => q.tier === t && !askedIds.includes(q.id))
    if (higher.length > 0) {
      return higher[Math.floor(Math.random() * higher.length)]
    }
  }
  return null
}

/**
 * Get the next question in the adaptive sequence.
 *
 * @param {Array} answers — array of {questionId, isCorrect, skipped} so far (length 0–3)
 * @param {string} course — 'math124' | 'math125' | 'math126'
 * @returns {object|null} { question, questionNumber, totalQuestions, progressPercent }
 *                         or null when test is complete
 *
 * Branching:
 *   answers.length === 0 → Q1: T1 main
 *   answers.length === 1 → if Q1 right: T2 main; if wrong: T1 recovery
 *   answers.length === 2 → if Q2 right: T3 main; if wrong: T2 simplified
 *   answers.length === 3 → if Q3 right: T4 main (challenge); if wrong: T3 guided
 *   answers.length >= 4  → null (done)
 *
 * progressPercent is intentionally biased: 30% / 60% / 85% / 100%
 * to mirror Duolingo's "felt progress" pacing.
 */
export function getNextQuestion(answers, course) {
  if (!QUESTION_BANKS[course]) {
    throw new Error(`Unknown course: ${course}`)
  }
  const askedIds = answers.map((a) => a.questionId)
  const n = answers.length

  if (n >= 4) return null

  const TOTAL = 4
  const PROGRESS = [30, 60, 85, 100] // shown AFTER answering question (n+1)
  const progressPercent = PROGRESS[n]

  let tier, role

  if (n === 0) {
    // Q1 always T1 main
    tier = 1; role = 'main'
  } else if (n === 1) {
    const lastCorrect = answers[0].isCorrect
    if (lastCorrect) { tier = 2; role = 'main' }
    else             { tier = 1; role = 'recovery' }
  } else if (n === 2) {
    // Q2 was either T2 main (if Q1 right) or T1 recovery (if Q1 wrong)
    const q2 = answers[1]
    const q2Question = QUESTION_BANKS[course].find((x) => x.id === q2.questionId)
    const q2WasRecovery = q2Question && q2Question.role === 'recovery'

    if (q2WasRecovery) {
      // Student is climbing back up — give them T2 main next, regardless of Q2 result
      // (we're being generous: they earned the chance to try the concept tier)
      tier = 2; role = 'main'
    } else if (q2.isCorrect) {
      tier = 3; role = 'main'
    } else {
      tier = 2; role = 'simplified'
    }
  } else {
    // n === 3, deciding Q4 based on running performance
    const correctCount = answers.filter((a) => a.isCorrect).length
    const lastCorrect = answers[2].isCorrect
    // Find what the highest tier the student has *correctly* answered so far
    const bank = QUESTION_BANKS[course]
    let highestCorrectTier = 0
    for (const a of answers) {
      if (!a.isCorrect) continue
      const q = bank.find((x) => x.id === a.questionId)
      if (q && q.tier > highestCorrectTier) highestCorrectTier = q.tier
    }

    if (lastCorrect && highestCorrectTier >= 3) {
      // Earned the elite challenge
      tier = 4; role = 'main'
    } else if (lastCorrect && highestCorrectTier === 2) {
      // Climbing back, give T3 main as the final test
      tier = 3; role = 'main'
    } else if (correctCount >= 2) {
      // Some momentum, but failed last — give a guided T3
      tier = 3; role = 'guided'
    } else {
      // Struggling — finish with a T2 simplified to end on something they can do
      tier = 2; role = 'simplified'
    }
  }

  const question = pickQuestion(course, tier, role, askedIds)
  if (!question) return null

  return {
    question,
    questionNumber: n + 1,
    totalQuestions: TOTAL,
    progressPercent,
    // Display hint for UI: never expose actual difficulty/branching
    displayLabel: `Question ${n + 1} of ${TOTAL}`,
  }
}

// =============================================================================
// RESULT ANALYSIS
// =============================================================================

/**
 * Map an asked question's actual tier to a "highest achieved tier" inference.
 *
 * Because we branch, simply counting "passed tiers" misses the point.
 * What matters is: what's the highest tier the student demonstrated competence at?
 */
function inferHighestTier(answers, course) {
  const bank = QUESTION_BANKS[course] || []
  let highest = 0
  for (const a of answers) {
    if (!a.isCorrect) continue
    const q = bank.find((x) => x.id === a.questionId)
    if (!q) continue
    // Recovery / simplified / guided questions are "remedial" — they prove
    // the student can handle that tier's basics, not the full tier
    const effectiveTier =
      q.role === 'main' ? q.tier : Math.max(q.tier - 1, 1)
    if (effectiveTier > highest) highest = effectiveTier
  }
  return highest
}

/**
 * Analyze test results and return a structured report.
 *
 * @param {Array} answers — array of {questionId, isCorrect, skipped}
 * @param {string} course
 * @returns full report including skill level, gaps, strengths, and a
 *          "next step hook" for the UI to drive registration / learning path.
 */
export function analyzeResults(answers, course) {
  const bank = QUESTION_BANKS[course] || []
  const highestTier = inferHighestTier(answers, course)

  // Map highest demonstrated tier to a level
  // Note: No emojis in Claire v2 design system
  let skillLevel, skillEmoji, skillColor, levelDescription
  if (highestTier <= 1) {
    skillLevel = 'Building Foundations'
    skillEmoji = ''
    skillColor = '#E85D5D' // weak
    levelDescription = 'Core gaps detected. We\'ll target the fundamentals first.'
  } else if (highestTier === 2) {
    skillLevel = 'Almost There'
    skillEmoji = ''
    skillColor = '#5B8DEF' // next
    levelDescription = 'Concepts are there. Exam execution needs work.'
  } else if (highestTier === 3) {
    skillLevel = 'Exam Ready'
    skillEmoji = ''
    skillColor = '#2FBF9F' // strong
    levelDescription = 'You can pass. Let\'s push for the top of the curve.'
  } else {
    skillLevel = '4.0 Candidate'
    skillEmoji = ''
    skillColor = '#0B1F3A' // navy
    levelDescription = 'Elite level. We\'ll catch the rare gaps.'
  }

  // Build gaps & strengths
  const gaps = []
  const strengths = []
  for (const a of answers) {
    const q = bank.find((x) => x.id === a.questionId)
    if (!q) continue
    const entry = {
      tier: q.tier,
      tierName: TIER_INFO[q.tier].name,
      topic: q.topic,
      skill: q.skill,
      skillGap: q.skillGap,
      color: TIER_INFO[q.tier].color,
    }
    if (a.skipped) {
      gaps.push({ ...entry, reason: 'skipped' })
    } else if (!a.isCorrect) {
      gaps.push({ ...entry, reason: 'incorrect' })
    } else {
      strengths.push(entry)
    }
  }

  // Primary blocker — the lowest-tier gap is what to focus on first
  const sortedGaps = [...gaps].sort((a, b) => a.tier - b.tier)
  const primaryGap = sortedGaps[0] || null

  let blockerMessage = ''
  if (!primaryGap) {
    blockerMessage = 'No blockers found in this diagnostic. We\'ll start you on advanced material.'
  } else {
    if (primaryGap.tier === 1) {
      blockerMessage = `${primaryGap.skillGap} is blocking you. This is pre-calc territory — once we patch it, calculus gets dramatically easier.`
    } else if (primaryGap.tier === 2) {
      blockerMessage = `Your concepts in "${primaryGap.skillGap}" need reinforcement. This is the difference between memorizing and understanding.`
    } else if (primaryGap.tier === 3) {
      blockerMessage = `${primaryGap.skillGap} is your exam blocker. UW midterms test exactly this kind of execution.`
    } else {
      blockerMessage = `${primaryGap.skillGap} is what separates 3.5 from 4.0. You\'re close — the gap is small but specific.`
    }
  }

  // Predicted grade range — purely heuristic, used to make results feel personal
  let predictedGrade
  if (highestTier <= 1) predictedGrade = '2.0 – 2.7'
  else if (highestTier === 2) predictedGrade = '2.7 – 3.2'
  else if (highestTier === 3) predictedGrade = '3.2 – 3.7'
  else predictedGrade = '3.7 – 4.0'

  return {
    skillLevel,
    skillEmoji,
    skillColor,
    levelDescription,
    highestTier,
    gaps,
    strengths,
    primaryGap,
    blockerMessage,
    predictedGrade,
    totalAnswered: answers.length,
    correctCount: answers.filter((a) => a.isCorrect).length,
  }
}

// =============================================================================
// LEGACY COMPATIBILITY (do not remove without updating callers)
// =============================================================================

/**
 * @deprecated — kept for backward compatibility only. Use getNextQuestion instead.
 * Returns the *non-adaptive* set of T1/T2/T3/T4 main questions for cases where
 * you really do want a fixed 4-question render (e.g., admin preview).
 */
export function getBalancedQuestionSet(course) {
  const bank = QUESTION_BANKS[course] || QUESTION_BANKS.math126
  const result = []
  for (let tier = 1; tier <= 4; tier++) {
    const candidates = bank.filter((q) => q.tier === tier && q.role === 'main')
    if (candidates.length > 0) {
      result.push(candidates[Math.floor(Math.random() * candidates.length)])
    }
  }
  return result
}