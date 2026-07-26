/**
 * Taxonomy Metadata for Claire UI
 *
 * Centralized color and metadata system for topics/subtopics.
 * Low-saturation, learning-product-friendly color palette.
 */

// =============================================================================
// COLOR PALETTE
// Each color family has 5 shades (1=lightest, 5=darkest) for difficulty levels
// =============================================================================

const COLOR_FAMILIES = {
  blue: {
    1: { bg: '#EFF6FF', text: '#1E40AF', border: '#BFDBFE' },
    2: { bg: '#DBEAFE', text: '#1E3A8A', border: '#93C5FD' },
    3: { bg: '#BFDBFE', text: '#1E3A8A', border: '#60A5FA' },
    4: { bg: '#93C5FD', text: '#1E3A8A', border: '#3B82F6' },
    5: { bg: '#60A5FA', text: '#FFFFFF', border: '#2563EB' },
  },
  teal: {
    1: { bg: '#F0FDFA', text: '#115E59', border: '#99F6E4' },
    2: { bg: '#CCFBF1', text: '#0F766E', border: '#5EEAD4' },
    3: { bg: '#99F6E4', text: '#0F766E', border: '#2DD4BF' },
    4: { bg: '#5EEAD4', text: '#0F766E', border: '#14B8A6' },
    5: { bg: '#2DD4BF', text: '#FFFFFF', border: '#0D9488' },
  },
  green: {
    1: { bg: '#F0FDF4', text: '#166534', border: '#BBF7D0' },
    2: { bg: '#DCFCE7', text: '#15803D', border: '#86EFAC' },
    3: { bg: '#BBF7D0', text: '#15803D', border: '#4ADE80' },
    4: { bg: '#86EFAC', text: '#15803D', border: '#22C55E' },
    5: { bg: '#4ADE80', text: '#FFFFFF', border: '#16A34A' },
  },
  purple: {
    1: { bg: '#FAF5FF', text: '#6B21A8', border: '#E9D5FF' },
    2: { bg: '#F3E8FF', text: '#7E22CE', border: '#D8B4FE' },
    3: { bg: '#E9D5FF', text: '#7E22CE', border: '#C084FC' },
    4: { bg: '#D8B4FE', text: '#7E22CE', border: '#A855F7' },
    5: { bg: '#C084FC', text: '#FFFFFF', border: '#9333EA' },
  },
  orange: {
    1: { bg: '#FFF7ED', text: '#9A3412', border: '#FED7AA' },
    2: { bg: '#FFEDD5', text: '#C2410C', border: '#FDBA74' },
    3: { bg: '#FED7AA', text: '#C2410C', border: '#FB923C' },
    4: { bg: '#FDBA74', text: '#C2410C', border: '#F97316' },
    5: { bg: '#FB923C', text: '#FFFFFF', border: '#EA580C' },
  },
  amber: {
    1: { bg: '#FFFBEB', text: '#92400E', border: '#FDE68A' },
    2: { bg: '#FEF3C7', text: '#B45309', border: '#FCD34D' },
    3: { bg: '#FDE68A', text: '#B45309', border: '#FBBF24' },
    4: { bg: '#FCD34D', text: '#B45309', border: '#F59E0B' },
    5: { bg: '#FBBF24', text: '#78350F', border: '#D97706' },
  },
  rose: {
    1: { bg: '#FFF1F2', text: '#9F1239', border: '#FECDD3' },
    2: { bg: '#FFE4E6', text: '#BE123C', border: '#FDA4AF' },
    3: { bg: '#FECDD3', text: '#BE123C', border: '#FB7185' },
    4: { bg: '#FDA4AF', text: '#BE123C', border: '#F43F5E' },
    5: { bg: '#FB7185', text: '#FFFFFF', border: '#E11D48' },
  },
}

// =============================================================================
// TOPIC METADATA (mirrors Python taxonomy)
// =============================================================================

