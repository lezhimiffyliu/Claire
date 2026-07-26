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

# =============================================================================
# SECTIONS - Maps textbook sections to topics/concepts
# Based on UW Math 124 Sample Syllabus
#
# Fields:
#   - id: textbook section number (e.g., "2.1")
#   - display_name: human-readable name
#   - week: week number in the quarter (1-10)
#   - order: order within the week (1, 2, 3)
#   - covered_in_exam: "exam_1", "exam_2", or "final"
#   - concepts: list of SUBTOPIC keys covered in this section
# =============================================================================

SECTIONS = [
    # Week 1: Introduction to Limits
    {
        "id": "2.1",
        "display_name": "Tangents and Velocity",
        "week": 1,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "derivative_as_slope",
            "derivative_as_rate_of_change",
        ],
    },
    {
        "id": "2.2",
        "display_name": "Limits",
        "week": 1,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "limit_laws",
            "one_sided_limits",
        ],
    },

    # Week 2: Calculating Limits and Continuity
    {
        "id": "2.3",
        "display_name": "Calculating Limits",
        "week": 2,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "algebraic_limit_evaluation",
            "trig_limits",
            "squeeze_theorem",
        ],
    },
    {
        "id": "2.5",
        "display_name": "Continuity",
        "week": 2,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "continuity_at_a_point",
            "piecewise_continuity",
            "removable_discontinuity",
            "jump_discontinuity",
            "infinite_discontinuity",
            "intermediate_value_theorem",
        ],
    },
    {
        "id": "2.6",
        "display_name": "Asymptotes",
        "week": 2,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "asymptotes",
            "infinite_limits",
            "limits_at_infinity",
        ],
    },

    # Week 3: Definition of Derivative
    {
        "id": "2.7",
        "display_name": "Derivatives",
        "week": 3,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "limit_definition_of_derivative",
            "differentiability",
        ],
    },
    {
        "id": "2.8",
        "display_name": "The Derivative as a Function",
        "week": 3,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "tangent_line_equation",
            "higher_order_derivatives",
        ],
    },

    # Week 4: Derivative Rules
    {
        "id": "3.1-3.2",
        "display_name": "Derivative Rules",
        "week": 4,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "constant_rule",
            "power_rule",
            "sum_difference_rule",
            "product_rule",
            "quotient_rule",
        ],
    },
    {
        "id": "3.3",
        "display_name": "Trig Derivatives",
        "week": 4,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "trig_derivatives",
        ],
    },
    {
        "id": "3.4",
        "display_name": "Chain Rule",
        "week": 4,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "chain_rule",
            "exponential_derivatives",
            "logarithmic_derivatives",
        ],
    },

    # Week 5: Implicit Differentiation
    {
        "id": "3.5",
        "display_name": "Implicit Differentiation",
        "week": 5,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "implicit_differentiation_basic",
            "implicit_tangent_line",
            "implicit_second_derivative",
            "horizontal_vertical_tangents",
        ],
    },

    # Week 6: Parametric and Logarithmic Differentiation
    {
        "id": "10.1",
        "display_name": "Parametric Equations",
        "week": 6,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "parametric_curve_graphing",
            "eliminating_parameter",
        ],
    },
    {
        "id": "10.2",
        "display_name": "Parametric Derivatives",
        "week": 6,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "parametric_first_derivative",
            "parametric_second_derivative",
            "parametric_tangent_line",
            "parametric_motion",
        ],
    },
    {
        "id": "3.6",
        "display_name": "Logarithmic Differentiation",
        "week": 6,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "logarithmic_differentiation",
        ],
    },

    # Week 7: Related Rates and Linear Approximation
    {
        "id": "3.9",
        "display_name": "Related Rates",
        "week": 7,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "related_rates_setup",
            "time_differentiation",
            "geometric_related_rates",
            "trigonometric_related_rates",
            "rate_interpretation",
        ],
    },
    {
        "id": "3.10",
        "display_name": "Linear Approximation",
        "week": 7,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "linearization",
            "differentials",
            "error_estimation",
            "tangent_line_approximation",
        ],
    },

    # Week 8: Extrema and Curve Analysis
    {
        "id": "4.1",
        "display_name": "Maximum and Minimum Values",
        "week": 8,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "critical_points",
            "absolute_extrema",
            "local_extrema",
            "closed_interval_method",
        ],
    },
    {
        "id": "4.3",
        "display_name": "Derivatives and Shape of Curves",
        "week": 8,
        "order": 2,
        "covered_in_exam": "final",
        "concepts": [
            "mean_value_theorem",
            "increasing_decreasing_intervals",
            "first_derivative_test",
            "concavity",
            "inflection_points",
            "second_derivative_test",
        ],
    },

    # Week 9: L'Hôpital and Curve Sketching
    {
        "id": "4.4",
        "display_name": "L'Hôpital's Rule",
        "week": 9,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "indeterminate_zero_over_zero",
            "indeterminate_infinity_over_infinity",
            "indeterminate_other_forms",
            "lhopitals_rule_application",
        ],
    },
    {
        "id": "4.5",
        "display_name": "Curve Sketching",
        "week": 9,
        "order": 2,
        "covered_in_exam": "final",
        "concepts": [
            "curve_sketching",
            "intercepts",
        ],
    },

    # Week 10: Optimization
    {
        "id": "4.7",
        "display_name": "Optimization",
        "week": 10,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "optimization_setup",
            "objective_function",
            "constraint_equation",
            "geometric_optimization",
            "distance_optimization",
            "applied_optimization",
            "optimization_verification",
        ],
    },
]

