/**
 * attemptApi — the two /api/attempt paths, kept strictly separate:
 *
 *   1. GRADE a full answer:   submitAttempt()   → POST /api/attempt
 *        → run_tutor_turn(): the SymPy verifier decides correctness. Structured
 *          response (grade_status / action / hint_level / misconception / phase).
 *
 *   2. CONTINUE a teaching episode: continueTeaching() → POST /api/attempt/continue
 *        → run_teaching_turn(): a follow-up reply within the SAME problem's
 *          teaching state. It does NOT grade the final answer — if the student
 *          pastes a complete answer, the response sets `redirect_to_submit` and
 *          the caller must route them back through submitAttempt().
 *
 * The frontend NEVER string-matches prose, grades locally, or sends the official
 * answer. Correctness is only ever decided by path (1).
 */
import { getAuthToken } from './authToken'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function authHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  const token = await getAuthToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function throwForResponse(response, fallback) {
  let detail = null
  try {
    detail = (await response.json()).detail
  } catch {
    // non-JSON error body
  }
  const err = new Error((detail && detail.message) || `${fallback}: ${response.status}`)
  err.status = response.status
  err.detail = detail
  throw err
}

/**
 * Grade one typed answer and advance the adaptive teaching loop.
 *
 * @returns {Promise<{
 *   is_correct: boolean, is_uncertain: boolean, grade_status: string,
 *   action: string, hint_level: string, misconception: string|null,
 *   message: string, phase: string, attempt_id: string|null,
 *   recommendations: Array, persisted: boolean
 * }>}
 */
export async function submitAttempt({
  problemId,
  answer,
  course,
  partLabel = null,
  attemptSessionId = null,
  source = 'practice',
}) {
  const response = await fetch(`${API_BASE}/api/attempt`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify({
      problem_id: problemId,
      answer,
      course,
      part_label: partLabel,
      attempt_session_id: attemptSessionId,
      source,
    }),
  })

  if (!response.ok) await throwForResponse(response, 'Attempt failed')
  return response.json()
}

/**
 * Continue a teaching episode: send the student's follow-up reply within the
 * current problem's teaching state. Does NOT grade the final answer.
 *
 * @returns {Promise<{
 *   action: string, message: string, hint_level: string, phase: string,
 *   ended: boolean, redirect_to_submit: boolean, tool_used: string|null,
 *   persisted: boolean
 * }>}
 */
export async function continueTeaching({
  problemId,
  message,
  course,
  partLabel = null,
  attemptSessionId = null,
}) {
  const response = await fetch(`${API_BASE}/api/attempt/continue`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify({
      problem_id: problemId,
      message,
      course,
      part_label: partLabel,
      attempt_session_id: attemptSessionId,
    }),
  })

  if (!response.ok) await throwForResponse(response, 'Teaching reply failed')
  return response.json()
}
