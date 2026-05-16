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

export default {
  sendMessage,
  getProblemHelp,
}
