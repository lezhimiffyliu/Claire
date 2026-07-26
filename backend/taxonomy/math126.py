"""
UW Math 126 taxonomy for Claire

Purpose:
- Canonical topic and subtopic definitions for question tagging
- Topic names should match heuristic file names under taxonomy/heuristics/
- Subtopics are finer-grained concepts within each topic
- SECTIONS maps to UW Math 126 official syllabus (Stewart's Calculus)

Design rules:
- No aliases
- No vague labels
- No duplicate / overlapping labels when avoidable
- Keep topic names aligned with heuristic filenames

Hierarchy:
  SECTIONS (syllabus-aligned) → concepts → SUBTOPICS (internal keys)
  TOPICS are for heuristic file mapping, independent of SECTIONS
"""

# =============================================================================
# SECTIONS - UW Math 126 Official Syllabus
# Based on Stewart's Calculus + UW Taylor Notes
# Aligned with typical Spring Quarter schedule
#
# Each section has:
#   - id: textbook section number (e.g., "12.1") or notes reference
#   - display_name: student-facing name (from syllabus)
#   - week: which week it's taught (1-10)
#   - order: order within the week (1, 2, 3)
#   - covered_in_exam: "exam_1", "exam_2", or "final"
#   - concepts: list of SUBTOPIC keys covered in this section
# =============================================================================

SECTIONS = [
    # Week 1: 3D Geometry and Vectors
    {
        "id": "12.1",
        "display_name": "3D Coordinate System",
        "week": 1,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "three_dimensional_coordinate_system",
        ],
    },
    {
        "id": "12.2",
        "display_name": "Vectors",
        "week": 1,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "vector_representation",
            "vector_operations",
            "magnitude_and_direction",
        ],
    },
    {
        "id": "12.3",
        "display_name": "Dot Products and Projections",
        "week": 1,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "dot_product",
            "angle_between_vectors",
            "orthogonality",
            "vector_projection",
        ],
    },

    # Week 2: Cross Products, Lines, Planes, Surfaces
    {
        "id": "12.4",
        "display_name": "Cross Product",
        "week": 2,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "cross_product_computation",
            "cross_product_geometric_interpretation",
            "right_hand_rule",
            "area_of_parallelogram_via_cross_product",
            "volume_of_parallelepiped",
        ],
    },
    {
        "id": "12.5",
        "display_name": "Lines and Planes in Space",
        "week": 2,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "parametric_equations_of_lines",
            "symmetric_equations_of_lines",
            "direction_vectors",
            "equations_of_planes",
            "normal_vector_to_plane",
            "line_plane_intersection",
            "parallel_and_perpendicular_conditions",
        ],
    },
    {
        "id": "12.6",
        "display_name": "Cylinders and Quadric Surfaces",
        "week": 2,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "cylinders",
            "elliptic_paraboloid",
            "hyperbolic_paraboloid",
            "ellipsoid",
            "hyperboloid_of_one_sheet",
            "hyperboloid_of_two_sheets",
            "surface_identification",
            "traces_of_surfaces",
        ],
    },

    # Week 3: Vector Functions and Curvature
    {
        "id": "13.1",
        "display_name": "Vector Functions and Space Curves",
        "week": 3,
        "order": 1,
        "covered_in_exam": "exam_1",
        "concepts": [
            "vector_functions_definition",
            "space_curves",
            "component_functions",
            "limits_of_vector_functions",
            "parametrization_of_curves",
        ],
    },
    {
        "id": "13.2",
        "display_name": "Derivatives and Integrals of Vector Functions",
        "week": 3,
        "order": 2,
        "covered_in_exam": "exam_1",
        "concepts": [
            "derivatives_of_vector_functions",
            "integrals_of_vector_functions",
            "tangent_vector",
        ],
    },
    {
        "id": "13.3",
        "display_name": "Arc Length and Curvature",
        "week": 3,
        "order": 3,
        "covered_in_exam": "exam_1",
        "concepts": [
            "arc_length_parameterization",
            "curvature",
            "normal_vector",
            "binormal_vector",
            "normal_plane",
        ],
    },

    # Week 4: Motion in Space (after Exam I)
    {
        "id": "13.4",
        "display_name": "Motion in Space: Velocity and Acceleration",
        "week": 4,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "velocity_vector",
            "speed",
            "acceleration_vector",
            "tangential_and_normal_components",
        ],
    },

    # Week 5: Multivariable Functions and Partial Derivatives
    {
        "id": "14.1",
        "display_name": "Functions of Several Variables",
        "week": 5,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "functions_of_two_variables",
            "domain_in_r2",
            "level_curves",
            "level_surfaces",
            "visualization_of_surfaces",
        ],
    },
    {
        "id": "14.3",
        "display_name": "Partial Derivatives",
        "week": 5,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "partial_derivative_definition",
            "higher_order_partial_derivatives",
            "mixed_partials",
            "clairs_theorem",
            "implicit_partial_differentiation",
        ],
    },
    {
        "id": "14.4",
        "display_name": "Tangent Planes and Linear Approximations",
        "week": 5,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "tangent_plane_equation",
            "linear_approximation_multivariable",
            "total_differential",
            "differentials_interpretation",
        ],
    },

    # Week 6: Optimization and Double Integrals
    {
        "id": "14.7",
        "display_name": "Maximum and Minimum Values",
        "week": 6,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "critical_points_multivariable",
            "second_derivative_test_multivariable",
            "local_extrema_multivariable",
            "global_extrema_multivariable",
            "optimization_with_constraints",
            "lagrange_multipliers",
        ],
    },
    {
        "id": "15.1",
        "display_name": "Double Integrals over Rectangles",
        "week": 6,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "double_integrals_over_rectangles",
        ],
    },
    {
        "id": "15.2",
        "display_name": "Double Integrals over General Regions",
        "week": 6,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "double_integrals_over_general_regions",
            "iterated_integrals",
            "changing_order_of_integration",
            "integration_bounds_setup",
        ],
    },

    # Week 7: Polar Coordinates and Applications
    {
        "id": "10.3",
        "display_name": "Polar Coordinates",
        "week": 7,
        "order": 1,
        "covered_in_exam": "exam_2",
        "concepts": [
            "polar_coordinate_conversion",
            "graphing_in_polar",
        ],
    },
    {
        "id": "15.3",
        "display_name": "Double Integrals in Polar Coordinates",
        "week": 7,
        "order": 2,
        "covered_in_exam": "exam_2",
        "concepts": [
            "area_in_polar_coordinates",
            "polar_integral_setup",
        ],
    },
    {
        "id": "15.4",
        "display_name": "Applications: Mass and Center of Mass",
        "week": 7,
        "order": 3,
        "covered_in_exam": "exam_2",
        "concepts": [
            "mass_from_density_2d",
            "center_of_mass_2d",
            "moments_2d",
            "average_value_multivariable",
        ],
    },

    # Week 8-9: Taylor Polynomials and Series (after Exam II)
    {
        "id": "Taylor1",
        "display_name": "Taylor Polynomials",
        "week": 8,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "first_order_taylor_polynomial",
            "second_order_taylor_polynomial",
            "higher_order_taylor_polynomial",
            "error_estimation_taylor",
        ],
    },
    {
        "id": "Taylor2",
        "display_name": "Taylor Series",
        "week": 9,
        "order": 1,
        "covered_in_exam": "final",
        "concepts": [
            "taylor_series_definition",
            "building_new_series_from_known_series",
            "power_series_representation",
        ],
    },
]

