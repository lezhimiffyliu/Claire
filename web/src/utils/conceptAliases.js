/**
 * Concept Alias Mapping Layer
 *
 * Maps problem.concepts (various naming conventions) to canonical taxonomy subtopics.
 * Taxonomy SECTIONS.concepts remain the canonical source of truth.
 */

// Alias map: problem concept -> canonical taxonomy subtopic
const CONCEPT_ALIASES = {
  // Cross product variants
  cross_product: 'cross_product_computation',
  area_of_parallelogram: 'area_of_parallelogram_via_cross_product',
  volume: 'volume_of_parallelepiped',

  // Tangent planes variants
  tangent_planes: 'tangent_plane_equation',
  linearization: 'linear_approximation_multivariable',

  // Partial derivatives variants
  partial_derivatives: 'partial_derivative_definition',
  derivatives: 'partial_derivative_definition',

  // Optimization variants
  critical_points: 'critical_points_multivariable',
  extrema: 'local_extrema_multivariable',
  saddle_points: 'second_derivative_test_multivariable',
  optimization: 'optimization_with_constraints',
  constrained_optimization: 'optimization_with_constraints',

  // Double integrals variants
  double_integrals: 'double_integrals_over_general_regions',
  multiple_integrals: 'double_integrals_over_general_regions',

  // Polar variants
  polar_coordinates: 'polar_coordinate_conversion',

  // Vector variants
  vectors: 'vector_operations',
  unit_vectors: 'magnitude_and_direction',
  projections: 'vector_projection',

  // Lines and planes variants
  lines: 'parametric_equations_of_lines',
  planes: 'equations_of_planes',
  lines_and_planes: 'equations_of_planes',
  parallel_planes: 'parallel_and_perpendicular_conditions',
  perpendicular_conditions: 'parallel_and_perpendicular_conditions',
  intersection: 'line_plane_intersection',
  distance: 'three_dimensional_coordinate_system',
  distance_formula: 'three_dimensional_coordinate_system',

  // Quadric surfaces variants
  quadric_surfaces: 'surface_identification',
  surfaces: 'surface_identification',
  paraboloid: 'elliptic_paraboloid',
  paraboloids: 'elliptic_paraboloid',
  cylinder: 'cylinders',
  spheres: 'three_dimensional_coordinate_system',

  // Vector valued functions variants
  vector_valued_functions: 'vector_functions_definition',
  parametrization: 'parametrization_of_curves',

  // Motion in space variants
  motion_in_space: 'velocity_vector',
  osculating_plane: 'normal_plane',

  // Taylor variants
  taylor_series: 'taylor_series_definition',
  taylor_polynomials: 'higher_order_taylor_polynomial',
  taylor_polynomials_and_series: 'taylor_series_definition',
  taylor_polynomial_construction: 'higher_order_taylor_polynomial',
  series: 'taylor_series_definition',
  convergence_of_series: 'taylor_series_definition',
  error_bounds: 'error_estimation_taylor',

  // Applications variants
  applications_of_double_integrals: 'mass_from_density_2d',
  center_of_mass: 'center_of_mass_2d',
  density: 'mass_from_density_2d',
  lamina: 'mass_from_density_2d',

  // Multivariable functions variants
  multivariable_optimization: 'critical_points_multivariable',
  directional_derivatives: 'partial_derivative_definition',

  // Other
  three_dimensional_geometry: 'three_dimensional_coordinate_system',
  skew_lines: 'parametric_equations_of_lines',
}

/**
 * Normalize a single concept to its canonical taxonomy subtopic.
 * Returns the alias if found, otherwise returns the original concept.
 */
export function normalizeConcept(concept) {
  return CONCEPT_ALIASES[concept] || concept
}

/**
 * Normalize a list of concepts to canonical taxonomy subtopics.
 * Preserves order, removes duplicates after normalization.
 */
export function normalizeConcepts(concepts) {
  if (!concepts || !Array.isArray(concepts)) return []

  const seen = new Set()
  const result = []
  for (const c of concepts) {
    const normalized = normalizeConcept(c)
    if (!seen.has(normalized)) {
      seen.add(normalized)
      result.push(normalized)
    }
  }
  return result
}

/**
 * Check if a problem matches a section based on concept overlap.
 * Uses normalized concepts for matching.
 */
export function problemMatchesSection(problem, sectionConcepts) {
  if (!problem?.concepts || !sectionConcepts?.length) return false

  const normalizedProblemConcepts = normalizeConcepts(problem.concepts)
  return normalizedProblemConcepts.some(c => sectionConcepts.includes(c))
}

/**
 * Math 126 Sections - maps concepts to textbook sections
 * Source: taxonomy/math126.py SECTIONS
 */
