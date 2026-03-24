# Lagrange Multipliers

## Pattern Recognition
- Optimize f(x,y) or f(x,y,z)
- Subject to constraint g(x,y) = c
- Keywords: "subject to", "given that", "constraint"

## Solving Template
1. Identify objective function f and constraint g = c
2. Set up system: ∇f = λ∇g
   - fₓ = λgₓ
   - fᵧ = λgᵧ
   - (fᵤ = λgᵤ if 3D)
3. Include constraint equation: g = c
4. Solve the system for x, y (and λ)
5. Evaluate f at all critical points
6. Compare to find max/min

## Common Mistakes
- Forgetting the constraint equation
- Not checking ALL solutions
- Sign errors in gradients