# Helper: Build section lookup by ID
SECTION_BY_ID = {s["id"]: s for s in SECTIONS}

# Ordered by pedagogical dependency (prerequisites first), then frequency
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
        "cross_product_computation",
        "cross_product_geometric_interpretation",
        "area_of_parallelogram_via_cross_product",
        "volume_of_parallelepiped",
        "right_hand_rule",
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

# =============================================================================
# TOPIC METADATA
# - difficulty: 1-5 (cognitive load, not just math complexity)
# - frequency: "high" | "medium" | "low" (how often it appears on exams)
# - order: pedagogical order (prerequisites first, then high-frequency)
# - color_family: color hue for UI (semantic name)
# =============================================================================

TOPIC_METADATA = {
    "vectors_and_geometry": {
        "difficulty": 2,
        "frequency": "high",
        "order": 1,
        "color_family": "blue",
        "display_name": "Vectors & Geometry",
    },
    "lines_and_planes": {
        "difficulty": 3,
        "frequency": "high",
        "order": 2,
        "color_family": "blue",
        "display_name": "Lines & Planes",
    },
    "quadric_surfaces": {
        "difficulty": 2,
        "frequency": "medium",
        "order": 3,
        "color_family": "blue",
        "display_name": "Quadric Surfaces",
    },
    "vector_valued_functions": {
        "difficulty": 3,
        "frequency": "high",
        "order": 4,
        "color_family": "teal",
        "display_name": "Vector Functions",
    },
    "motion_in_space": {
        "difficulty": 3,
        "frequency": "high",
        "order": 5,
        "color_family": "teal",
        "display_name": "Motion in Space",
    },
    "multivariable_functions": {
        "difficulty": 2,
        "frequency": "medium",
        "order": 6,
        "color_family": "green",
        "display_name": "Multivariable Functions",
    },
    "partial_derivatives": {
        "difficulty": 2,
        "frequency": "medium",
        "order": 7,
        "color_family": "green",
        "display_name": "Partial Derivatives",
    },
    "tangent_planes_and_differentials": {
        "difficulty": 3,
        "frequency": "high",
        "order": 8,
        "color_family": "green",
        "display_name": "Tangent Planes",
    },
    "multivariable_optimization": {
        "difficulty": 4,
        "frequency": "high",
        "order": 9,
        "color_family": "amber",
        "display_name": "Optimization",
    },
    "double_integrals": {
        "difficulty": 3,
        "frequency": "high",
        "order": 10,
        "color_family": "purple",
        "display_name": "Double Integrals",
    },
    "polar_coordinates": {
        "difficulty": 3,
        "frequency": "high",
        "order": 11,
        "color_family": "purple",
        "display_name": "Polar Coordinates",
    },
    "applications_of_double_integrals": {
        "difficulty": 3,
        "frequency": "high",
        "order": 12,
        "color_family": "purple",
        "display_name": "Applications",
    },
    "taylor_polynomials_and_series": {
        "difficulty": 4,
        "frequency": "high",
        "order": 13,
        "color_family": "rose",
        "display_name": "Taylor Polynomials",
    },
}

