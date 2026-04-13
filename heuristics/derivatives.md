# Derivatives

## Pattern Recognition
- Keywords: "derivative", "differentiate", "d/dx", "f'(x)", "dy/dx"
- Rate of change, slope of tangent line, instantaneous velocity
- Implicit differentiation when y is defined implicitly

## Key Formulas (MUST MEMORIZE)

### Basic Derivative Rules
| Function | Derivative |
|----------|------------|
| $x^n$ | $n \cdot x^{n-1}$ |
| $e^x$ | $e^x$ |
| $a^x$ | $a^x \ln(a)$ |
| $\ln(x)$ | $\frac{1}{x}$ |
| $\log_a(x)$ | $\frac{1}{x \ln(a)}$ |

### Trigonometric Derivatives
| Function | Derivative |
|----------|------------|
| $\sin(x)$ | $\cos(x)$ |
| $\cos(x)$ | $-\sin(x)$ |
| $\tan(x)$ | $\sec^2(x)$ |
| $\sec(x)$ | $\sec(x)\tan(x)$ |
| $\csc(x)$ | $-\csc(x)\cot(x)$ |
| $\cot(x)$ | $-\csc^2(x)$ |

### Inverse Trig Derivatives
| Function | Derivative |
|----------|------------|
| $\arcsin(x)$ | $\frac{1}{\sqrt{1-x^2}}$ |
| $\arccos(x)$ | $\frac{-1}{\sqrt{1-x^2}}$ |
| $\arctan(x)$ | $\frac{1}{1+x^2}$ |

### Combination Rules
- **Sum/Difference:** $(f \pm g)' = f' \pm g'$
- **Constant Multiple:** $(cf)' = c \cdot f'$
- **Product Rule:** $(fg)' = f'g + fg'$
- **Quotient Rule:** $\left(\frac{f}{g}\right)' = \frac{f'g - fg'}{g^2}$
- **Chain Rule:** $\frac{d}{dx}[f(g(x))] = f'(g(x)) \cdot g'(x)$

## Decision Tree

```
What type of derivative?
│
├── Single function (power, trig, exp, log)
│   └── Use basic rules from table above
│
├── Product of functions (f · g)
│   └── Product Rule: (fg)' = f'g + fg'
│
├── Quotient of functions (f / g)
│   └── Quotient Rule: (f/g)' = (f'g - fg')/g²
│
├── Composition f(g(x))
│   └── Chain Rule: f'(g(x)) · g'(x)
│   └── Identify: outer f, inner g
│
├── Implicit equation F(x,y) = 0
│   └── Implicit differentiation
│   └── Treat y as y(x), use chain rule
│
└── Complex product/power (x^x, etc.)
    └── Logarithmic differentiation
    └── Take ln, then differentiate
```

## Solving Template

### Standard Derivative
1. Identify the function type(s) present
2. Determine which rule(s) apply (product, quotient, chain)
3. Apply rules from outside in
4. Simplify the result

### Chain Rule (Composite Functions)
1. **Identify outer and inner functions**
   - Write as f(g(x))
   - Outer: f(u), Inner: u = g(x)
2. **Differentiate outer, keep inner unchanged**
   - f'(g(x))
3. **Multiply by derivative of inner**
   - f'(g(x)) · g'(x)
4. **Simplify**

*Example:* $\frac{d}{dx}[\sin(x^2)]$
- Outer: sin(u), Inner: u = x²
- = cos(x²) · 2x = **2x cos(x²)**

### Implicit Differentiation
1. **Differentiate both sides with respect to x**
2. **Apply chain rule to y terms:** $\frac{d}{dx}[y^n] = ny^{n-1} \cdot \frac{dy}{dx}$
3. **Collect all dy/dx terms on one side**
4. **Factor out dy/dx and solve**

*Example:* $x^2 + y^2 = 25$
- $2x + 2y \cdot \frac{dy}{dx} = 0$
- $\frac{dy}{dx} = -\frac{x}{y}$

### Logarithmic Differentiation
1. Take natural log of both sides: $\ln(y) = \ln(f(x))$
2. Simplify using log rules
3. Differentiate both sides (implicit on left)
4. Solve for $\frac{dy}{dx} = y \cdot [\text{derivative of ln side}]$

## Common Mistakes
- **Chain rule forgotten:** $\frac{d}{dx}[\sin(3x)] \neq \cos(3x)$, it's $3\cos(3x)$
- **Sign error on cos:** $\frac{d}{dx}[\cos(x)] = -\sin(x)$, not $+\sin(x)$
- **Quotient rule order:** Numerator is $f'g - fg'$, not $fg' - f'g$
- **Power rule with negative exponents:** $\frac{d}{dx}[x^{-2}] = -2x^{-3}$, not $-2x^{-1}$
- **Implicit differentiation:** Forgetting to multiply by dy/dx when differentiating y terms
- **Constants disappear:** $\frac{d}{dx}[5] = 0$

## Practice Pattern
- "Find the derivative of..."
- "Differentiate the following..."
- "Find dy/dx if..."
- "Find the slope of the tangent line at..."
- "Find f'(x) when f(x) = ..."