# Ordered by pedagogical dependency (prerequisites first), then frequency
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

# =============================================================================
# TOPIC METADATA
# - difficulty: 1-5 (cognitive load, not just math complexity)
# - frequency: "high" | "medium" | "low" (how often it appears on exams)
# - order: pedagogical order (prerequisites first, then high-frequency)
# - color_family: color hue for UI (0-360 degrees, or semantic name)
# =============================================================================

# Based on real UW exam distribution (136 problems analyzed):
# - curve_analysis: 22.8% (high)
# - derivative_rules: 13.2% (high)
# - related_rates: 13.2% (high)
# - optimization: 12.5% (high)
# - limits: 11.0% (medium)
# - parametric_equations: 10.3% (medium)
# - implicit_differentiation: 9.6% (medium)
# - linear_approximation: 5.1% (medium)
# - lhopitals_rule: 1.5% (low)
# - continuity: 0.7% (low)

TOPIC_METADATA = {
    "limits": {
        "difficulty": 2,
        "frequency": "medium",  # 11.0%
        "order": 1,
        "color_family": "blue",
        "display_name": "Limits",
    },
    "continuity": {
        "difficulty": 2,
        "frequency": "low",  # 0.7%
        "order": 2,
        "color_family": "blue",
        "display_name": "Continuity",
    },
    "derivative_definition": {
        "difficulty": 2,
        "frequency": "low",  # not in top topics
        "order": 3,
        "color_family": "teal",
        "display_name": "Derivative Definition",
    },
    "derivative_rules": {
        "difficulty": 2,
        "frequency": "high",  # 13.2%
        "order": 4,
        "color_family": "teal",
        "display_name": "Derivative Rules",
    },
    "implicit_differentiation": {
        "difficulty": 3,
        "frequency": "medium",  # 9.6%
        "order": 5,
        "color_family": "teal",
        "display_name": "Implicit Differentiation",
    },
    "parametric_equations": {
        "difficulty": 3,
        "frequency": "medium",  # 10.3%
        "order": 6,
        "color_family": "purple",
        "display_name": "Parametric Equations",
    },
    "related_rates": {
        "difficulty": 4,
        "frequency": "high",  # 13.2%
        "order": 7,
        "color_family": "orange",
        "display_name": "Related Rates",
    },
    "linear_approximation": {
        "difficulty": 3,
        "frequency": "medium",  # 5.1%
        "order": 8,
        "color_family": "green",
        "display_name": "Linear Approximation",
    },
    "curve_analysis": {
        "difficulty": 3,
        "frequency": "high",  # 22.8% - MOST COMMON
        "order": 9,
        "color_family": "rose",
        "display_name": "Curve Analysis",
    },
    "lhopitals_rule": {
        "difficulty": 3,
        "frequency": "low",  # 1.5%
        "order": 10,
        "color_family": "blue",
        "display_name": "L'Hôpital's Rule",
    },
    "optimization": {
        "difficulty": 4,
        "frequency": "high",  # 12.5%
        "order": 11,
        "color_family": "amber",
        "display_name": "Optimization",
    },
}

