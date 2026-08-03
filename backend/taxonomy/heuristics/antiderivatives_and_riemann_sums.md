# Integration

## Pattern Recognition
- Keywords: "integrate", "integral", "∫", "antiderivative", "area under"
- Finding F(x) such that F'(x) = f(x)
- Area, accumulation, total change problems

## Key Formulas (MUST MEMORIZE)

### Basic Antiderivatives
| Function | Integral |
|----------|----------|
| $x^n$ (n ≠ -1) | $\frac{x^{n+1}}{n+1} + C$ |
| $\frac{1}{x}$ | $\ln|x| + C$ |
| $e^x$ | $e^x + C$ |
| $a^x$ | $\frac{a^x}{\ln(a)} + C$ |

### Trigonometric Integrals
| Function | Integral |
|----------|----------|
| $\sin(x)$ | $-\cos(x) + C$ |
| $\cos(x)$ | $\sin(x) + C$ |
| $\sec^2(x)$ | $\tan(x) + C$ |
| $\csc^2(x)$ | $-\cot(x) + C$ |
| $\sec(x)\tan(x)$ | $\sec(x) + C$ |
| $\csc(x)\cot(x)$ | $-\csc(x) + C$ |

### Inverse Trig Forms
| Function | Integral |
|----------|----------|
| $\frac{1}{\sqrt{1-x^2}}$ | $\arcsin(x) + C$ |
| $\frac{1}{1+x^2}$ | $\arctan(x) + C$ |
| $\frac{1}{x\sqrt{x^2-1}}$ | $\text{arcsec}(x) + C$ |

### Integration by Parts Formula
$$\int u \, dv = uv - \int v \, du$$

**LIATE Rule** (priority for choosing u):
- **L**ogarithmic (ln x, log x)
- **I**nverse trig (arctan, arcsin)
- **A**lgebraic (x², x, polynomials)
- **T**rig (sin, cos, tan)
- **E**xponential (eˣ, aˣ)

## Decision Tree

```
Which technique to use?
│
├── Direct antiderivative?
│   └── Use table above
│
├── Composite function f(g(x)) · g'(x)?
│   └── U-SUBSTITUTION
│   └── Let u = g(x), du = g'(x)dx
│
├── Product of different types?
│   └── INTEGRATION BY PARTS
│   └── ∫udv = uv - ∫vdu
│   └── Use LIATE for choosing u
│
├── Rational function P(x)/Q(x)?
│   └── PARTIAL FRACTIONS
│   └── Factor denominator, decompose
│
├── √(a² - x²), √(a² + x²), √(x² - a²)?
│   └── TRIG SUBSTITUTION
│   └── See trig_substitution.md
│
├── Powers of sin and cos?
│   └── TRIG IDENTITIES
│   └── Use power reduction or Pythagorean
│
└── Nothing else works?
    └── Try completing the square
    └── Try algebraic manipulation first
```

## Solving Templates

### U-Substitution
1. **Identify inner function:** Look for g(x) whose derivative g'(x) also appears
2. **Set u = g(x):** Compute du = g'(x)dx
3. **Rewrite integral in u:** Replace all x terms
4. **Integrate in u**
5. **Substitute back:** Replace u with g(x)

*Example:* $\int 2x \cos(x^2) \, dx$
- Let u = x², du = 2x dx
- = $\int \cos(u) \, du = \sin(u) + C$
- = $\sin(x^2) + C$

### Integration by Parts
1. **Choose u and dv using LIATE**
2. **Compute du and v:** differentiate u, integrate dv
3. **Apply formula:** $\int u \, dv = uv - \int v \, du$
4. **Solve the remaining integral**
5. **May need to repeat or solve algebraically**

*Example:* $\int x e^x \, dx$
- u = x (A), dv = eˣdx (E)
- du = dx, v = eˣ
- = xeˣ - ∫eˣdx = **xeˣ - eˣ + C**

### Partial Fractions
1. **Factor the denominator completely**
2. **Set up partial fraction form:**
   - Linear factor (x-a): $\frac{A}{x-a}$
   - Repeated linear (x-a)²: $\frac{A}{x-a} + \frac{B}{(x-a)^2}$
   - Irreducible quadratic: $\frac{Ax+B}{x^2+bx+c}$
3. **Solve for constants** (multiply out, compare coefficients)
4. **Integrate each term**

### Definite Integrals
1. **Find antiderivative F(x)**
2. **Apply Fundamental Theorem:** $\int_a^b f(x)dx = F(b) - F(a)$
3. **Evaluate at bounds and subtract**

*Tip:* For u-sub with definite integrals, either:
- Change bounds when substituting, OR
- Substitute back to x before evaluating

## Common Mistakes
- **Forgetting +C** for indefinite integrals
- **Sign errors on trig integrals:** $\int \sin(x)dx = -\cos(x) + C$
- **Not substituting back** after u-substitution
- **Wrong u choice** in parts: remember LIATE
- **Forgetting absolute value:** $\int \frac{1}{x}dx = \ln|x| + C$
- **Power rule at n = -1:** $\int x^{-1}dx = \ln|x| + C$, not $\frac{x^0}{0}$
- **Definite integral bounds:** Don't forget to evaluate F(b) - F(a)

## Practice Pattern
- "Evaluate the integral..."
- "Find the antiderivative of..."
- "Compute ∫...dx"
- "Find the area under the curve..."
- "Use [specific technique] to integrate..."
