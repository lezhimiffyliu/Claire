/**
 * useClaireAgent - Hook for managing Claire agent conversation
 *
 * SESSION LIFECYCLE (explicit navigation semantics):
 *
 * HYDRATE (restore previous state):
 *   - Browser minimize/restore
 *   - Page refresh (F5)
 *   - HMR during development
 *   - React remount (StrictMode, etc.)
 *   → Active instance marker EXISTS in sessionStorage
 *   → User did NOT call markSessionEnded()
 *
 * FRESH (start clean):
 *   - User clicks back button → markSessionEnded('back_button')
 *   - User completes problem → markSessionEnded('marked_complete')
 *   - User opens new tab (sessionStorage is per-tab)
 *   → Active instance marker does NOT exist
 *   → User explicitly ended the practice flow
 *
 * SAFETY FALLBACK:
 *   - If timestamp > 5 minutes old → FRESH (crash recovery edge case)
 *
 * Key principle: Time-based logic is only for safety, not primary control.
 * The primary signal is whether markSessionEnded() was called.
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { tutorRespond, getThread, saveThread } from '../api/chatApi'

// ============================================================
// Constants
// ============================================================

const SESSION_PREFIX = 'claire_session_'
const ACTIVE_INSTANCE_KEY = 'claire_active_instance'
const SESSION_EXPIRY_MS = 4 * 60 * 60 * 1000 // 4 hours
const STALE_SAFETY_MS = 5 * 60 * 1000 // 5 minutes - safety fallback for crash recovery edge cases

// ============================================================
// Session Storage (localStorage - for thread persistence)
// ============================================================

function getSessionKey(problemId) {
  return `${SESSION_PREFIX}${problemId}`
}

function loadSession(problemId) {
  if (!problemId) return null
  try {
    const raw = localStorage.getItem(getSessionKey(problemId))
    if (!raw) return null
    const session = JSON.parse(raw)
    if (Date.now() - session.last_active_at > SESSION_EXPIRY_MS) {
      localStorage.removeItem(getSessionKey(problemId))
      return null
    }
    return session
  } catch (e) {
    console.warn('[useClaireAgent] Failed to load session:', e)
    return null
  }
}

function saveSession(session) {
  if (!session?.problem_id) return
  try {
    session.last_active_at = Date.now()
    localStorage.setItem(getSessionKey(session.problem_id), JSON.stringify(session))
  } catch (e) {
    console.warn('[useClaireAgent] Failed to save session:', e)
  }
}

function clearSession(problemId, reason) {
  if (!problemId) return
  console.log(`[useClaireAgent] CLEAR session for ${problemId} | reason: ${reason}`)
  localStorage.removeItem(getSessionKey(problemId))
}

function createSession(problemId, instanceId) {
  return {
    session_id: `session_${problemId}_${Date.now()}`,
    problem_id: problemId,
    instance_id: instanceId,
    has_initialized: false,
    conversation_history: [],
    last_active_at: Date.now()
  }
}

// ============================================================
// Active Instance Tracking (sessionStorage - survives refresh, not tab close)
// ============================================================

function getActiveInstance() {
  try {
    const raw = sessionStorage.getItem(ACTIVE_INSTANCE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function setActiveInstance(problemId, instanceId) {
  try {
    sessionStorage.setItem(ACTIVE_INSTANCE_KEY, JSON.stringify({
      problemId,
      instanceId,
      timestamp: Date.now()
    }))
    console.log(`[useClaireAgent] SET active instance: ${problemId}/${instanceId}`)
  } catch (e) {
    console.warn('[useClaireAgent] Failed to set active instance:', e)
  }
}

function clearActiveInstance(reason) {
  console.log(`[useClaireAgent] CLEAR active instance | reason: ${reason}`)
  sessionStorage.removeItem(ACTIVE_INSTANCE_KEY)
}

/**
 * Determine if we should hydrate (restore) or start fresh
 *
 * PRIMARY LOGIC (explicit navigation semantics):
 * - If active instance marker exists for this problem → HYDRATE
 *   (markSessionEnded was NOT called, user didn't explicitly leave)
 * - If no active instance marker → FRESH
 *   (markSessionEnded was called, or new tab/context)
 *
 * SAFETY FALLBACK (for crash recovery edge cases):
 * - If timestamp is extremely old (> 5 min) → FRESH
 *   (probably stale from browser crash/restore)
 *
 * @returns {{ shouldHydrate: boolean, reason: string }}
 */