# =============================================================================
# SUBTOPIC METADATA
# - difficulty: 1-5 (relative to parent topic)
# - frequent: boolean (commonly tested within topic)
# - order: order within parent topic
# =============================================================================

SUBTOPIC_METADATA = {
    # VECTORS AND GEOMETRY
    "three_dimensional_coordinate_system": {"difficulty": 1, "frequent": False, "order": 1},
    "vector_representation": {"difficulty": 1, "frequent": True, "order": 2},
    "vector_operations": {"difficulty": 2, "frequent": True, "order": 3},
    "magnitude_and_direction": {"difficulty": 2, "frequent": True, "order": 4},
    "dot_product": {"difficulty": 2, "frequent": True, "order": 5},
    "angle_between_vectors": {"difficulty": 2, "frequent": True, "order": 6},
    "orthogonality": {"difficulty": 2, "frequent": True, "order": 7},
    "vector_projection": {"difficulty": 3, "frequent": True, "order": 8},

    # LINES AND PLANES
    "cross_product_computation": {"difficulty": 2, "frequent": True, "order": 1},
    "cross_product_geometric_interpretation": {"difficulty": 3, "frequent": True, "order": 2},
    "area_of_parallelogram_via_cross_product": {"difficulty": 3, "frequent": True, "order": 3},
    "volume_of_parallelepiped": {"difficulty": 3, "frequent": False, "order": 4},
    "right_hand_rule": {"difficulty": 2, "frequent": True, "order": 5},
    "parametric_equations_of_lines": {"difficulty": 2, "frequent": True, "order": 6},
    "symmetric_equations_of_lines": {"difficulty": 2, "frequent": True, "order": 7},
    "direction_vectors": {"difficulty": 2, "frequent": True, "order": 8},
    "equations_of_planes": {"difficulty": 3, "frequent": True, "order": 9},
    "normal_vector_to_plane": {"difficulty": 2, "frequent": True, "order": 10},
    "line_plane_intersection": {"difficulty": 3, "frequent": True, "order": 11},
    "parallel_and_perpendicular_conditions": {"difficulty": 3, "frequent": True, "order": 12},

    # QUADRIC SURFACES
    "cylinders": {"difficulty": 1, "frequent": False, "order": 1},
    "elliptic_paraboloid": {"difficulty": 2, "frequent": True, "order": 2},
    "hyperbolic_paraboloid": {"difficulty": 2, "frequent": True, "order": 3},
    "ellipsoid": {"difficulty": 2, "frequent": True, "order": 4},
    "hyperboloid_of_one_sheet": {"difficulty": 2, "frequent": True, "order": 5},
    "hyperboloid_of_two_sheets": {"difficulty": 2, "frequent": True, "order": 6},
    "surface_identification": {"difficulty": 3, "frequent": True, "order": 7},
    "traces_of_surfaces": {"difficulty": 2, "frequent": True, "order": 8},

    # VECTOR VALUED FUNCTIONS
    "vector_functions_definition": {"difficulty": 1, "frequent": False, "order": 1},
    "space_curves": {"difficulty": 2, "frequent": True, "order": 2},
    "component_functions": {"difficulty": 2, "frequent": True, "order": 3},
    "limits_of_vector_functions": {"difficulty": 2, "frequent": False, "order": 4},
    "derivatives_of_vector_functions": {"difficulty": 2, "frequent": True, "order": 5},
    "integrals_of_vector_functions": {"difficulty": 2, "frequent": True, "order": 6},
    "tangent_vector": {"difficulty": 2, "frequent": True, "order": 7},
    "parametrization_of_curves": {"difficulty": 3, "frequent": True, "order": 8},

    # MOTION IN SPACE
    "velocity_vector": {"difficulty": 2, "frequent": True, "order": 1},
    "speed": {"difficulty": 2, "frequent": True, "order": 2},
    "acceleration_vector": {"difficulty": 2, "frequent": True, "order": 3},
    "tangential_and_normal_components": {"difficulty": 4, "frequent": True, "order": 4},
    "arc_length_parameterization": {"difficulty": 3, "frequent": True, "order": 5},
    "curvature": {"difficulty": 4, "frequent": True, "order": 6},
    "normal_vector": {"difficulty": 3, "frequent": True, "order": 7},
    "binormal_vector": {"difficulty": 3, "frequent": False, "order": 8},
    "normal_plane": {"difficulty": 3, "frequent": False, "order": 9},

    # MULTIVARIABLE FUNCTIONS
    "functions_of_two_variables": {"difficulty": 1, "frequent": True, "order": 1},
    "domain_in_r2": {"difficulty": 2, "frequent": True, "order": 2},
    "level_curves": {"difficulty": 2, "frequent": True, "order": 3},
    "level_surfaces": {"difficulty": 2, "frequent": False, "order": 4},
    "visualization_of_surfaces": {"difficulty": 2, "frequent": False, "order": 5},

    # PARTIAL DERIVATIVES
    "partial_derivative_definition": {"difficulty": 2, "frequent": True, "order": 1},
    "higher_order_partial_derivatives": {"difficulty": 2, "frequent": True, "order": 2},
    "mixed_partials": {"difficulty": 2, "frequent": True, "order": 3},
    "clairs_theorem": {"difficulty": 2, "frequent": False, "order": 4},
    "implicit_partial_differentiation": {"difficulty": 3, "frequent": True, "order": 5},

    # TANGENT PLANES AND DIFFERENTIALS
    "tangent_plane_equation": {"difficulty": 2, "frequent": True, "order": 1},
    "linear_approximation_multivariable": {"difficulty": 3, "frequent": True, "order": 2},
    "total_differential": {"difficulty": 3, "frequent": True, "order": 3},
    "differentials_interpretation": {"difficulty": 3, "frequent": False, "order": 4},

    # MULTIVARIABLE OPTIMIZATION
    "critical_points_multivariable": {"difficulty": 3, "frequent": True, "order": 1},
    "second_derivative_test_multivariable": {"difficulty": 4, "frequent": True, "order": 2},
    "local_extrema_multivariable": {"difficulty": 3, "frequent": True, "order": 3},
    "global_extrema_multivariable": {"difficulty": 4, "frequent": True, "order": 4},
    "optimization_with_constraints": {"difficulty": 4, "frequent": True, "order": 5},
    "lagrange_multipliers": {"difficulty": 5, "frequent": True, "order": 6},

    # DOUBLE INTEGRALS
    "double_integrals_over_rectangles": {"difficulty": 2, "frequent": True, "order": 1},
    "double_integrals_over_general_regions": {"difficulty": 3, "frequent": True, "order": 2},
    "iterated_integrals": {"difficulty": 2, "frequent": True, "order": 3},
    "changing_order_of_integration": {"difficulty": 4, "frequent": True, "order": 4},
    "integration_bounds_setup": {"difficulty": 3, "frequent": True, "order": 5},

    # POLAR COORDINATES
    "polar_coordinate_conversion": {"difficulty": 2, "frequent": True, "order": 1},
    "graphing_in_polar": {"difficulty": 2, "frequent": False, "order": 2},
    "area_in_polar_coordinates": {"difficulty": 3, "frequent": True, "order": 3},
    "polar_integral_setup": {"difficulty": 3, "frequent": True, "order": 4},

    # APPLICATIONS OF DOUBLE INTEGRALS
    "mass_from_density_2d": {"difficulty": 3, "frequent": True, "order": 1},
    "center_of_mass_2d": {"difficulty": 3, "frequent": True, "order": 2},
    "moments_2d": {"difficulty": 3, "frequent": True, "order": 3},
    "average_value_multivariable": {"difficulty": 2, "frequent": True, "order": 4},

    # TAYLOR POLYNOMIALS AND SERIES
    "first_order_taylor_polynomial": {"difficulty": 2, "frequent": True, "order": 1},
    "second_order_taylor_polynomial": {"difficulty": 3, "frequent": True, "order": 2},
    "higher_order_taylor_polynomial": {"difficulty": 3, "frequent": True, "order": 3},
    "taylor_series_definition": {"difficulty": 3, "frequent": True, "order": 4},
    "error_estimation_taylor": {"difficulty": 4, "frequent": True, "order": 5},
    "building_new_series_from_known_series": {"difficulty": 4, "frequent": True, "order": 6},
    "power_series_representation": {"difficulty": 3, "frequent": True, "order": 7},
}