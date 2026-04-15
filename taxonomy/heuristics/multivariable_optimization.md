# Multivariable Optimization

## Pattern Recognition
- Keywords: "maximize", "minimize", "largest", "smallest", "optimal"
- Function of two or more variables: f(x,y) or f(x,y,z)
- May include constraint: "subject to", "given that"
- Also: "classify the critical point", "what type of point"

---

## Part 1: Unconstrained Optimization

### Key Formula: Second Derivative Test (Discriminant/Hessian)
Given critical point where ∇f = 0:

**Step 1: Compute the discriminant**
$$D = f_{xx} \cdot f_{yy} - (f_{xy})^2$$

**Step 2: Classify using D**
| D | f_xx | Conclusion |
|---|------|------------|
| D > 0 | f_xx > 0 | **Local minimum** |
| D > 0 | f_xx < 0 | **Local maximum** |
| D < 0 | (any) | **Saddle point** |
| D = 0 | (any) | **Inconclusive** |

*Memory trick: D < 0 means eigenvalues have opposite signs → saddle*

### Solving Template (Unconstrained)
1. Find ∇f = (∂f/∂x, ∂f/∂y)
2. Set ∇f = 0, solve system for critical points
3. Compute f_xx, f_yy, f_xy at each critical point
4. Apply discriminant test (see above)
5. Check boundary if domain is restricted

### Classification Problems (given second derivatives)
When problem gives you f_xx, f_yy, f_xy values directly:
1. Compute D = f_xx · f_yy - (f_xy)²
2. Check sign of D
3. If D > 0, check sign of f_xx
4. Apply the table above

---

## Part 2: Constrained Optimization (Lagrange Multipliers)

### Decision Tree
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

### Key Formula: Lagrange Multipliers
$$\nabla f = \lambda \nabla g$$

This gives the system:
- ∂f/∂x = λ · ∂g/∂x
- ∂f/∂y = λ · ∂g/∂y
- g(x,y) = c (constraint equation)

### Solving Template (Lagrange)
1. **Identify** objective f(x,y) and constraint g(x,y) = c
2. **Set up equations**:
   - fₓ = λgₓ
   - fᵧ = λgᵧ
   - g(x,y) = c
3. **Solve** the system of 3 equations for x, y, λ
4. **Evaluate** f at all critical points
5. **Compare** to find maximum/minimum

### Quick Check
- Number of equations = number of unknowns (x, y, λ)
- λ can be any real number (positive, negative, zero)

### Example Setup
Maximize f(x,y) = xy subject to x + 2y = 10

fₓ = y = λ(1)
fᵧ = x = λ(2)
x + 2y = 10

From first two: y = λ and x = 2λ → x = 2y
Substitute: 2y + 2y = 10 → y = 2.5, x = 5

---

## Common Mistakes
- Forgetting the square on f_xy in the discriminant
- Confusing D > 0 cases (check f_xx, not f_yy!)
- D = 0 is inconclusive, not a saddle point
- Not checking endpoints on closed intervals
- Forgetting the constraint equation g = c
- Not checking if solution satisfies constraint
- Confusing f and g in Lagrange setup