# =============================================================================
# SUBTOPIC METADATA
# - difficulty: 1-5 (relative to parent topic)
# - frequent: boolean (commonly tested within topic)
# - order: order within parent topic
# =============================================================================

# Based on real UW exam distribution (600 concept occurrences analyzed):
# Frequent (>=3%): critical_points (5.5%), concavity (4.5%), inflection_points (4.3%),
#   increasing_decreasing_intervals (4.0%), chain_rule (3.5%), local_extrema (3.2%),
#   related_rates_setup (3.0%), time_differentiation (3.0%)

SUBTOPIC_METADATA = {
    # LIMITS - topic is medium frequency (11%)
    "limit_laws": {"difficulty": 1, "frequent": False, "order": 1},
    "one_sided_limits": {"difficulty": 2, "frequent": False, "order": 2},
    "infinite_limits": {"difficulty": 2, "frequent": False, "order": 3},
    "limits_at_infinity": {"difficulty": 2, "frequent": False, "order": 4},
    "squeeze_theorem": {"difficulty": 3, "frequent": False, "order": 5},
    "trig_limits": {"difficulty": 3, "frequent": False, "order": 6},
    "algebraic_limit_evaluation": {"difficulty": 2, "frequent": True, "order": 7},  # 2.7%

    # CONTINUITY - topic is low frequency (0.7%)
    "continuity_at_a_point": {"difficulty": 1, "frequent": False, "order": 1},
    "piecewise_continuity": {"difficulty": 2, "frequent": False, "order": 2},
    "removable_discontinuity": {"difficulty": 2, "frequent": False, "order": 3},
    "jump_discontinuity": {"difficulty": 2, "frequent": False, "order": 4},
    "infinite_discontinuity": {"difficulty": 2, "frequent": False, "order": 5},
    "intermediate_value_theorem": {"difficulty": 3, "frequent": False, "order": 6},

    # DERIVATIVE DEFINITION - topic is low frequency
    "limit_definition_of_derivative": {"difficulty": 2, "frequent": False, "order": 1},
    "derivative_as_slope": {"difficulty": 1, "frequent": False, "order": 2},
    "derivative_as_rate_of_change": {"difficulty": 2, "frequent": False, "order": 3},
    "tangent_line_equation": {"difficulty": 2, "frequent": False, "order": 4},
    "differentiability": {"difficulty": 3, "frequent": False, "order": 5},
    "higher_order_derivatives": {"difficulty": 2, "frequent": False, "order": 6},

    # DERIVATIVE RULES - topic is high frequency (13.2%)
    "constant_rule": {"difficulty": 1, "frequent": False, "order": 1},
    "power_rule": {"difficulty": 1, "frequent": False, "order": 2},
    "sum_difference_rule": {"difficulty": 1, "frequent": False, "order": 3},
    "product_rule": {"difficulty": 2, "frequent": False, "order": 4},
    "quotient_rule": {"difficulty": 2, "frequent": False, "order": 5},  # 2.0%
    "chain_rule": {"difficulty": 3, "frequent": True, "order": 6},  # 3.5% - FREQUENT
    "trig_derivatives": {"difficulty": 2, "frequent": False, "order": 7},  # 2.7%
    "exponential_derivatives": {"difficulty": 2, "frequent": False, "order": 8},  # 2.7%
    "logarithmic_derivatives": {"difficulty": 2, "frequent": False, "order": 9},
    "logarithmic_differentiation": {"difficulty": 3, "frequent": False, "order": 10},

    # IMPLICIT DIFFERENTIATION - topic is medium frequency (9.6%)
    "implicit_differentiation_basic": {"difficulty": 2, "frequent": False, "order": 1},  # 2.2%
    "implicit_tangent_line": {"difficulty": 3, "frequent": False, "order": 2},
    "implicit_second_derivative": {"difficulty": 4, "frequent": False, "order": 3},
    "horizontal_vertical_tangents": {"difficulty": 3, "frequent": False, "order": 4},

    # PARAMETRIC EQUATIONS - topic is medium frequency (10.3%)
    "parametric_curve_graphing": {"difficulty": 2, "frequent": False, "order": 1},
    "eliminating_parameter": {"difficulty": 2, "frequent": False, "order": 2},
    "parametric_first_derivative": {"difficulty": 2, "frequent": False, "order": 3},  # 2.2%
    "parametric_second_derivative": {"difficulty": 3, "frequent": False, "order": 4},
    "parametric_tangent_line": {"difficulty": 3, "frequent": False, "order": 5},
    "parametric_motion": {"difficulty": 3, "frequent": False, "order": 6},

    # RELATED RATES - topic is high frequency (13.2%)
    "related_rates_setup": {"difficulty": 3, "frequent": True, "order": 1},  # 3.0% - FREQUENT
    "time_differentiation": {"difficulty": 3, "frequent": True, "order": 2},  # 3.0% - FREQUENT
    "geometric_related_rates": {"difficulty": 4, "frequent": False, "order": 3},  # 2.3%
    "trigonometric_related_rates": {"difficulty": 4, "frequent": False, "order": 4},
    "rate_interpretation": {"difficulty": 3, "frequent": False, "order": 5},  # 2.3%

    # LINEAR APPROXIMATION - topic is medium frequency (5.1%)
    "linearization": {"difficulty": 2, "frequent": False, "order": 1},
    "differentials": {"difficulty": 3, "frequent": False, "order": 2},
    "error_estimation": {"difficulty": 3, "frequent": False, "order": 3},
    "tangent_line_approximation": {"difficulty": 2, "frequent": False, "order": 4},

    # CURVE ANALYSIS - topic is high frequency (22.8%) - MOST COMMON TOPIC
    "critical_points": {"difficulty": 2, "frequent": True, "order": 1},  # 5.5% - MOST FREQUENT
    "absolute_extrema": {"difficulty": 2, "frequent": False, "order": 2},
    "local_extrema": {"difficulty": 2, "frequent": True, "order": 3},  # 3.2% - FREQUENT
    "closed_interval_method": {"difficulty": 2, "frequent": False, "order": 4},
    "mean_value_theorem": {"difficulty": 3, "frequent": False, "order": 5},
    "increasing_decreasing_intervals": {"difficulty": 2, "frequent": True, "order": 6},  # 4.0% - FREQUENT
    "first_derivative_test": {"difficulty": 3, "frequent": False, "order": 7},
    "concavity": {"difficulty": 2, "frequent": True, "order": 8},  # 4.5% - FREQUENT
    "inflection_points": {"difficulty": 3, "frequent": True, "order": 9},  # 4.3% - FREQUENT
    "second_derivative_test": {"difficulty": 3, "frequent": False, "order": 10},
    "asymptotes": {"difficulty": 2, "frequent": False, "order": 11},  # 2.8%
    "intercepts": {"difficulty": 1, "frequent": False, "order": 12},
    "curve_sketching": {"difficulty": 4, "frequent": False, "order": 13},  # 2.8%

    # L'HOPITAL'S RULE - topic is low frequency (1.5%)
    "indeterminate_zero_over_zero": {"difficulty": 2, "frequent": False, "order": 1},
    "indeterminate_infinity_over_infinity": {"difficulty": 2, "frequent": False, "order": 2},
    "indeterminate_other_forms": {"difficulty": 3, "frequent": False, "order": 3},
    "lhopitals_rule_application": {"difficulty": 3, "frequent": False, "order": 4},

    # OPTIMIZATION - topic is high frequency (12.5%)
    "optimization_setup": {"difficulty": 3, "frequent": False, "order": 1},  # 2.7%
    "objective_function": {"difficulty": 3, "frequent": False, "order": 2},
    "constraint_equation": {"difficulty": 3, "frequent": False, "order": 3},
    "geometric_optimization": {"difficulty": 4, "frequent": False, "order": 4},  # 2.3%
    "distance_optimization": {"difficulty": 4, "frequent": False, "order": 5},
    "applied_optimization": {"difficulty": 4, "frequent": False, "order": 6},
    "optimization_verification": {"difficulty": 3, "frequent": False, "order": 7},
}