# Limits

## Pattern Recognition
- Find lim as x → a
- Evaluate limit, limiting behavior
- Continuity, asymptotes

## Decision Tree

```
Try direct substitution first
│
├── Got a number → Done!
│
├── Got 0/0 (indeterminate)
│   ├── Factor and cancel
│   ├── Multiply by conjugate (if √ present)
│   ├── Use L'Hôpital's Rule
│   └── Use special limits (sin(x)/x, etc.)
│
├── Got ∞/∞ (indeterminate)
│   ├── Divide by highest power
│   └── Use L'Hôpital's Rule
│
├── Got k/0 (k ≠ 0)
│   └── Limit is ±∞ (check sign from left/right)
│
└── Got other indeterminate (0·∞, ∞-∞, 0^0, 1^∞, ∞^0)
    └── Rewrite to 0/0 or ∞/∞, then L'Hôpital
```

## L'Hôpital's Rule Template
If lim f(x)/g(x) = 0/0 or ∞/∞:

lim [f(x)/g(x)] = lim [f'(x)/g'(x)]

**Conditions:**
- Must be 0/0 or ∞/∞ form
- Derivative of top and bottom separately (NOT quotient rule)
- May need to apply multiple times

## Special Limits
| Limit | Value |
|-------|-------|
| lim(x→0) sin(x)/x | 1 |
| lim(x→0) (1-cos(x))/x | 0 |
| lim(x→0) (e^x - 1)/x | 1 |
| lim(x→∞) (1 + 1/x)^x | e |
| lim(x→0) (1 + x)^(1/x) | e |

## Limits at Infinity Template
For rational functions P(x)/Q(x) as x → ∞:
- deg(P) < deg(Q) → limit = 0
- deg(P) = deg(Q) → limit = ratio of leading coefficients
- deg(P) > deg(Q) → limit = ±∞

## One-Sided Limits
- lim(x→a⁺) means approach from right (x > a)
- lim(x→a⁻) means approach from left (x < a)
- Two-sided limit exists only if both one-sided limits exist and are equal

## Common Mistakes
- Using L'Hôpital when not 0/0 or ∞/∞
- Using quotient rule instead of separate derivatives
- Forgetting to check if conditions are met
- Sign errors with one-sided limits
