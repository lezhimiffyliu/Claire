/**
 * Anonymous Learning State Management
 *
 * Simple module to save/load anonymous user's onboarding selections.
 * Used to ensure anonymous users see their selected course (not default math126).
 */

const STORAGE_KEY = 'claire_anonymous_learning_state'

/**
 * Save anonymous learning state after onboarding.
 * Called in App.jsx when user completes onboarding without logging in.
 */
export function saveAnonymousLearningState({ selections, testState }) {
  const state = {
    course: selections?.course || 'math126',
    selections,
    testState,
    savedAt: new Date().toISOString(),
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    console.log('[AnonymousState] Saved:', { course: state.course })
  } catch (e) {
    console.error('[AnonymousState] Failed to save:', e)
  }
}

/**
 * Load anonymous learning state.
 */
export function loadAnonymousLearningState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

/**
 * Get course from anonymous state, with legacy fallback.
 */
export function getAnonymousCourse() {
  // Try new format
  const state = loadAnonymousLearningState()
  if (state?.course) return state.course

  // Fallback to legacy claire_selections
  try {
    const selections = JSON.parse(localStorage.getItem('claire_selections') || '{}')
    return selections.course || null
  } catch {
    return null
  }
}
