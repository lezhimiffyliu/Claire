/**
 * Mobile Upload API - QR code session management and handwriting analysis
 *
 * Connects to FastAPI backend endpoints:
 * - POST /api/mobile/session - Create upload session
 * - GET /api/mobile/session/{id}/result - Poll for analysis result
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

/**
 * Create a mobile upload session for QR code scanning
 * @param {object} params
 * @param {string} params.userId - User ID (can be 'anonymous' for logged out users)
 * @param {string} params.solveSessionId - Current solve session ID
 * @param {string} params.questionId - Problem ID
 * @param {string} params.course - Course code (124, 125, 126)
 * @param {string} params.displayText - Problem text to show on mobile
 * @returns {Promise<{sessionId: string, qrUrl: string, expiresAt: string, status: string}>}
 */
export async function createMobileSession({ userId, solveSessionId, questionId, course, displayText }) {
  const response = await fetch(`${API_BASE}/api/mobile/session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId || 'anonymous',
      solve_session_id: solveSessionId || `solve_${Date.now()}`,
      question_id: questionId,
      course: course,
      display_text: displayText,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Failed to create session: ${response.status}`)
  }

  const data = await response.json()
  return {
    sessionId: data.session_id,
    qrUrl: data.qr_url,
    expiresAt: data.expires_at,
    status: data.status,
  }
}

/**
 * Poll session result (for desktop)
 *
 * Status values:
 * - pending: waiting for mobile to upload
 * - processing: image uploaded, analysis running
 * - completed: analysis done, results available
 * - error: something went wrong
 * - expired: session timed out
 *
 * @param {string} sessionId - Upload session ID
 * @returns {Promise<{
 *   sessionId: string,
 *   status: 'pending' | 'processing' | 'completed' | 'error' | 'expired',
 *   isCorrect?: boolean,
 *   teachingAction?: string,
 *   teachingMessage?: string,
 *   partsSummary?: Array<{label: string, correct: boolean, feedback: string}>,
 *   error?: string
 * }>}
 */
export async function pollSessionResult(sessionId) {
  const response = await fetch(`${API_BASE}/api/mobile/session/${sessionId}/result`)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Session not found')
    }
    if (response.status === 410) {
      return { sessionId, status: 'expired', error: 'Session expired' }
    }
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Failed to get result: ${response.status}`)
  }

  const data = await response.json()
  return {
    sessionId: data.session_id,
    status: data.status,
    isCorrect: data.is_correct,
    teachingAction: data.teaching_action,
    teachingMessage: data.teaching_message,
    partsSummary: data.parts_summary,
    error: data.error,
  }
}

/**
 * Get full session status (more detailed than pollSessionResult)
 * @param {string} sessionId - Upload session ID
 * @returns {Promise<object>}
 */
export async function getSessionStatus(sessionId) {
  const response = await fetch(`${API_BASE}/api/mobile/session/${sessionId}`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Failed to get status: ${response.status}`)
  }

  return response.json()
}

export default {
  createMobileSession,
  pollSessionResult,
  getSessionStatus,
}
