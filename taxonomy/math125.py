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