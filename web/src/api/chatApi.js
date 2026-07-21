/**
 * Chat API - 调用 Claire agent
 */

const API_BASE = 'http://localhost:8000'

/**
 * 发送消息给 Claire
 */
export async function sendMessage(message, options = {}) {
  const { level = 'beginner', guidedMode = true } = options

  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      level,
      guided_mode: guidedMode,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Chat failed: ${response.status}`)
  }

  return response.json()
}

/**
 * 获取题目讲解
 */
export async function getProblemHelp(problem, partIndex = null) {
  let message = `Help me understand this problem:\n\n`

  if (problem.stem) {
    message += `${problem.stem}\n\n`
  }

  if (problem.parts && problem.parts.length > 0) {
    if (partIndex !== null && problem.parts[partIndex]) {
      const part = problem.parts[partIndex]
      message += `Part ${part.label || partIndex + 1}: ${part.question_text}`
    } else {
      // First part
      const part = problem.parts[0]
      message += `Part ${part.label || 'a'}: ${part.question_text}`
    }
  }

  message += `\n\nPlease guide me through solving this step by step.`

  return sendMessage(message)
}

/**
 * Run Claire agent with structured teaching actions
 * Returns events: say, ask_back, concept_card
 *
 * Phase 5 additions:
 * - intent: detected user intent
 * - model_used: which model tier was used (basic=Sonnet, premium=Opus)
 */
export async function runClaireAgent({ message, sessionId, problemContext, userId }) {
  const response = await fetch(`${API_BASE}/api/claire/agent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      problem_context: problemContext,
      user_id: userId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Claire agent failed: ${response.status}`)
  }

  return response.json() // { events, turns, intent, model_used }
}

/**
 * Phase 4: Get existing thread from backend
 * Returns: { exists, initialized_once, events, warm_cache, session_id }
 */
export async function getThread({ userId, problemId }) {
  const response = await fetch(`${API_BASE}/api/claire/thread/get`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      problem_id: problemId,
    }),
  })

  if (!response.ok) {
    console.warn('[chatApi] getThread failed:', response.status)
    return { exists: false }
  }

  return response.json()
}

/**
 * Phase 4: Save thread to backend
 */
export async function saveThread({ userId, problemId, sessionId, events, warmCache, initializedOnce }) {
  const response = await fetch(`${API_BASE}/api/claire/thread/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      problem_id: problemId,
      session_id: sessionId,
      events,
      warm_cache: warmCache,
      initialized_once: initializedOnce,
    }),
  })

  if (!response.ok) {
    console.warn('[chatApi] saveThread failed:', response.status)
    return { status: 'error' }
  }

  return response.json()
}

/**
 * Tutor Pipeline: Semantic retrieval-based response generation
 *
 * Args:
 * - message: Student message text
 * - sessionId: Session identifier
 * - problemContext: Current problem info
 * - recentThread: Recent conversation history
 * - userId: User identifier
 * - actionType: Explicit intent from button (e.g., "cant_start", "how_to_start")
 *               If provided, skips Haiku classification for cache key
 * - partId: Current part identifier for cache key
 * - stepIndex: Current step within part (0=start, 1=after first hint, etc.)
 *              Differentiates solving stages to avoid stale cache hits
 *
 * Returns:
 * - events: Claire teaching events
 * - intent: classified user intent
 * - concept: identified math concept
 * - model_used: which model was used (response_cache/haiku/sonnet/opus)
 * - response_cache_hit: true if returned from response cache (no LLM calls)
 * - retrieval_cache_hit: true if high retrieval score (chunks reused)
 * - retrieval_score: similarity score for retrieved chunks
 * - strategy_decision: why this model was chosen
 * - chunks_used: IDs of teaching chunks used
 */
export async function tutorRespond({ message, sessionId, problemContext, recentThread, userId, actionType, partId, stepIndex }) {
  const response = await fetch(`${API_BASE}/api/tutor/respond`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      problem_context: problemContext,
      recent_thread: recentThread,
      user_id: userId,
      action_type: actionType,
      part_id: partId,
      step_index: stepIndex,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail?.message || `Tutor failed: ${response.status}`)
  }

  return response.json()
}

// Teaching Action: DEPRECATED
// Now unified into tutorRespond() with actionType parameter
// Use tutorRespond({ actionType: 'student_stuck', ... }) instead

export default {
  sendMessage,
  getProblemHelp,
  runClaireAgent,
  tutorRespond,
  getThread,
  saveThread,
}