function shouldHydrateSession(problemId) {
  const active = getActiveInstance()

  // No active instance marker → user explicitly ended session (markSessionEnded called)
  // or this is a completely new context (new tab, cleared storage)
  if (!active) {
    return { shouldHydrate: false, reason: 'no_active_instance (session ended or new context)' }
  }

  // Different problem → definitely fresh start
  if (active.problemId !== problemId) {
    return { shouldHydrate: false, reason: `different_problem (active=${active.problemId}, requested=${problemId})` }
  }

  // Same problem, active instance exists → user did NOT explicitly leave
  // This covers: minimize/restore, HMR, visibility change, React remount

  // Safety fallback: check if timestamp is extremely stale (crash recovery edge case)
  const timeSinceActive = Date.now() - active.timestamp
  if (timeSinceActive > STALE_SAFETY_MS) {
    return {
      shouldHydrate: false,
      reason: `stale_safety_fallback (${Math.round(timeSinceActive / 1000)}s old, likely crash recovery)`
    }
  }

  // Active instance exists, not stale → HYDRATE
  return {
    shouldHydrate: true,
    reason: `active_instance_exists (user did not explicitly leave, ${Math.round(timeSinceActive / 1000)}s ago)`
  }
}

// ============================================================
// Thread Event Conversion
// ============================================================

// Extract human-readable text from any stored event content, so prior Claire
// turns survive into the recent-thread context we send back to the backend.
// (teaching_card/teaching_action keep their text in concept_bridge/next_micro_step,
// NOT in `.text` — missing this made multi-turn memory look blank to the agent.)
function extractEventText(content) {
  if (typeof content === 'string') return content
  if (!content) return ''
  if (content.event === 'teaching_card' || content.event === 'teaching_action') {
    return [content.concept_bridge, content.next_micro_step].filter(Boolean).join(' ')
  }
  if (content.event === 'ask_back') return content.question || ''
  if (content.event === 'concept_card') return content.card?.one_liner || ''
  return content.text || content.question || content.next_micro_step || ''
}

function toThreadEvent(evt) {
  if (evt.event === 'say') {
    return { role: 'claire', text: evt.text, tone: evt.tone }
  }
  if (evt.event === 'ask_back') {
    return { role: 'claire', text: evt.question, quickReplies: evt.hints || [] }
  }
  if (evt.event === 'concept_card') {
    return { role: 'claire', text: evt.card?.one_liner || '', conceptCard: evt.card }
  }
  // Unified teaching_card event (new format from pipeline)
  if (evt.event === 'teaching_card') {
    return {
      role: 'claire',
      type: 'teaching_action',
      conceptBridge: evt.concept_bridge,
      nextMicroStep: evt.next_micro_step,
      quickReplies: evt.quick_replies || [],
    }
  }
  // Legacy teaching_action event (for backwards compatibility)
  if (evt.event === 'teaching_action') {
    return {
      role: 'claire',
      type: 'teaching_action',
      conceptBridge: evt.concept_bridge,
      nextMicroStep: evt.next_micro_step,
      quickReplies: evt.quick_replies || [],
    }
  }
  return { role: 'claire', text: typeof evt === 'string' ? evt : JSON.stringify(evt) }
}

// ============================================================
// Exported helper for synchronous hydration check (use before component renders)
// ============================================================

export function willHydrateClaire(problemId) {
  if (!problemId) return { willHydrate: false, threadLength: 0 }

  const { shouldHydrate } = shouldHydrateSession(problemId)
  if (!shouldHydrate) return { willHydrate: false, threadLength: 0 }

  const session = loadSession(problemId)
  if (session?.has_initialized && session.conversation_history?.length > 0) {
    return { willHydrate: true, threadLength: session.conversation_history.length }
  }

  return { willHydrate: false, threadLength: 0 }
}

