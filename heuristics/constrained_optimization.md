# Constrained Optimization

## Pattern Recognition
- Maximize/minimize objective function f(x,y)
- Subject to constraint g(x,y) = c
- Keywords: "subject to", "given that", "constraint"

## Decision Tree

```
Is constraint an EQUALITY (g = c)?
├── YES → Use Lagrange Multipliers
│         Set up: ∇f = λ∇g and g(x,y) = c
│
└── Is constraint an INEQUALITY (g ≤ c)?
    └── YES → Check TWO cases:
              1. Interior: solve ∇f = 0 (constraint inactive)
              2. Boundary: g = c (use Lagrange)
              Compare all critical points
```

## Solving Template (Lagrange Multipliers)

1. **Identify** objective f(x,y) and constraint g(x,y) = c
2. **Set up equations**:
   - ∂f/∂x = λ · ∂g/∂x
   - ∂f/∂y = λ · ∂g/∂y
   - g(x,y) = c
3. **Solve** the system of 3 equations for x, y, λ
4. **Evaluate** f at all critical points
5. **Compare** to find maximum/minimum

## Quick Check
- Number of equations = number of unknowns (x, y, λ)
- λ can be any real number (positive, negative, zero)

## Common Mistakes
- Forgetting the constraint equation g = c
- Sign errors in partial derivatives
- Not checking if solution satisfies constraint
- Confusing f and g

## Example Setup
Maximize f(x,y) = xy subject to x + 2y = 10

∂f/∂x = y = λ(1)
∂f/∂y = x = λ(2)
x + 2y = 10

From first two: y = λ and x = 2λ → x = 2y
Substitute: 2y + 2y = 10 → y = 2.5, x = 5
