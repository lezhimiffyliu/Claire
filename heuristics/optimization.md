# Optimization (Unconstrained)

## Pattern Recognition
- Keywords: "maximize", "minimize", "largest", "smallest", "optimal"
- Single objective function f(x) or f(x,y)
- No constraint equation
- Also: "classify the critical point", "what type of point"

## Key Formulas (MUST MEMORIZE)

### Single Variable Second Derivative Test
Given critical point where f'(c) = 0:
- f''(c) > 0 → **local minimum** (concave up)
- f''(c) < 0 → **local maximum** (concave down)
- f''(c) = 0 → test inconclusive, use first derivative test

### Two Variable Second Derivative Test (Discriminant/Hessian)
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

*Memory trick: D < 0 means the eigenvalues have opposite signs → saddle*

## Solving Template

### Single Variable f(x)
1. Find f'(x)
2. Set f'(x) = 0, solve for critical points
3. Apply second derivative test (see above)
4. Check endpoints if domain is restricted
5. Compare all values to find global max/min

### Two Variables f(x,y)
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

## Common Mistakes
- Forgetting the square on f_xy in the discriminant
- Confusing D > 0 cases (check f_xx, not f_yy!)
- Forgetting D = 0 is inconclusive
- Not checking endpoints on closed intervals

## Practice Pattern
- "Find the dimensions of [shape] that maximize/minimize [quantity]"
- "Classify the critical point at (a,b)"
- "Given second derivatives, determine if max/min/saddle"
