# Limits

## Pattern Recognition
- Keywords: "limit", "lim", "approaches", "tends to", "as x →"
- Continuity at a point, asymptotic behavior
- L'Hôpital's rule applications (indeterminate forms)

## Key Formulas (MUST MEMORIZE)

### Special Limits
| Limit | Value |
|-------|-------|
| $\lim_{x \to 0} \frac{\sin(x)}{x}$ | $1$ |
| $\lim_{x \to 0} \frac{1 - \cos(x)}{x}$ | $0$ |
| $\lim_{x \to 0} \frac{1 - \cos(x)}{x^2}$ | $\frac{1}{2}$ |
| $\lim_{x \to 0} \frac{e^x - 1}{x}$ | $1$ |
| $\lim_{x \to 0} \frac{\ln(1+x)}{x}$ | $1$ |
| $\lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x$ | $e$ |
| $\lim_{x \to 0} (1 + x)^{1/x}$ | $e$ |
| $\lim_{x \to \infty} \frac{e^x}{x^n}$ | $\infty$ (exp beats polynomial) |
| $\lim_{x \to \infty} \frac{x^n}{\ln(x)}$ | $\infty$ (polynomial beats log) |

### L'Hôpital's Rule
If $\lim_{x \to a} \frac{f(x)}{g(x)}$ gives $\frac{0}{0}$ or $\frac{\infty}{\infty}$:

$$\lim_{x \to a} \frac{f(x)}{g(x)} = \lim_{x \to a} \frac{f'(x)}{g'(x)}$$

**Critical:** Differentiate numerator and denominator **separately** (NOT quotient rule!)

### Indeterminate Forms
| Form | How to Handle |
|------|---------------|
| $\frac{0}{0}$ | L'Hôpital or factor/simplify |
| $\frac{\infty}{\infty}$ | L'Hôpital or divide by highest power |
| $0 \cdot \infty$ | Rewrite as $\frac{0}{1/\infty}$ or $\frac{\infty}{1/0}$ |
| $\infty - \infty$ | Combine fractions or rationalize |
| $0^0, 1^\infty, \infty^0$ | Take ln, use $e^{\ln(...)}$ |

### Limits at Infinity for Rational Functions
For $\lim_{x \to \infty} \frac{a_n x^n + ...}{b_m x^m + ...}$:

| Condition | Limit |
|-----------|-------|
| n < m | 0 |
| n = m | $\frac{a_n}{b_m}$ (ratio of leading coefficients) |
| n > m | $\pm\infty$ (sign depends on leading terms) |

## Decision Tree

```
Evaluating lim f(x) as x → a
│
├── Try direct substitution
│   │
│   ├── Got a finite number → DONE!
│   │
│   ├── Got 0/0
│   │   ├── Factor and cancel
│   │   ├── Multiply by conjugate (if radicals)
│   │   ├── Use special limits (sin(x)/x, etc.)
│   │   └── L'Hôpital's Rule
│   │
│   ├── Got ∞/∞
│   │   ├── Divide by highest power of x
│   │   └── L'Hôpital's Rule
│   │
│   ├── Got k/0 (k ≠ 0)
│   │   └── Check left/right limits → ±∞
│   │
│   └── Got other indeterminate form
│       └── Transform to 0/0 or ∞/∞
│
└── One-sided limits (x → a⁺ or x → a⁻)
    └── Check behavior from each side
    └── Limit exists only if both sides equal
```

## Solving Templates

### Basic Limit Evaluation
1. **Try direct substitution**
2. **If indeterminate, identify the form**
3. **Apply appropriate technique:**
   - Factor and cancel
   - Rationalize (multiply by conjugate)
   - Use known special limits
   - L'Hôpital's Rule
4. **Verify the form before L'Hôpital**

### L'Hôpital's Rule Application
1. **Verify 0/0 or ∞/∞ form** (CRITICAL!)
2. **Differentiate numerator:** f'(x)
3. **Differentiate denominator:** g'(x)
4. **Evaluate the new limit**
5. **Repeat if still indeterminate**

*Example:* $\lim_{x \to 0} \frac{\sin(x)}{x}$
- Direct sub: 0/0 ✓
- L'Hôpital: $\lim_{x \to 0} \frac{\cos(x)}{1} = 1$

### Limits at Infinity
1. **Identify the dominant terms** (highest powers)
2. **Divide numerator and denominator by x^(highest power in denominator)**
3. **Evaluate:** terms with negative powers → 0

*Example:* $\lim_{x \to \infty} \frac{3x^2 + x}{2x^2 - 5}$
- Divide by x²: $\frac{3 + 1/x}{2 - 5/x^2}$
- As x → ∞: $\frac{3 + 0}{2 - 0} = \frac{3}{2}$

### Exponential Indeterminate Forms (0⁰, 1^∞, ∞⁰)
1. **Let y = f(x)^g(x)**
2. **Take natural log:** ln(y) = g(x) · ln(f(x))
3. **Evaluate lim ln(y)** (usually 0·∞ → rewrite as fraction)
4. **Answer:** $\lim y = e^{\lim \ln(y)}$

*Example:* $\lim_{x \to 0^+} x^x$ (form 0⁰)
- ln(y) = x·ln(x) = ln(x)/(1/x) → ∞/∞
- L'Hôpital: (1/x)/(-1/x²) = -x → 0
- Answer: e⁰ = **1**

### One-Sided Limits
1. **Evaluate from the right:** x → a⁺ (x slightly > a)
2. **Evaluate from the left:** x → a⁻ (x slightly < a)
3. **Two-sided limit exists only if both are equal**

## Common Mistakes
- **Using L'Hôpital when not 0/0 or ∞/∞:** Must verify the form first!
- **Using quotient rule:** L'Hôpital differentiates top and bottom separately
- **Forgetting to check conditions:** "Can I even use L'Hôpital here?"
- **Sign errors with one-sided limits:** Check if denominator is + or - on each side
- **Stopping too early:** Sometimes L'Hôpital needs multiple applications
- **Ignoring when it doesn't work:** If limit of f'/g' doesn't exist, original may still exist

## Practice Pattern
- "Find the limit as x approaches..."
- "Evaluate lim..."
- "Does the limit exist?"
- "Find the horizontal asymptote of..."
- "Use L'Hôpital's Rule to evaluate..."
- "Find one-sided limits at x = a"