const MATH126_SECTIONS = [
  { id: '12.1', display_name: '3D Coordinate System', concepts: ['three_dimensional_coordinate_system'] },
  { id: '12.2', display_name: 'Vectors', concepts: ['vector_representation', 'vector_operations', 'magnitude_and_direction'] },
  { id: '12.3', display_name: 'Dot Products and Projections', concepts: ['dot_product', 'angle_between_vectors', 'orthogonality', 'vector_projection'] },
  { id: '12.4', display_name: 'Cross Product', concepts: ['cross_product_computation', 'cross_product_geometric_interpretation', 'right_hand_rule', 'area_of_parallelogram_via_cross_product', 'volume_of_parallelepiped'] },
  { id: '12.5', display_name: 'Lines and Planes in Space', concepts: ['parametric_equations_of_lines', 'symmetric_equations_of_lines', 'direction_vectors', 'equations_of_planes', 'normal_vector_to_plane', 'line_plane_intersection', 'parallel_and_perpendicular_conditions'] },
  { id: '12.6', display_name: 'Cylinders and Quadric Surfaces', concepts: ['cylinders', 'elliptic_paraboloid', 'hyperbolic_paraboloid', 'ellipsoid', 'hyperboloid_of_one_sheet', 'hyperboloid_of_two_sheets', 'surface_identification', 'traces_of_surfaces'] },
  { id: '13.1', display_name: 'Vector Functions and Space Curves', concepts: ['vector_functions_definition', 'space_curves', 'component_functions', 'limits_of_vector_functions', 'parametrization_of_curves'] },
  { id: '13.2', display_name: 'Derivatives and Integrals of Vector Functions', concepts: ['derivatives_of_vector_functions', 'integrals_of_vector_functions', 'tangent_vector'] },
  { id: '13.3', display_name: 'Arc Length and Curvature', concepts: ['arc_length_parameterization', 'curvature', 'normal_vector', 'binormal_vector', 'normal_plane'] },
  { id: '13.4', display_name: 'Motion in Space', concepts: ['velocity_vector', 'speed', 'acceleration_vector', 'tangential_and_normal_components'] },
  { id: '14.1', display_name: 'Functions of Several Variables', concepts: ['functions_of_two_variables', 'domain_in_r2', 'level_curves', 'level_surfaces', 'visualization_of_surfaces'] },
  { id: '14.3', display_name: 'Partial Derivatives', concepts: ['partial_derivative_definition', 'higher_order_partial_derivatives', 'mixed_partials', 'clairs_theorem', 'implicit_partial_differentiation'] },
  { id: '14.4', display_name: 'Tangent Planes and Linear Approximations', concepts: ['tangent_plane_equation', 'linear_approximation_multivariable', 'total_differential', 'differentials_interpretation'] },
  { id: '14.7', display_name: 'Maximum and Minimum Values', concepts: ['critical_points_multivariable', 'second_derivative_test_multivariable', 'local_extrema_multivariable', 'global_extrema_multivariable', 'optimization_with_constraints', 'lagrange_multipliers'] },
  { id: '15.1', display_name: 'Double Integrals over Rectangles', concepts: ['double_integrals_over_rectangles'] },
  { id: '15.2', display_name: 'Double Integrals over General Regions', concepts: ['double_integrals_over_general_regions', 'iterated_integrals', 'changing_order_of_integration', 'integration_bounds_setup'] },
  { id: '10.3', display_name: 'Polar Coordinates', concepts: ['polar_coordinate_conversion', 'graphing_in_polar'] },
  { id: '15.3', display_name: 'Double Integrals in Polar Coordinates', concepts: ['area_in_polar_coordinates', 'polar_integral_setup'] },
  { id: '15.4', display_name: 'Applications: Mass and Center of Mass', concepts: ['mass_from_density_2d', 'center_of_mass_2d', 'moments_2d', 'average_value_multivariable'] },
  { id: 'Taylor', display_name: 'Taylor Polynomials and Series', concepts: ['first_order_taylor_polynomial', 'second_order_taylor_polynomial', 'higher_order_taylor_polynomial', 'taylor_series_definition', 'error_estimation_taylor', 'building_new_series_from_known_series', 'power_series_representation'] },
]

/**
 * Find the section that best matches a problem's concepts
 */
export function findSectionForProblem(problem) {
  if (!problem?.concepts?.length) return null

  const normalizedConcepts = normalizeConcepts(problem.concepts)

  let bestMatch = null
  let bestOverlap = 0

  for (const section of MATH126_SECTIONS) {
    const overlap = normalizedConcepts.filter(c => section.concepts.includes(c)).length
    if (overlap > bestOverlap) {
      bestOverlap = overlap
      bestMatch = section
    }
  }

  return bestMatch
}

export default {
  normalizeConcept,
  normalizeConcepts,
  problemMatchesSection,
  findSectionForProblem,
  CONCEPT_ALIASES,
  MATH126_SECTIONS,
}
