# Derivatives

## Pattern Recognition
- Find derivative, differentiate, d/dx, f'(x)
- Rate of change, slope of tangent line
- Velocity, acceleration (physics context)

## Decision Tree

```
What type of function?
│
├── Polynomial (x^n)
│   └── Power rule: d/dx[x^n] = n·x^(n-1)
│
├── Product (f·g)
│   └── Product rule: (fg)' = f'g + fg'
│
├── Quotient (f/g)
│   └── Quotient rule: (f/g)' = (f'g - fg')/g²
│
├── Composition f(g(x))
│   └── Chain rule: d/dx[f(g(x))] = f'(g(x))·g'(x)
│
├── Implicit (F(x,y) = 0)
│   └── Implicit differentiation:
│       Differentiate both sides, solve for dy/dx
│
└── Logarithmic (complex products/powers)
    └── Take ln of both sides first, then differentiate
```

## Chain Rule Template
For f(g(x)):
1. Identify outer function f and inner function g
2. Derivative = f'(outer) · g'(inner)
3. Substitute back

Example: d/dx[sin(x²)]
- Outer: sin(u), inner: u = x²
- = cos(x²) · 2x = 2x·cos(x²)

## Implicit Differentiation Template
1. Differentiate both sides with respect to x
2. Apply chain rule: d/dx[y²] = 2y · dy/dx
3. Collect terms with dy/dx on one side
4. Factor out dy/dx and solve

## Common Derivatives
| f(x) | f'(x) |
|------|-------|
| x^n | n·x^(n-1) |
| e^x | e^x |
| ln(x) | 1/x |
| sin(x) | cos(x) |
| cos(x) | -sin(x) |
| tan(x) | sec²(x) |

## Common Mistakes
- Forgetting chain rule on inner function
- Sign error on cos(x) derivative
- Power rule errors with negative/fractional exponents
