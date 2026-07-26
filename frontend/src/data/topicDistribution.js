/**
 * Topic Distribution Data
 *
 * Generated from /problems/*.json
 * Used to prioritize learning path recommendations.
 *
 * Formula: topic_weight = points_total + problem_count × 0.5
 */

export const TOPIC_DISTRIBUTION = {
  math124: [
    { topic: "curve_analysis", count: 31, points: 433, weight: 448.5 },
    { topic: "derivative_rules", count: 18, points: 237, weight: 246.0 },
    { topic: "related_rates", count: 18, points: 213, weight: 222.0 },
    { topic: "optimization", count: 17, points: 204, weight: 212.5 },
    { topic: "limits", count: 15, points: 186, weight: 193.5 },
    { topic: "parametric_equations", count: 14, points: 163, weight: 170.0 },
    { topic: "implicit_differentiation", count: 13, points: 152, weight: 158.5 },
    { topic: "linear_approximation", count: 7, points: 78, weight: 81.5 },
    { topic: "lhopitals_rule", count: 2, points: 27, weight: 28.0 },
    { topic: "continuity", count: 1, points: 12, weight: 12.5 },
  ],
  math125: [
    { topic: "differential_equations", count: 64, points: 651, weight: 683.0 },
    { topic: "applications_of_integration", count: 58, points: 598, weight: 627.0 },
    { topic: "substitution", count: 33, points: 358, weight: 374.5 },
    { topic: "volumes", count: 32, points: 307, weight: 323.0 },
    { topic: "fundamental_theorem_of_calculus", count: 26, points: 270, weight: 283.0 },
    { topic: "work", count: 22, points: 220, weight: 231.0 },
    { topic: "improper_integrals", count: 17, points: 170, weight: 178.5 },
    { topic: "arc_length", count: 16, points: 160, weight: 168.0 },
    { topic: "area_between_curves", count: 12, points: 122, weight: 128.0 },
    { topic: "integration_by_parts", count: 9, points: 94, weight: 98.5 },
    { topic: "trigonometric_integrals", count: 5, points: 52, weight: 54.5 },
    { topic: "trigonometric_substitution", count: 3, points: 24, weight: 25.5 },
    { topic: "partial_fractions", count: 2, points: 22, weight: 23.0 },
  ],
  math126: [
    { topic: "taylor_polynomials_and_series", count: 79, points: 996, weight: 1035.5 },
    { topic: "double_integrals", count: 41, points: 492, weight: 512.5 },
    { topic: "multivariable_optimization", count: 41, points: 487, weight: 507.5 },
    { topic: "lines_and_planes", count: 35, points: 386, weight: 403.5 },
    { topic: "motion_in_space", count: 27, points: 307, weight: 320.5 },
    { topic: "vector_valued_functions", count: 21, points: 249, weight: 259.5 },
    { topic: "applications_of_double_integrals", count: 19, points: 215, weight: 224.5 },
    { topic: "tangent_planes_and_differentials", count: 19, points: 207, weight: 216.5 },
    { topic: "vectors_and_geometry", count: 18, points: 192, weight: 201.0 },
    { topic: "polar_coordinates", count: 10, points: 118, weight: 123.0 },
    { topic: "partial_derivatives", count: 10, points: 117, weight: 122.0 },
    { topic: "quadric_surfaces", count: 8, points: 77, weight: 81.0 },
    { topic: "multivariable_functions", count: 5, points: 56, weight: 58.5 },
  ],
}

/**
 * Get topic distribution for a course, sorted by weight
 */
export function getTopicsByWeight(course) {
  return TOPIC_DISTRIBUTION[course] || []
}

/**
 * Get the weight for a specific topic
 */
export function getTopicWeight(course, topic) {
  const dist = TOPIC_DISTRIBUTION[course] || []
  const entry = dist.find(d => d.topic === topic)
  return entry ? entry.weight : 0
}

/**
 * Get display name for a topic (convert snake_case to Title Case)
 */
export function getTopicDisplayName(topic) {
  return topic
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default TOPIC_DISTRIBUTION
