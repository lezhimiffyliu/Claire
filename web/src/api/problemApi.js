/**
 * Problem API - Calls with Bearer token for authenticated requests
 *
 * Security:
 * - All authenticated requests include Authorization: Bearer <token>
 * - Token is obtained from Supabase auth session
 * - RLS is enforced on backend based on auth.uid()
 */

import { supabase } from '../lib/supabase'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Get current session access token (if authenticated)
 */
async function getAccessToken() {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

/**
 * Build headers with optional Bearer token
 */
async function buildHeaders(includeAuth = true) {
  const headers = { 'Content-Type': 'application/json' }

  if (includeAuth) {
    const token = await getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

/**
 * Get personalized problem recommendations
 *
 * Returns recommendations based on:
 * - Student profile (if authenticated)
 * - Recent attempt history
 * - Topic mastery levels
 *
 * @param {string} course - Course code ("124", "125", "126")
 * @returns {Promise<{recommendations: Array, profile_summary: Object}>}
 */
export async function getRecommendations(course = '124') {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/recommendations?course=${course}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Failed to get recommendations: ${response.status}`)
  }

  return response.json()
}

/**
 * Send chat message with optional example-level memory
 *
 * When problem_id is provided and user is authenticated,
 * the backend will inject relevant past attempt context.
 *
 * @param {string} message - User's message
 * @param {Object} options - Options
 * @param {string} [options.level='beginner'] - User level
 * @param {boolean} [options.guidedMode=true] - Guided mode flag
 * @param {string} [options.problemId] - Current problem ID for memory context
 * @returns {Promise<{output: string, intermediate_steps: Array, usage: Object}>}
 */
export async function sendChatMessage(message, options = {}) {
  const {
    level = 'beginner',
    guidedMode = true,
    problemId = null,
  } = options

  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      level,
      guided_mode: guidedMode,
      problem_id: problemId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Chat failed: ${response.status}`)
  }

  return response.json()
}

/**
 * Get problem help with memory context
 *
 * @param {Object} problem - Problem object
 * @param {number} [partIndex=0] - Part index
 * @returns {Promise<Object>}
 */
export async function getProblemHelp(problem, partIndex = 0) {
  let message = `Help me understand this problem:\n\n`

  if (problem.stem) {
    message += `${problem.stem}\n\n`
  }

  if (problem.parts && problem.parts.length > 0) {
    const part = problem.parts[partIndex] || problem.parts[0]
    message += `Part ${part.label || partIndex + 1}: ${part.question_text}`
  }

  message += `\n\nPlease guide me through solving this step by step.`

  return sendChatMessage(message, {
    problemId: problem.id,
  })
}

/**
 * Get exam countdown for the current user
 *
 * @returns {Promise<{next_exam: string, next_exam_display: string, days_until: number, course: string, course_display: string}>}
 */
export async function getExamCountdown() {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/exam-countdown`, {
    method: 'GET',
    headers,
  })

  // Default values - will be overridden by user's popup selection
  if (!response.ok) {
    return {
      next_exam: 'midterm_1',
      next_exam_display: 'Midterm I',
      days_until: 14,
      course: 'math126',
      course_display: 'Math 126',
    }
  }

  return response.json()
}

/**
 * Get must-know sections before an exam
 *
 * @param {string} exam - "exam_1" | "exam_2" | "final"
 * @returns {Promise<{sections: Array, exam: string}>}
 */
export async function getMustKnowSections(exam = 'exam_1') {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/must-know-sections?exam=${exam}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    return { sections: [], exam }
  }

  return response.json()
}

/**
 * Get roadmap state for all sections
 *
 * @returns {Promise<{sections: Array, current_section_id: string|null}>}
 */
export async function getRoadmapState() {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/roadmap-state`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    return { sections: [], current_section_id: null }
  }

  return response.json()
}

/**
 * Get user quota status
 *
 * @returns {Promise<{is_pro: boolean, limit_reached: boolean, remaining: number}>}
 */
export async function getQuotaStatus() {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/quota`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    return { is_pro: false, limit_reached: false, remaining: 20 }
  }

  return response.json()
}

/**
 * Create Stripe checkout session
 *
 * @param {string} userId
 * @param {string} email
 * @returns {Promise<{checkout_url: string|null, error: string|null}>}
 */
export async function createCheckout(userId, email) {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/checkout`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ user_id: userId, email }),
  })

  return response.json()
}

/**
 * Save student preferences (exam date, prep level, target goal)
 *
 * Saves to backend profile (if authenticated).
 * Frontend should also save to localStorage for anonymous users.
 *
 * @param {Object} preferences - Preferences to save
 * @param {string} [preferences.exam_date] - ISO date string (YYYY-MM-DD)
 * @param {string} [preferences.prep_level] - Prep level ID
 * @param {string} [preferences.target_goal] - Target goal ID
 * @returns {Promise<{status: string, message: string}>}
 */
export async function saveStudentPreferences({ exam_type, exam_date, prep_level, target_goal }) {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/student-preferences`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ exam_type, exam_date, prep_level, target_goal }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Failed to save preferences: ${response.status}`)
  }

  return response.json()
}

/**
 * Get personalized roadmap based on plan mode
 *
 * Reads from profile first, falls back to localStorage values passed as query params.
 *
 * @param {string} course - Course code ("124", "125", "126")
 * @returns {Promise<Object>} - Roadmap response with blocks
 */
export async function getRoadmap(course = '126') {
  const headers = await buildHeaders(true)

  // Build query params with localStorage fallbacks
  const params = new URLSearchParams({ course })

  // Pass localStorage values as fallback query params
  const examDate = localStorage.getItem('claire_exam_date')
  const prepLevel = localStorage.getItem('claire_prep_level')
  const targetGoal = localStorage.getItem('claire_target_goal')

  if (examDate) params.append('exam_date', examDate)
  if (prepLevel) params.append('prep_level', prepLevel)
  if (targetGoal) params.append('target_goal', targetGoal)

  const response = await fetch(`${API_BASE}/api/roadmap?${params}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    return {
      plan_mode: 'sweep',
      plan_mode_description: { title: 'Full Sweep', description: 'Explore all topics', icon: 'compass' },
      roadmap_blocks: [],
      current_block: null,
      fallback_to_legacy: true,
    }
  }

  return response.json()
}

/**
 * Get remediation items for a problem
 *
 * V1: Only returns remediation if gap already detected by agent.
 *
 * @param {string} problemId - Problem ID
 * @param {Object} options - Optional gap info from agent
 * @param {string} [options.detected_gap] - Gap concept detected by agent
 * @param {string[]} [options.prerequisite_concepts] - Prerequisite concepts needed
 * @param {string} [options.error_type] - Type of error detected
 * @returns {Promise<Object>} - Remediation response
 */
export async function getRemediation(problemId, options = {}) {
  const headers = await buildHeaders(true)

  const response = await fetch(`${API_BASE}/api/remediation`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      problem_id: problemId,
      detected_gap: options.detected_gap || null,
      prerequisite_concepts: options.prerequisite_concepts || null,
      error_type: options.error_type || null,
    }),
  })

  if (!response.ok) {
    return { has_remediation: false, items: [] }
  }

  return response.json()
}

export default {
  getRecommendations,
  sendChatMessage,
  getProblemHelp,
  getExamCountdown,
  getMustKnowSections,
  getRoadmapState,
  getQuotaStatus,
  createCheckout,
  saveStudentPreferences,
  getRoadmap,
  getRemediation,
}
