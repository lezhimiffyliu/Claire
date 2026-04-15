"""
UW Math 124 taxonomy for Claire

Purpose:
- Canonical topic and subtopic definitions for question tagging
- Topic names should match heuristic file names under taxonomy/heuristics/
- Subtopics are finer-grained concepts within each topic

Design rules:
- No aliases
- No vague labels
- No duplicate / overlapping labels when avoidable
- Keep topic names aligned with heuristic filenames
"""

TOPICS = [
    "limits",
    "continuity",
    "derivative_definition",
    "derivative_rules",
    "implicit_differentiation",
    "parametric_equations",
    "related_rates",
    "linear_approximation",
    "curve_analysis",
    "lhopitals_rule",
    "optimization",
]

SUBTOPICS = {
    "limits": [
        "limit_laws",
        "one_sided_limits",
        "infinite_limits",
        "limits_at_infinity",
        "squeeze_theorem",
        "trig_limits",
        "algebraic_limit_evaluation",
    ],

    "continuity": [
        "continuity_at_a_point",
        "piecewise_continuity",
        "removable_discontinuity",
        "jump_discontinuity",
        "infinite_discontinuity",
        "intermediate_value_theorem",
    ],

    "derivative_definition": [
        "limit_definition_of_derivative",
        "derivative_as_slope",
        "derivative_as_rate_of_change",
        "tangent_line_equation",
        "differentiability",
        "higher_order_derivatives",
    ],

    "derivative_rules": [
        "constant_rule",
        "power_rule",
        "sum_difference_rule",
        "product_rule",
        "quotient_rule",
        "chain_rule",
        "trig_derivatives",
        "exponential_derivatives",
        "logarithmic_derivatives",
        "logarithmic_differentiation",
    ],

    "implicit_differentiation": [
        "implicit_differentiation_basic",
        "implicit_tangent_line",
        "implicit_second_derivative",
        "horizontal_vertical_tangents",
    ],

    "parametric_equations": [
        "parametric_curve_graphing",
        "eliminating_parameter",
        "parametric_first_derivative",
        "parametric_second_derivative",
        "parametric_tangent_line",
        "parametric_motion",
    ],

    "related_rates": [
        "related_rates_setup",
        "time_differentiation",
        "geometric_related_rates",
        "trigonometric_related_rates",
        "rate_interpretation",
    ],

    "linear_approximation": [
        "linearization",
        "differentials",
        "error_estimation",
        "tangent_line_approximation",
    ],

    "curve_analysis": [
        "critical_points",
        "absolute_extrema",
        "local_extrema",
        "closed_interval_method",
        "mean_value_theorem",
        "increasing_decreasing_intervals",
        "first_derivative_test",
        "concavity",
        "inflection_points",
        "second_derivative_test",
        "asymptotes",
        "intercepts",
        "curve_sketching",
    ],

    "lhopitals_rule": [
        "indeterminate_zero_over_zero",
        "indeterminate_infinity_over_infinity",
        "indeterminate_other_forms",
        "lhopitals_rule_application",
    ],

    "optimization": [
        "optimization_setup",
        "objective_function",
        "constraint_equation",
        "geometric_optimization",
        "distance_optimization",
        "applied_optimization",
        "optimization_verification",
    ],
}