export const TOPIC_METADATA = {
  math124: {
    limits: { difficulty: 2, frequency: 'high', order: 1, colorFamily: 'blue', displayName: 'Limits' },
    continuity: { difficulty: 2, frequency: 'low', order: 2, colorFamily: 'blue', displayName: 'Continuity' },
    derivative_definition: { difficulty: 2, frequency: 'medium', order: 3, colorFamily: 'teal', displayName: 'Derivative Definition' },
    derivative_rules: { difficulty: 2, frequency: 'high', order: 4, colorFamily: 'teal', displayName: 'Derivative Rules' },
    implicit_differentiation: { difficulty: 3, frequency: 'high', order: 5, colorFamily: 'teal', displayName: 'Implicit Differentiation' },
    parametric_equations: { difficulty: 3, frequency: 'high', order: 6, colorFamily: 'purple', displayName: 'Parametric Equations' },
    related_rates: { difficulty: 4, frequency: 'high', order: 7, colorFamily: 'orange', displayName: 'Related Rates' },
    linear_approximation: { difficulty: 3, frequency: 'medium', order: 8, colorFamily: 'green', displayName: 'Linear Approximation' },
    curve_analysis: { difficulty: 3, frequency: 'high', order: 9, colorFamily: 'rose', displayName: 'Curve Analysis' },
    lhopitals_rule: { difficulty: 3, frequency: 'low', order: 10, colorFamily: 'blue', displayName: "L'Hôpital's Rule" },
    optimization: { difficulty: 4, frequency: 'high', order: 11, colorFamily: 'amber', displayName: 'Optimization' },
  },
  math125: {
    antiderivatives_and_riemann_sums: { difficulty: 2, frequency: 'medium', order: 1, colorFamily: 'blue', displayName: 'Antiderivatives & Riemann Sums' },
    fundamental_theorem_of_calculus: { difficulty: 2, frequency: 'high', order: 2, colorFamily: 'blue', displayName: 'Fundamental Theorem' },
    substitution: { difficulty: 2, frequency: 'high', order: 3, colorFamily: 'teal', displayName: 'U-Substitution' },
    area_between_curves: { difficulty: 2, frequency: 'medium', order: 4, colorFamily: 'green', displayName: 'Area Between Curves' },
    volumes: { difficulty: 3, frequency: 'high', order: 5, colorFamily: 'green', displayName: 'Volumes of Revolution' },
    work: { difficulty: 3, frequency: 'high', order: 6, colorFamily: 'orange', displayName: 'Work' },
    integration_by_parts: { difficulty: 3, frequency: 'medium', order: 7, colorFamily: 'purple', displayName: 'Integration by Parts' },
    trigonometric_integrals: { difficulty: 3, frequency: 'medium', order: 8, colorFamily: 'purple', displayName: 'Trig Integrals' },
    trigonometric_substitution: { difficulty: 4, frequency: 'low', order: 9, colorFamily: 'purple', displayName: 'Trig Substitution' },
    partial_fractions: { difficulty: 3, frequency: 'low', order: 10, colorFamily: 'purple', displayName: 'Partial Fractions' },
    improper_integrals: { difficulty: 3, frequency: 'high', order: 11, colorFamily: 'rose', displayName: 'Improper Integrals' },
    applications_of_integration: { difficulty: 3, frequency: 'high', order: 12, colorFamily: 'amber', displayName: 'Applications' },
    arc_length: { difficulty: 3, frequency: 'high', order: 13, colorFamily: 'amber', displayName: 'Arc Length' },
    differential_equations: { difficulty: 4, frequency: 'high', order: 14, colorFamily: 'rose', displayName: 'Differential Equations' },
  },
  math126: {
    vectors_and_geometry: { difficulty: 2, frequency: 'high', order: 1, colorFamily: 'blue', displayName: 'Vectors & Geometry' },
    lines_and_planes: { difficulty: 3, frequency: 'high', order: 2, colorFamily: 'blue', displayName: 'Lines & Planes' },
    quadric_surfaces: { difficulty: 2, frequency: 'medium', order: 3, colorFamily: 'blue', displayName: 'Quadric Surfaces' },
    vector_valued_functions: { difficulty: 3, frequency: 'high', order: 4, colorFamily: 'teal', displayName: 'Vector Functions' },
    motion_in_space: { difficulty: 3, frequency: 'high', order: 5, colorFamily: 'teal', displayName: 'Motion in Space' },
    multivariable_functions: { difficulty: 2, frequency: 'medium', order: 6, colorFamily: 'green', displayName: 'Multivariable Functions' },
    partial_derivatives: { difficulty: 2, frequency: 'medium', order: 7, colorFamily: 'green', displayName: 'Partial Derivatives' },
    tangent_planes_and_differentials: { difficulty: 3, frequency: 'high', order: 8, colorFamily: 'green', displayName: 'Tangent Planes' },
    multivariable_optimization: { difficulty: 4, frequency: 'high', order: 9, colorFamily: 'amber', displayName: 'Optimization' },
    double_integrals: { difficulty: 3, frequency: 'high', order: 10, colorFamily: 'purple', displayName: 'Double Integrals' },
    polar_coordinates: { difficulty: 3, frequency: 'high', order: 11, colorFamily: 'purple', displayName: 'Polar Coordinates' },
    applications_of_double_integrals: { difficulty: 3, frequency: 'high', order: 12, colorFamily: 'purple', displayName: 'Applications' },
    taylor_polynomials_and_series: { difficulty: 4, frequency: 'high', order: 13, colorFamily: 'rose', displayName: 'Taylor Polynomials' },
  },
}

