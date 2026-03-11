# Optimization (Unconstrained)

## Pattern Recognition
- Keywords: "maximize", "minimize", "largest", "smallest", "optimal"
- Single objective function f(x) or f(x,y)
- No constraint equation

## Solving Template

### Single Variable f(x)
1. Find f'(x)
2. Set f'(x) = 0, solve for critical points
3. Use second derivative test:
   - f''(x) > 0 → local minimum
   - f''(x) < 0 → local maximum
4. Check endpoints if domain is restricted
5. Compare all values to find global max/min

### Two Variables f(x,y)
1. Find ∇f = (∂f/∂x, ∂f/∂y)
2. Set ∇f = 0, solve system for critical points
3. Use second derivative test (Hessian):
   - D = f_xx * f_yy - (f_xy)²
   - D > 0 and f_xx > 0 → local minimum
   - D > 0 and f_xx < 0 → local maximum
   - D < 0 → saddle point
4. Check boundary if domain is restricted

## Common Mistakes
- Forgetting to check endpoints on closed intervals
- Not verifying if critical point is max or min
- Arithmetic errors when solving f'(x) = 0

## Practice Pattern
"Find the dimensions of [shape] that maximize/minimize [quantity]"