// ============================================================
// Hook
// ============================================================

export function useClaireAgent({ sessionId, problemContext, userId, instanceId }) {
  const problemId = sessionId || problemContext?.id

  // ============================================================
  // SYNCHRONOUS LOCAL HYDRATION (runs on first render, no flicker)
  // ============================================================
  const initializedForRef = useRef(null)

  // Compute initial state synchronously from localStorage
  const computeInitialState = () => {
    const start = performance.now()

    if (!problemId || !instanceId) {
      return { thread: [], session: null, isHydrated: false }
    }

    const { shouldHydrate, reason } = shouldHydrateSession(problemId)
    console.log(`[useClaireAgent] SYNC hydrate check | shouldHydrate=${shouldHydrate} | ${reason}`)

    if (shouldHydrate) {
      const session = loadSession(problemId)
      if (session?.has_initialized && session.conversation_history?.length > 0) {
        const thread = session.conversation_history
          .filter(msg => msg.content)
          .map(msg => msg.role === 'user'
            ? { role: 'user', text: msg.content }
            : toThreadEvent(msg.content)
          )

        // Update instance ID in session
        session.instance_id = instanceId

        const elapsed = Math.round(performance.now() - start)
        console.log(`[useClaireAgent] SYNC local hydrate took ${elapsed}ms | ${thread.length} events`)

        // Set active instance marker
        setActiveInstance(problemId, instanceId)
        initializedForRef.current = problemId

        return { thread, session, isHydrated: true }
      }
    }

    // Fresh start
    console.log(`[useClaireAgent] SYNC fresh start for ${problemId}`)
    const newSession = createSession(problemId, instanceId)
    saveSession(newSession)
    setActiveInstance(problemId, instanceId)
    initializedForRef.current = problemId

    return { thread: [], session: newSession, isHydrated: false }
  }

  // Use lazy initializers so first render already has correct state
  const [initialState] = useState(computeInitialState)
  const [thread, setThread] = useState(initialState.thread)
  const [isHydrated, setIsHydrated] = useState(initialState.isHydrated)
  const sessionRef = useRef(initialState.session)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Debug info from backend tutor pipeline
  const [lastIntent, setLastIntent] = useState(null)
  const [lastConcept, setLastConcept] = useState(null)
  const [lastModelUsed, setLastModelUsed] = useState(null)
  const [lastResponseCacheHit, setLastResponseCacheHit] = useState(false)
  const [lastRetrievalCacheHit, setLastRetrievalCacheHit] = useState(false)
  const [lastRetrievalScore, setLastRetrievalScore] = useState(0)

  const userIdRef = useRef(userId)
  useEffect(() => { userIdRef.current = userId }, [userId])

  const problemContextRef = useRef(problemContext)
  useEffect(() => { problemContextRef.current = problemContext }, [problemContext])

  // ============================================================
  // Handle problemId changes (re-init if different problem)
  // ============================================================
  useEffect(() => {
    if (!problemId || !instanceId) return
    if (initializedForRef.current === problemId) return // Already initialized for this problem

    console.log(`[useClaireAgent] problemId changed from ${initializedForRef.current} to ${problemId}, re-initializing`)

    const { shouldHydrate, reason } = shouldHydrateSession(problemId)
    console.log(`[useClaireAgent] Re-init hydrate decision: ${shouldHydrate} | ${reason}`)

    if (shouldHydrate) {
      const session = loadSession(problemId)
      if (session?.has_initialized && session.conversation_history?.length > 0) {
        const restoredThread = session.conversation_history
          .filter(msg => msg.content)
          .map(msg => msg.role === 'user'
            ? { role: 'user', text: msg.content }
            : toThreadEvent(msg.content)
          )

        session.instance_id = instanceId
        sessionRef.current = session
        setThread(restoredThread)
        setIsHydrated(true)
        setActiveInstance(problemId, instanceId)
        initializedForRef.current = problemId
        return
      }
    }

    // Fresh start
    const newSession = createSession(problemId, instanceId)
    sessionRef.current = newSession
    saveSession(newSession)
    setActiveInstance(problemId, instanceId)
    setThread([])
    setIsHydrated(false)
    initializedForRef.current = problemId
  }, [problemId, instanceId])

  // ============================================================
  // Background backend sync (does NOT block UI)
  // ============================================================
  useEffect(() => {
    if (!problemId || !userId) return

    const syncWithBackend = async () => {
      const start = performance.now()
      console.log(`[useClaireAgent] Backend sync started for ${problemId}`)

      try {
        // This is background sync only - UI is already showing local state
        // We could fetch from backend and merge if needed
        // For now, just log that sync would happen here
        const elapsed = Math.round(performance.now() - start)
        console.log(`[useClaireAgent] Backend sync completed in ${elapsed}ms (no-op for now)`)
      } catch (e) {
        console.warn('[useClaireAgent] Backend sync failed:', e)
      }
    }

    // Run in background, don't block
    syncWithBackend()
  }, [problemId, userId])

  // Update active instance timestamp periodically (keeps session "warm")
  useEffect(() => {
    if (!problemId || !instanceId) return

    const interval = setInterval(() => {
      setActiveInstance(problemId, instanceId)
    }, 10000) // Every 10 seconds

    return () => clearInterval(interval)
  }, [problemId, instanceId])

  // ============================================================
  // Send Message (all logic delegated to backend)
  // ============================================================
  const sendMessage = useCallback(async (text, options = {}) => {
    const { actionType, partId, stepIndex } = options

    if (!problemId) {
      console.warn('[useClaireAgent] No problemId provided')
      return []
    }

    if (!sessionRef.current) {
      sessionRef.current = createSession(problemId, instanceId)
    }
    const session = sessionRef.current

    // Record user message
    session.conversation_history.push({
      role: 'user',
      content: text,
      timestamp: Date.now()
    })

    setLoading(true)
    setError(null)

    try {
      const recentThread = session.conversation_history
        .slice(-8)
        .map(msg => ({
          role: msg.role,
          text: msg.role === 'user' ? (msg.content || '') : extractEventText(msg.content),
        }))
        .filter(m => m.text && m.text.trim())

      console.log('[useClaireAgent] Calling /api/tutor/respond', actionType ? `(actionType=${actionType}, step=${stepIndex})` : '')
      const result = await tutorRespond({
        message: text,
        sessionId: session.session_id,
        problemContext: problemContextRef.current,
        recentThread,
        userId: userIdRef.current,
        actionType,
        partId: partId || problemContextRef.current?.current_part_index?.toString(),
        stepIndex: stepIndex ?? problemContextRef.current?.step_index ?? 0,
      })

      const events = result.events || []

      setLastIntent(result.intent)
      setLastConcept(result.concept)
      setLastModelUsed(result.model_used)
      setLastResponseCacheHit(result.response_cache_hit)
      setLastRetrievalCacheHit(result.retrieval_cache_hit)
      setLastRetrievalScore(result.retrieval_score)

      console.log('[useClaireAgent] Response:',
        'intent=', result.intent,
        '| model=', result.model_used)

      for (const evt of events) {
        session.conversation_history.push({
          role: 'assistant',
          content: evt,
          timestamp: Date.now()
        })
      }

      if (!session.has_initialized) {
        session.has_initialized = true
      }

      saveSession(session)

      // Persist to backend if logged in (async)
      if (userIdRef.current) {
        const threadEventsForBackend = session.conversation_history
          .filter(msg => msg.content)
          .map(msg => msg.role === 'user'
            ? { role: 'user', text: msg.content }
            : { role: 'claire', ...msg.content }
          )

        saveThread({
          userId: userIdRef.current,
          problemId: session.problem_id,
          sessionId: session.session_id,
          events: threadEventsForBackend,
          warmCache: {},
          initializedOnce: true
        }).catch(e => console.warn('[useClaireAgent] Backend save failed:', e))
      }

      const newThreadEvents = events.map(toThreadEvent)
      setThread(prev => [...prev, ...newThreadEvents])

      setLoading(false)
      return newThreadEvents

    } catch (err) {
      console.error('[useClaireAgent] Error:', err)
      setError(err.message)
      setLoading(false)
      return []
    }
  }, [problemId, instanceId])

  // ============================================================
  // Teaching Action (Task-based, not chat-based)
  // DEPRECATED: Now unified into sendMessage with actionType option
  // Use: sendMessage('', { actionType: 'student_stuck', partId: '0', stepIndex: 0 })
  // ============================================================
  const executeTeachingAction = useCallback(async (intent, currentPartIndex = 0, studentMessage = null) => {
    // Delegate to sendMessage with actionType
    console.log('[useClaireAgent] executeTeachingAction called, delegating to sendMessage with actionType')
    return sendMessage(studentMessage || '', {
      actionType: intent,
      partId: currentPartIndex.toString(),
      stepIndex: 0,
    })
  }, [sendMessage])

  // ============================================================
  // Thread Helpers
  // ============================================================

  const appendUserMessage = useCallback((text) => {
    setThread(prev => [...prev, { role: 'user', text }])
    if (sessionRef.current) {
      sessionRef.current.conversation_history.push({
        role: 'user',
        content: text,
        timestamp: Date.now()
      })
      saveSession(sessionRef.current)
    }
  }, [])

  const appendUserImage = useCallback((imageUrl) => {
    setThread(prev => [...prev, { role: 'user', imageUrl }])
  }, [])

  const appendClaireMessage = useCallback((text, options = {}) => {
    setThread(prev => [...prev, { role: 'claire', text, ...options }])
    if (sessionRef.current) {
      sessionRef.current.conversation_history.push({
        role: 'assistant',
        content: { event: 'say', text, tone: 'neutral' },
        timestamp: Date.now()
      })
      saveSession(sessionRef.current)
    }
  }, [])

  /**
   * Reset the session - MUST include a reason
   */
  const reset = useCallback((reason) => {
    if (!reason) {
      console.error('[useClaireAgent] reset() called without reason - this is a bug!')
      console.trace()
      reason = 'UNKNOWN (missing reason)'
    }

    console.log(`[useClaireAgent] RESET | reason: ${reason}`)

    setThread([])
    setLoading(false)
    setError(null)
    setIsHydrated(false)
    setLastIntent(null)
    setLastConcept(null)
    setLastModelUsed(null)
    setLastResponseCacheHit(false)
    setLastRetrievalCacheHit(false)
    setLastRetrievalScore(0)

    if (problemId) {
      clearSession(problemId, reason)
    }
    sessionRef.current = null
    initializedForRef.current = null
  }, [problemId])

  /**
   * Clear the active instance marker (call when user intentionally navigates away)
   */
  const markSessionEnded = useCallback((reason) => {
    console.log(`[useClaireAgent] markSessionEnded | reason: ${reason}`)
    clearActiveInstance(reason)
  }, [])

  // ============================================================
  // Debug / Session Info
  // ============================================================
  const getSessionInfo = useCallback(() => {
    if (!sessionRef.current) return null
    return {
      session_id: sessionRef.current.session_id,
      problem_id: sessionRef.current.problem_id,
      instance_id: sessionRef.current.instance_id,
      has_initialized: sessionRef.current.has_initialized,
      history_length: sessionRef.current.conversation_history.length,
      last_active: new Date(sessionRef.current.last_active_at).toISOString(),
      is_hydrated: isHydrated,
      last_intent: lastIntent,
      last_concept: lastConcept,
      last_model_used: lastModelUsed,
    }
  }, [isHydrated, lastIntent, lastConcept, lastModelUsed])

  return {
    thread,
    loading,
    error,
    isHydrated,
    sendMessage,
    executeTeachingAction,
    appendUserMessage,
    appendUserImage,
    appendClaireMessage,
    reset,
    markSessionEnded,
    getSessionInfo,
    // Debug info
    lastIntent,
    lastConcept,
    lastModelUsed,
    lastResponseCacheHit,
    lastRetrievalCacheHit,
    lastRetrievalScore,
  }
}

export default useClaireAgent
