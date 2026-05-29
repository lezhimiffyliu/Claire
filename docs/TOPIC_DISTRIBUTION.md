# Topic Distribution Analysis

Generated from `/problems/*.json` — used to prioritize learning path recommendations.

**Formula:** `topic_weight = points_total + problem_count × 0.5`

---

## Math 124 (Differential Calculus)

| Rank | Topic | Problems | Points | Weight |
|------|-------|----------|--------|--------|
| 1 | curve_analysis | 31 | 433 | 448.5 |
| 2 | derivative_rules | 18 | 237 | 246.0 |
| 3 | related_rates | 18 | 213 | 222.0 |
| 4 | optimization | 17 | 204 | 212.5 |
| 5 | limits | 15 | 186 | 193.5 |
| 6 | parametric_equations | 14 | 163 | 170.0 |
| 7 | implicit_differentiation | 13 | 152 | 158.5 |
| 8 | linear_approximation | 7 | 78 | 81.5 |
| 9 | lhopitals_rule | 2 | 27 | 28.0 |
| 10 | continuity | 1 | 12 | 12.5 |

**Key insight:** `curve_analysis` dominates Math 124 finals — accounts for ~30% of all points.

---

## Math 125 (Integral Calculus)

| Rank | Topic | Problems | Points | Weight |
|------|-------|----------|--------|--------|
| 1 | differential_equations | 64 | 651 | 683.0 |
| 2 | applications_of_integration | 58 | 598 | 627.0 |
| 3 | substitution | 33 | 358 | 374.5 |
| 4 | volumes | 32 | 307 | 323.0 |
| 5 | fundamental_theorem_of_calculus | 26 | 270 | 283.0 |
| 6 | work | 22 | 220 | 231.0 |
| 7 | improper_integrals | 17 | 170 | 178.5 |
| 8 | arc_length | 16 | 160 | 168.0 |
| 9 | area_between_curves | 12 | 122 | 128.0 |
| 10 | integration_by_parts | 9 | 94 | 98.5 |
| 11 | trigonometric_integrals | 5 | 52 | 54.5 |
| 12 | trigonometric_substitution | 3 | 24 | 25.5 |
| 13 | partial_fractions | 2 | 22 | 23.0 |

**Key insight:** `differential_equations` + `applications_of_integration` together are ~40% of exam weight.

---

## Math 126 (Multivariable Calculus & Series)

| Rank | Topic | Problems | Points | Weight |
|------|-------|----------|--------|--------|
| 1 | taylor_polynomials_and_series | 79 | 996 | 1035.5 |
| 2 | double_integrals | 41 | 492 | 512.5 |
| 3 | multivariable_optimization | 41 | 487 | 507.5 |
| 4 | lines_and_planes | 35 | 386 | 403.5 |
| 5 | motion_in_space | 27 | 307 | 320.5 |
| 6 | vector_valued_functions | 21 | 249 | 259.5 |
| 7 | applications_of_double_integrals | 19 | 215 | 224.5 |
| 8 | tangent_planes_and_differentials | 19 | 207 | 216.5 |
| 9 | vectors_and_geometry | 18 | 192 | 201.0 |
| 10 | polar_coordinates | 10 | 118 | 123.0 |
| 11 | partial_derivatives | 10 | 117 | 122.0 |
| 12 | quadric_surfaces | 8 | 77 | 81.0 |
| 13 | multivariable_functions | 5 | 56 | 58.5 |

**Key insight:** `taylor_polynomials_and_series` is the single most tested topic — 2× the weight of second place.

---

## Recommendation Logic

1. **Initial path:** Sort by `weight` descending, recommend top 5 topics
2. **After diagnostic:** Insert student's weak topics at position 1, then fill with high-weight topics
3. **After practice:** Track accuracy per topic, boost weak topics in recommendations
