"""
UW Math 125 taxonomy for Claire

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
# Based on UW Math 125 Sample Syllabus (Spring Quarter)
#
# Fields:
#   - id: textbook section number (e.g., "5.1")
#   - display_name: human-readable name
#   - week: week number in the quarter (1-10)
#   - order: order within the week (1, 2, 3)
#   - covered_in_exam: "exam_1", "exam_2", or "final"
#   - concepts: list of SUBTOPIC keys covered in this section
# =============================================================================

SECTIONS = [
    # Week 1: Antiderivatives and Definite Integrals
    {
        "id": "4.9",
        "display_name": "Antiderivatives",
        "week": 1,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "basic_antiderivatives",
            "initial_value_problems",
        ],
    },
    {
        "id": "5.1",
        "display_name": "Areas and Riemann Sums",
        "week": 1,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "sigma_notation",
            "left_riemann_sums",
            "right_riemann_sums",
            "midpoint_riemann_sums",
            "riemann_sum_limit_definition",
        ],
    },
    {
        "id": "5.2",
        "display_name": "Definite Integrals",
        "week": 1,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "definite_integral_as_area",
            "net_change_from_integral",
        ],
    },

    # Week 2: Fundamental Theorem and Substitution
    {
        "id": "5.3",
        "display_name": "Fundamental Theorem of Calculus",
        "week": 2,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "accumulation_functions",
            "derivative_of_integral_function",
            "evaluation_by_antiderivatives",
        ],
    },
    {
        "id": "5.4",
        "display_name": "Indefinite Integrals and Net Change",
        "week": 2,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "total_change_theorem",
            "indefinite_integrals",
        ],
    },
    {
        "id": "5.5",
        "display_name": "Substitution",
        "week": 2,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "u_substitution_basic",
            "u_substitution_with_bounds",
            "reverse_chain_rule_recognition",
            "algebraic_substitution_setup",
            "definite_integral_substitution",
        ],
    },

    # Week 3: Areas and Volumes
    {
        "id": "6.1",
        "display_name": "Areas Between Curves",
        "week": 3,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "area_between_two_curves_dx",
            "area_between_two_curves_dy",
            "finding_intersection_points_for_area",
            "top_minus_bottom_setup",
            "right_minus_left_setup",
        ],
    },
    {
        "id": "6.2",
        "display_name": "Volumes by Slicing",
        "week": 3,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "cross_sections",
        ],
    },
    {
        "id": "6.3",
        "display_name": "Disks and Washers",
        "week": 3,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "disk_method",
            "washer_method",
            "volume_with_respect_to_x",
            "volume_with_respect_to_y",
            "radius_from_geometry",
            "inner_outer_radius_setup",
        ],
    },

    # Week 4: More Volumes and Work (Midterm 1)
    {
        "id": "6.4",
        "display_name": "Work",
        "week": 4,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "constant_force_work",
            "variable_force_work",
            "spring_work",
            "pumping_liquid_work",
            "distance_and_force_setup",
            "work_integral_interpretation",
        ],
    },

    # Week 5: Average Value and Integration by Parts
    {
        "id": "6.5",
        "display_name": "Average Value of a Function",
        "week": 5,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "average_value_of_a_function",
        ],
    },
    {
        "id": "7.1",
        "display_name": "Integration by Parts",
        "week": 5,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "integration_by_parts_basic",
            "choosing_u_and_dv",
            "repeated_integration_by_parts",
            "tabular_integration_by_parts",
            "integrals_involving_logs",
            "integrals_involving_inverse_trig",
        ],
    },
    {
        "id": "7.2",
        "display_name": "Trigonometric Integrals",
        "week": 5,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "powers_of_sine_and_cosine",
            "powers_of_tangent_and_secant",
            "trig_identity_rewriting",
            "odd_even_power_strategy",
            "product_of_trig_functions",
        ],
    },

    # Week 6: More Integration Techniques
    {
        "id": "7.3",
        "display_name": "Trigonometric Substitution",
        "week": 6,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "sqrt_a2_minus_x2_substitution",
            "sqrt_a2_plus_x2_substitution",
            "sqrt_x2_minus_a2_substitution",
            "triangle_back_substitution",
            "trigonometric_substitution_setup",
        ],
    },
    {
        "id": "7.4",
        "display_name": "Partial Fractions",
        "week": 6,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "linear_factor_decomposition",
            "repeated_linear_factor_decomposition",
            "irreducible_quadratic_decomposition",
            "solving_for_coefficients",
            "integrating_rational_functions",
        ],
    },
    {
        "id": "7.5",
        "display_name": "Strategies of Integration",
        "week": 6,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [],
    },

    # Week 7: Numerical Methods and Improper Integrals
    {
        "id": "7.7",
        "display_name": "Approximations of Integrals",
        "week": 7,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "numerical_integration_midpoint_rule",
            "numerical_integration_trapezoidal_rule",
            "numerical_integration_simpsons_rule",
            "error_estimation_for_numerical_integration",
        ],
    },
    {
        "id": "7.8",
        "display_name": "Improper Integrals",
        "week": 7,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "infinite_interval_integrals",
            "vertical_asymptote_integrals",
            "splitting_at_discontinuities",
            "convergence_of_improper_integrals",
            "divergence_of_improper_integrals",
        ],
    },
    {
        "id": "8.1",
        "display_name": "Arc Length",
        "week": 7,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "arc_length_of_y_fx",
            "arc_length_of_x_gy",
            "arc_length_integrand_setup",
        ],
    },

    # Week 8: Center of Mass and Intro to DEs (Midterm 2)
    {
        "id": "8.3",
        "display_name": "Center of Mass",
        "week": 8,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "mass_from_density",
            "center_of_mass_one_dimensional",
            "center_of_mass_two_dimensional",
            "moments",
        ],
    },
    {
        "id": "9.1",
        "display_name": "Introduction to Differential Equations",
        "week": 8,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "differential_equation_terminology",
            "solution_verification",
        ],
    },

    # Week 9: Separable DEs and Applications
    {
        "id": "9.3",
        "display_name": "Separable Differential Equations",
        "week": 9,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "separable_differential_equations",
            "initial_value_problems_for_separable_equations",
        ],
    },
    {
        "id": "9.4",
        "display_name": "Applications of Differential Equations",
        "week": 9,
        "order": 2,
        "covered_in_exam": "final",
        "concepts": [
            "exponential_growth_and_decay",
            "logistic_differential_equation",
            "mixing_or_application_modeling",
        ],
    },
]

# Ordered by pedagogical dependency (prerequisites first), then frequency
TOPICS = [
    "antiderivatives_and_riemann_sums",
    "fundamental_theorem_of_calculus",
    "substitution",
    "area_between_curves",
    "volumes",
    "work",
    "integration_by_parts",
    "trigonometric_integrals",
    "trigonometric_substitution",
    "partial_fractions",
    "improper_integrals",
    "applications_of_integration",
    "arc_length",
    "differential_equations",
]

SUBTOPICS = {
    "antiderivatives_and_riemann_sums": [
        "basic_antiderivatives",
        "initial_value_problems",
        "sigma_notation",
        "left_riemann_sums",
        "right_riemann_sums",
        "midpoint_riemann_sums",
        "riemann_sum_limit_definition",
        "definite_integral_as_area",
        "net_change_from_integral",
    ],

    "fundamental_theorem_of_calculus": [
        "accumulation_functions",
        "derivative_of_integral_function",
        "evaluation_by_antiderivatives",
        "total_change_theorem",
        "indefinite_integrals",
    ],

    "substitution": [
        "u_substitution_basic",
        "u_substitution_with_bounds",
        "reverse_chain_rule_recognition",
        "algebraic_substitution_setup",
        "definite_integral_substitution",
    ],

    "area_between_curves": [
        "area_between_two_curves_dx",
        "area_between_two_curves_dy",
        "finding_intersection_points_for_area",
        "top_minus_bottom_setup",
        "right_minus_left_setup",
    ],

    "volumes": [
        "cross_sections",
        "disk_method",
        "washer_method",
        "volume_with_respect_to_x",
        "volume_with_respect_to_y",
        "radius_from_geometry",
        "inner_outer_radius_setup",
    ],

    "work": [
        "constant_force_work",
        "variable_force_work",
        "spring_work",
        "pumping_liquid_work",
        "distance_and_force_setup",
        "work_integral_interpretation",
    ],

    "integration_by_parts": [
        "integration_by_parts_basic",
        "choosing_u_and_dv",
        "repeated_integration_by_parts",
        "tabular_integration_by_parts",
        "integrals_involving_logs",
        "integrals_involving_inverse_trig",
    ],

    "trigonometric_integrals": [
        "powers_of_sine_and_cosine",
        "powers_of_tangent_and_secant",
        "trig_identity_rewriting",
        "odd_even_power_strategy",
        "product_of_trig_functions",
    ],

    "trigonometric_substitution": [
        "sqrt_a2_minus_x2_substitution",
        "sqrt_a2_plus_x2_substitution",
        "sqrt_x2_minus_a2_substitution",
        "triangle_back_substitution",
        "trigonometric_substitution_setup",
    ],

    "partial_fractions": [
        "linear_factor_decomposition",
        "repeated_linear_factor_decomposition",
        "irreducible_quadratic_decomposition",
        "solving_for_coefficients",
        "integrating_rational_functions",
    ],

    "improper_integrals": [
        "infinite_interval_integrals",
        "vertical_asymptote_integrals",
        "splitting_at_discontinuities",
        "convergence_of_improper_integrals",
        "divergence_of_improper_integrals",
    ],

    "applications_of_integration": [
        "average_value_of_a_function",
        "numerical_integration_midpoint_rule",
        "numerical_integration_trapezoidal_rule",
        "numerical_integration_simpsons_rule",
        "error_estimation_for_numerical_integration",
        "mass_from_density",
        "center_of_mass_one_dimensional",
        "center_of_mass_two_dimensional",
        "moments",
    ],

    "arc_length": [
        "arc_length_of_y_fx",
        "arc_length_of_x_gy",
        "arc_length_integrand_setup",
    ],

    "differential_equations": [
        "differential_equation_terminology",
        "separable_differential_equations",
        "initial_value_problems_for_separable_equations",
        "exponential_growth_and_decay",
        "logistic_differential_equation",
        "mixing_or_application_modeling",
        "solution_verification",
    ],
}

# =============================================================================
# TOPIC METADATA
# - difficulty: 1-5 (cognitive load, not just math complexity)
# - frequency: "high" | "medium" | "low" (how often it appears on exams)
# - order: pedagogical order (prerequisites first, then high-frequency)
# - color_family: color hue for UI (semantic name)
# =============================================================================

# Based on real UW exam distribution (299 problems analyzed):
# - differential_equations: 21.4% (high)
# - applications_of_integration: 19.4% (high)
# - substitution: 11.0% (medium)
# - volumes: 10.7% (medium)
# - fundamental_theorem_of_calculus: 8.7% (medium)
# - work: 7.4% (medium)
# - improper_integrals: 5.7% (medium)
# - arc_length: 5.4% (medium)
# - area_between_curves: 4.0% (low)
# - integration_by_parts: 3.0% (low)
# - trigonometric_integrals: 1.7% (low)
# - trigonometric_substitution: 1.0% (low)
# - partial_fractions: 0.7% (low)

TOPIC_METADATA = {
    "antiderivatives_and_riemann_sums": {
        "difficulty": 2,
        "frequency": "low",  # not in top topics
        "order": 1,
        "color_family": "blue",
        "display_name": "Antiderivatives & Riemann Sums",
    },
    "fundamental_theorem_of_calculus": {
        "difficulty": 2,
        "frequency": "medium",  # 8.7%
        "order": 2,
        "color_family": "blue",
        "display_name": "Fundamental Theorem",
    },
    "substitution": {
        "difficulty": 2,
        "frequency": "medium",  # 11.0%
        "order": 3,
        "color_family": "teal",
        "display_name": "U-Substitution",
    },
    "area_between_curves": {
        "difficulty": 2,
        "frequency": "low",  # 4.0%
        "order": 4,
        "color_family": "green",
        "display_name": "Area Between Curves",
    },
    "volumes": {
        "difficulty": 3,
        "frequency": "medium",  # 10.7%
        "order": 5,
        "color_family": "green",
        "display_name": "Volumes of Revolution",
    },
    "work": {
        "difficulty": 3,
        "frequency": "medium",  # 7.4%
        "order": 6,
        "color_family": "orange",
        "display_name": "Work",
    },
    "integration_by_parts": {
        "difficulty": 3,
        "frequency": "low",  # 3.0%
        "order": 7,
        "color_family": "purple",
        "display_name": "Integration by Parts",
    },
    "trigonometric_integrals": {
        "difficulty": 3,
        "frequency": "low",  # 1.7%
        "order": 8,
        "color_family": "purple",
        "display_name": "Trig Integrals",
    },
    "trigonometric_substitution": {
        "difficulty": 4,
        "frequency": "low",  # 1.0%
        "order": 9,
        "color_family": "purple",
        "display_name": "Trig Substitution",
    },
    "partial_fractions": {
        "difficulty": 3,
        "frequency": "low",  # 0.7%
        "order": 10,
        "color_family": "purple",
        "display_name": "Partial Fractions",
    },
    "improper_integrals": {
        "difficulty": 3,
        "frequency": "medium",  # 5.7%
        "order": 11,
        "color_family": "rose",
        "display_name": "Improper Integrals",
    },
    "applications_of_integration": {
        "difficulty": 3,
        "frequency": "high",  # 19.4% - SECOND MOST COMMON
        "order": 12,
        "color_family": "amber",
        "display_name": "Applications",
    },
    "arc_length": {
        "difficulty": 3,
        "frequency": "medium",  # 5.4%
        "order": 13,
        "color_family": "amber",
        "display_name": "Arc Length",
    },
    "differential_equations": {
        "difficulty": 4,
        "frequency": "high",  # 21.4% - MOST COMMON
        "order": 14,
        "color_family": "rose",
        "display_name": "Differential Equations",
    },
}

# =============================================================================
# SUBTOPIC METADATA
# - difficulty: 1-5 (relative to parent topic)
# - frequent: boolean (commonly tested within topic)
# - order: order within parent topic
# =============================================================================

# Based on real UW exam distribution (645 concept occurrences analyzed):
# Frequent (>=3%): separable_differential_equations (8.0%), initial_value_problems_for_separable_equations (7.3%),
#   washer_method (3.9%), u_substitution_basic (3.6%), center_of_mass_two_dimensional (3.6%),
#   variable_force_work (3.4%), distance_and_force_setup (3.1%), volume_with_respect_to_x (3.1%)

SUBTOPIC_METADATA = {
    # ANTIDERIVATIVES AND RIEMANN SUMS - topic is low frequency
    "basic_antiderivatives": {"difficulty": 1, "frequent": False, "order": 1},
    "initial_value_problems": {"difficulty": 2, "frequent": False, "order": 2},
    "sigma_notation": {"difficulty": 2, "frequent": False, "order": 3},
    "left_riemann_sums": {"difficulty": 2, "frequent": False, "order": 4},
    "right_riemann_sums": {"difficulty": 2, "frequent": False, "order": 5},
    "midpoint_riemann_sums": {"difficulty": 2, "frequent": False, "order": 6},
    "riemann_sum_limit_definition": {"difficulty": 3, "frequent": False, "order": 7},
    "definite_integral_as_area": {"difficulty": 2, "frequent": False, "order": 8},
    "net_change_from_integral": {"difficulty": 2, "frequent": False, "order": 9},  # 2.6%

    # FUNDAMENTAL THEOREM OF CALCULUS - topic is medium frequency (8.7%)
    "accumulation_functions": {"difficulty": 2, "frequent": False, "order": 1},  # 2.0%
    "derivative_of_integral_function": {"difficulty": 3, "frequent": False, "order": 2},  # 2.2%
    "evaluation_by_antiderivatives": {"difficulty": 2, "frequent": False, "order": 3},
    "total_change_theorem": {"difficulty": 2, "frequent": False, "order": 4},
    "indefinite_integrals": {"difficulty": 1, "frequent": False, "order": 5},

    # SUBSTITUTION - topic is medium frequency (11.0%)
    "u_substitution_basic": {"difficulty": 2, "frequent": True, "order": 1},  # 3.6% - FREQUENT
    "u_substitution_with_bounds": {"difficulty": 2, "frequent": False, "order": 2},
    "reverse_chain_rule_recognition": {"difficulty": 3, "frequent": False, "order": 3},
    "algebraic_substitution_setup": {"difficulty": 2, "frequent": False, "order": 4},
    "definite_integral_substitution": {"difficulty": 2, "frequent": False, "order": 5},

    # AREA BETWEEN CURVES - topic is low frequency (4.0%)
    "area_between_two_curves_dx": {"difficulty": 2, "frequent": False, "order": 1},  # 2.0%
    "area_between_two_curves_dy": {"difficulty": 3, "frequent": False, "order": 2},
    "finding_intersection_points_for_area": {"difficulty": 2, "frequent": False, "order": 3},
    "top_minus_bottom_setup": {"difficulty": 2, "frequent": False, "order": 4},
    "right_minus_left_setup": {"difficulty": 2, "frequent": False, "order": 5},

    # VOLUMES - topic is medium frequency (10.7%)
    "cross_sections": {"difficulty": 3, "frequent": False, "order": 1},
    "disk_method": {"difficulty": 2, "frequent": False, "order": 2},  # 2.5%
    "washer_method": {"difficulty": 3, "frequent": True, "order": 3},  # 3.9% - FREQUENT
    "volume_with_respect_to_x": {"difficulty": 2, "frequent": True, "order": 4},  # 3.1% - FREQUENT
    "volume_with_respect_to_y": {"difficulty": 3, "frequent": False, "order": 5},
    "radius_from_geometry": {"difficulty": 3, "frequent": False, "order": 6},
    "inner_outer_radius_setup": {"difficulty": 3, "frequent": False, "order": 7},

    # WORK - topic is medium frequency (7.4%)
    "constant_force_work": {"difficulty": 1, "frequent": False, "order": 1},
    "variable_force_work": {"difficulty": 3, "frequent": True, "order": 2},  # 3.4% - FREQUENT
    "spring_work": {"difficulty": 3, "frequent": False, "order": 3},
    "pumping_liquid_work": {"difficulty": 4, "frequent": False, "order": 4},  # 2.6%
    "distance_and_force_setup": {"difficulty": 3, "frequent": True, "order": 5},  # 3.1% - FREQUENT
    "work_integral_interpretation": {"difficulty": 2, "frequent": False, "order": 6},  # 2.8%

    # INTEGRATION BY PARTS - topic is low frequency (3.0%)
    "integration_by_parts_basic": {"difficulty": 2, "frequent": False, "order": 1},
    "choosing_u_and_dv": {"difficulty": 2, "frequent": False, "order": 2},
    "repeated_integration_by_parts": {"difficulty": 3, "frequent": False, "order": 3},
    "tabular_integration_by_parts": {"difficulty": 3, "frequent": False, "order": 4},
    "integrals_involving_logs": {"difficulty": 3, "frequent": False, "order": 5},
    "integrals_involving_inverse_trig": {"difficulty": 3, "frequent": False, "order": 6},

    # TRIGONOMETRIC INTEGRALS - topic is low frequency (1.7%)
    "powers_of_sine_and_cosine": {"difficulty": 3, "frequent": False, "order": 1},
    "powers_of_tangent_and_secant": {"difficulty": 3, "frequent": False, "order": 2},
    "trig_identity_rewriting": {"difficulty": 3, "frequent": False, "order": 3},
    "odd_even_power_strategy": {"difficulty": 3, "frequent": False, "order": 4},
    "product_of_trig_functions": {"difficulty": 3, "frequent": False, "order": 5},

    # TRIGONOMETRIC SUBSTITUTION - topic is low frequency (1.0%)
    "sqrt_a2_minus_x2_substitution": {"difficulty": 4, "frequent": False, "order": 1},
    "sqrt_a2_plus_x2_substitution": {"difficulty": 4, "frequent": False, "order": 2},
    "sqrt_x2_minus_a2_substitution": {"difficulty": 4, "frequent": False, "order": 3},
    "triangle_back_substitution": {"difficulty": 3, "frequent": False, "order": 4},
    "trigonometric_substitution_setup": {"difficulty": 3, "frequent": False, "order": 5},

    # PARTIAL FRACTIONS - topic is low frequency (0.7%)
    "linear_factor_decomposition": {"difficulty": 2, "frequent": False, "order": 1},
    "repeated_linear_factor_decomposition": {"difficulty": 3, "frequent": False, "order": 2},
    "irreducible_quadratic_decomposition": {"difficulty": 3, "frequent": False, "order": 3},
    "solving_for_coefficients": {"difficulty": 2, "frequent": False, "order": 4},
    "integrating_rational_functions": {"difficulty": 3, "frequent": False, "order": 5},

    # IMPROPER INTEGRALS - topic is medium frequency (5.7%)
    "infinite_interval_integrals": {"difficulty": 2, "frequent": False, "order": 1},
    "vertical_asymptote_integrals": {"difficulty": 3, "frequent": False, "order": 2},
    "splitting_at_discontinuities": {"difficulty": 3, "frequent": False, "order": 3},
    "convergence_of_improper_integrals": {"difficulty": 3, "frequent": False, "order": 4},  # 2.6%
    "divergence_of_improper_integrals": {"difficulty": 3, "frequent": False, "order": 5},

    # APPLICATIONS OF INTEGRATION - topic is high frequency (19.4%)
    "average_value_of_a_function": {"difficulty": 2, "frequent": False, "order": 1},
    "numerical_integration_midpoint_rule": {"difficulty": 2, "frequent": False, "order": 2},
    "numerical_integration_trapezoidal_rule": {"difficulty": 2, "frequent": False, "order": 3},
    "numerical_integration_simpsons_rule": {"difficulty": 3, "frequent": False, "order": 4},
    "error_estimation_for_numerical_integration": {"difficulty": 3, "frequent": False, "order": 5},
    "mass_from_density": {"difficulty": 2, "frequent": False, "order": 6},
    "center_of_mass_one_dimensional": {"difficulty": 3, "frequent": False, "order": 7},
    "center_of_mass_two_dimensional": {"difficulty": 3, "frequent": True, "order": 8},  # 3.6% - FREQUENT
    "moments": {"difficulty": 3, "frequent": False, "order": 9},  # 2.2%

    # ARC LENGTH - topic is medium frequency (5.4%)
    "arc_length_of_y_fx": {"difficulty": 2, "frequent": False, "order": 1},  # 2.5%
    "arc_length_of_x_gy": {"difficulty": 3, "frequent": False, "order": 2},
    "arc_length_integrand_setup": {"difficulty": 2, "frequent": False, "order": 3},  # 2.6%

    # DIFFERENTIAL EQUATIONS - topic is high frequency (21.4%) - MOST COMMON
    "differential_equation_terminology": {"difficulty": 1, "frequent": False, "order": 1},
    "separable_differential_equations": {"difficulty": 3, "frequent": True, "order": 2},  # 8.0% - MOST FREQUENT
    "initial_value_problems_for_separable_equations": {"difficulty": 3, "frequent": True, "order": 3},  # 7.3% - FREQUENT
    "exponential_growth_and_decay": {"difficulty": 3, "frequent": False, "order": 4},  # 2.5%
    "logistic_differential_equation": {"difficulty": 4, "frequent": False, "order": 5},
    "mixing_or_application_modeling": {"difficulty": 4, "frequent": False, "order": 6},
    "solution_verification": {"difficulty": 2, "frequent": False, "order": 7},
}