// =============================================================================
// SUBTOPIC METADATA (subset - frequently used ones)
// =============================================================================

export const SUBTOPIC_METADATA = {
  // Math 124
  chain_rule: { difficulty: 3, frequent: true },
  product_rule: { difficulty: 2, frequent: true },
  quotient_rule: { difficulty: 2, frequent: true },
  critical_points: { difficulty: 2, frequent: true },
  curve_sketching: { difficulty: 4, frequent: true },
  related_rates_setup: { difficulty: 3, frequent: true },
  optimization_setup: { difficulty: 3, frequent: true },

  // Math 125
  u_substitution_basic: { difficulty: 2, frequent: true },
  disk_method: { difficulty: 2, frequent: true },
  washer_method: { difficulty: 3, frequent: true },
  integration_by_parts_basic: { difficulty: 2, frequent: true },
  separable_differential_equations: { difficulty: 3, frequent: true },

  // Math 126
  dot_product: { difficulty: 2, frequent: true },
  equations_of_planes: { difficulty: 3, frequent: true },
  lagrange_multipliers: { difficulty: 5, frequent: true },
  changing_order_of_integration: { difficulty: 4, frequent: true },
  second_order_taylor_polynomial: { difficulty: 3, frequent: true },
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get color scheme for a topic based on its color family and difficulty
 * @param {string} topic - Topic slug
 * @param {string} course - Course name (math124, math125, math126)
 * @returns {{ bg: string, text: string, border: string }}
 */
export function getTopicColor(topic, course) {
  const meta = TOPIC_METADATA[course]?.[topic]
  if (!meta) {
    return COLOR_FAMILIES.blue[2] // Default fallback
  }

  const colorFamily = COLOR_FAMILIES[meta.colorFamily] || COLOR_FAMILIES.blue
  const difficulty = Math.min(5, Math.max(1, meta.difficulty))
  return colorFamily[difficulty]
}

/**
 * Get color for a specific difficulty level within a color family
 * @param {string} colorFamily - Color family name
 * @param {number} difficulty - Difficulty level 1-5
 * @returns {{ bg: string, text: string, border: string }}
 */
export function getDifficultyShade(colorFamily, difficulty) {
  const family = COLOR_FAMILIES[colorFamily] || COLOR_FAMILIES.blue
  const level = Math.min(5, Math.max(1, difficulty))
  return family[level]
}

/**
 * Get display name for a topic
 * @param {string} topic - Topic slug
 * @param {string} course - Course name
 * @returns {string}
 */
export function getTopicDisplayName(topic, course) {
  const meta = TOPIC_METADATA[course]?.[topic]
  if (meta?.displayName) {
    return meta.displayName
  }
  // Fallback: convert snake_case to Title Case
  return topic
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Get all topics for a course, sorted by order
 * @param {string} course - Course name
 * @returns {Array<{ topic: string, ...metadata }>}
 */
export function getTopicsSorted(course) {
  const courseMeta = TOPIC_METADATA[course]
  if (!courseMeta) return []

  return Object.entries(courseMeta)
    .map(([topic, meta]) => ({ topic, ...meta }))
    .sort((a, b) => a.order - b.order)
}

/**
 * Check if a topic is high frequency (commonly tested)
 * @param {string} topic - Topic slug
 * @param {string} course - Course name
 * @returns {boolean}
 */
export function isHighFrequency(topic, course) {
  const meta = TOPIC_METADATA[course]?.[topic]
  return meta?.frequency === 'high'
}

/**
 * Get frequency label for display
 * @param {string} frequency - "high" | "medium" | "low"
 * @returns {string}
 */
export function getFrequencyLabel(frequency) {
  switch (frequency) {
    case 'high':
      return 'Frequent'
    case 'medium':
      return 'Common'
    case 'low':
      return 'Rare'
    default:
      return ''
  }
}

/**
 * Get difficulty indicator (dots or text)
 * @param {number} difficulty - 1-5
 * @returns {string}
 */
export function getDifficultyIndicator(difficulty) {
  const level = Math.min(5, Math.max(1, difficulty))
  return '●'.repeat(level) + '○'.repeat(5 - level)
}

/**
 * Get all color families (for legend/debugging)
 */
export function getColorFamilies() {
  return COLOR_FAMILIES
}

export default {
  TOPIC_METADATA,
  SUBTOPIC_METADATA,
  getTopicColor,
  getDifficultyShade,
  getTopicDisplayName,
  getTopicsSorted,
  isHighFrequency,
  getFrequencyLabel,
  getDifficultyIndicator,
  getColorFamilies,
}
