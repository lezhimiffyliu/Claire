/**
 * L0 Observations - Pre-authored teacher observations for problems
 *
 * These are "tutor assets" - pedagogical content that Claire displays as
 * ambient observations when a student opens a problem. They are NOT part
 * of the problem data itself.
 *
 * Keys are either:
 *   - problemId (e.g., "uw_math_126_wi25_p3") - applies to entire problem
 *   - partId (e.g., "uw_math_126_wi25_p1_a") - applies to specific part
 *
 * Lookup priority: partId first, then problemId, then null (no observation)
 */

export const L0_OBSERVATIONS = {
  // Math 126 Winter 2025 - Problem 3: Partial Derivatives
  'uw_math_126_wi25_p3': {
    start: [
      'The $\\tan^{-1}$ term has a clean derivative: $\\frac{1}{1+y^2}$.',
      'Watch the $\\cos(xy)$ term - it needs the chain rule twice.',
    ],
    common_mistake: [
      "Don't forget the negative sign when differentiating $\\cos$.",
    ],
  },

  // Math 126 Winter 2025 - Problem 1, Part a: Angle between vectors
  'uw_math_126_wi25_p1_a': {
    start: [
      'The component formula $\\text{comp}_{\\mathbf{a}}\\mathbf{b} = \\frac{\\mathbf{a} \\cdot \\mathbf{b}}{|\\mathbf{a}|}$ connects to $\\cos\\theta$.',
    ],
    common_mistake: [
      "Careful with the negative sign - it tells you the angle is obtuse.",
    ],
  },

  // Math 126 Winter 2025 - Problem 1, Part b: Cross product and area
  'uw_math_126_wi25_p1_b': {
    start: [
      'Triangle area = $\\frac{1}{2}|\\vec{AB} \\times \\vec{AC}|$. The cross product is already given.',
    ],
  },

  // Math 126 Spring 2025 - Problem 1, Part a: Sphere radius
  'uw_math_126_sp25_p1_a': {
    start: [
      'Distance formula in 3D: $d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2 + (z_2-z_1)^2}$.',
    ],
  },
}

/**
 * Look up the L0 observation for a problem/part.
 *
 * @param {string} problemId - The problem ID (e.g., "uw_math_126_wi25_p3")
 * @param {string|null} partLabel - The part label (e.g., "a", "b") or null
 * @returns {string|null} - The observation text, or null if none exists
 */
export function getL0Observation(problemId, partLabel = null) {
  if (!problemId) return null

  // Try part-specific lookup first (key = problemId_partLabel)
  if (partLabel) {
    const partId = `${problemId}_${partLabel}`
    const partObs = L0_OBSERVATIONS[partId]
    if (partObs?.start?.[0]) {
      return partObs.start[0]
    }
  }

  // Fall back to problem-level lookup
  const problemObs = L0_OBSERVATIONS[problemId]
  if (problemObs?.start?.[0]) {
    return problemObs.start[0]
  }

  return null
}

export default L0_OBSERVATIONS
