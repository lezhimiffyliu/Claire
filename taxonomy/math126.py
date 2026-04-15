"""
UW Math 126 taxonomy for Claire

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
    "vectors_and_geometry",
    "lines_and_planes",
    "quadric_surfaces",
    "vector_valued_functions",
    "motion_in_space",
    "multivariable_functions",
    "partial_derivatives",
    "tangent_planes_and_differentials",
    "multivariable_optimization",
    "double_integrals",
    "polar_coordinates",
    "applications_of_double_integrals",
    "taylor_polynomials_and_series",
]

SUBTOPICS = {
    "vectors_and_geometry": [
        "three_dimensional_coordinate_system",
        "vector_representation",
        "vector_operations",
        "magnitude_and_direction",
        "dot_product",
        "angle_between_vectors",
        "orthogonality",
        "vector_projection",
    ],

    "lines_and_planes": [
        "parametric_equations_of_lines",
        "symmetric_equations_of_lines",
        "direction_vectors",
        "equations_of_planes",
        "normal_vector_to_plane",
        "line_plane_intersection",
        "parallel_and_perpendicular_conditions",
    ],

    "quadric_surfaces": [
        "cylinders",
        "elliptic_paraboloid",
        "hyperbolic_paraboloid",
        "ellipsoid",
        "hyperboloid_of_one_sheet",
        "hyperboloid_of_two_sheets",
        "surface_identification",
        "traces_of_surfaces",
    ],

    "vector_valued_functions": [
        "vector_functions_definition",
        "space_curves",
        "component_functions",
        "limits_of_vector_functions",
        "derivatives_of_vector_functions",
        "integrals_of_vector_functions",
        "tangent_vector",
        "parametrization_of_curves",
    ],

    "motion_in_space": [
        "velocity_vector",
        "speed",
        "acceleration_vector",
        "tangential_and_normal_components",
        "arc_length_parameterization",
        "curvature",
        "normal_vector",
        "binormal_vector",
        "normal_plane",
    ],

    "multivariable_functions": [
        "functions_of_two_variables",
        "domain_in_r2",
        "level_curves",
        "level_surfaces",
        "visualization_of_surfaces",
    ],

    "partial_derivatives": [
        "partial_derivative_definition",
        "higher_order_partial_derivatives",
        "mixed_partials",
        "clairs_theorem",
        "implicit_partial_differentiation",
    ],

    "tangent_planes_and_differentials": [
        "tangent_plane_equation",
        "linear_approximation_multivariable",
        "total_differential",
        "differentials_interpretation",
    ],

    "multivariable_optimization": [
        "critical_points_multivariable",
        "second_derivative_test_multivariable",
        "local_extrema_multivariable",
        "global_extrema_multivariable",
        "optimization_with_constraints",
        "lagrange_multipliers",
    ],

    "double_integrals": [
        "double_integrals_over_rectangles",
        "double_integrals_over_general_regions",
        "iterated_integrals",
        "changing_order_of_integration",
        "integration_bounds_setup",
    ],

    "polar_coordinates": [
        "polar_coordinate_conversion",
        "graphing_in_polar",
        "area_in_polar_coordinates",
        "polar_integral_setup",
    ],

    "applications_of_double_integrals": [
        "mass_from_density_2d",
        "center_of_mass_2d",
        "moments_2d",
        "average_value_multivariable",
    ],

    "taylor_polynomials_and_series": [
        "first_order_taylor_polynomial",
        "second_order_taylor_polynomial",
        "higher_order_taylor_polynomial",
        "taylor_series_definition",
        "error_estimation_taylor",
        "building_new_series_from_known_series",
        "power_series_representation",
    ],
}