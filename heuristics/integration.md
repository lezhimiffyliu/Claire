# Integration

## Pattern Recognition
- Find integral, antiderivative, ∫
- Area under curve, accumulation
- Given derivative, find original function

## Decision Tree

```
What technique to use?
│
├── Direct (basic antiderivative)
│   └── Use integration table
│
├── Substitution (u-sub)
│   └── When: composite function f(g(x))·g'(x)
│   └── Let u = g(x), du = g'(x)dx
│
├── Integration by Parts
│   └── When: product of different types (x·e^x, x·sin(x))
│   └── ∫u dv = uv - ∫v du
│   └── LIATE rule for choosing u
│
├── Partial Fractions
│   └── When: rational function P(x)/Q(x)
│   └── Factor denominator, decompose
│
├── Trigonometric Substitution
│   └── When: √(a²-x²), √(a²+x²), √(x²-a²)
│   └── Use appropriate trig identity
│
└── Trigonometric Integrals
    └── When: sin^n(x)·cos^m(x)
    └── Use power-reduction or substitution
```

## U-Substitution Template
1. Identify inner function u = g(x)
2. Compute du = g'(x)dx
3. Rewrite integral in terms of u
4. Integrate
5. Substitute back x

## Integration by Parts Template
∫u dv = uv - ∫v du

LIATE priority for choosing u:
- **L**ogarithmic (ln x)
- **I**nverse trig (arctan x)
- **A**lgebraic (x², x)
- **T**rigonometric (sin x, cos x)
- **E**xponential (e^x)

## Common Integrals
| f(x) | ∫f(x)dx |
|------|---------|
| x^n | x^(n+1)/(n+1) + C |
| 1/x | ln\|x\| + C |
| e^x | e^x + C |
| sin(x) | -cos(x) + C |
| cos(x) | sin(x) + C |
| 1/(1+x²) | arctan(x) + C |

## Common Mistakes
- Forgetting +C for indefinite integrals
- Wrong sign on trig integrals
- Not substituting back after u-sub
- Choosing wrong u in integration by parts
