import { createContext, useContext, useState, useCallback } from 'react'

// Claire states
export const CLAIRE_STATE = {
  IDLE: 'idle',
  GUIDING: 'guiding',
  INTERVENING: 'intervening',
}

// Default messages for different contexts
export const CLAIRE_MESSAGES = {
  // Idle state
  idle: "Ready when you are.",

  // Path page (learn tab)
  path: "Stick with me. We'll fix this.",

  // Entering practice/exams view
  exams: "Pick a problem that challenges you.",

  // Entering a specific problem
  problemStart: "Before you calculate, tell me what behavior you expect first.",

  // During problem solving (inline hint at top of problem)
  problemHint: "Before you calculate, tell me what behavior you expect first.",

  // After submission (incorrect)
  afterSubmitIncorrect: "Okay, let's look at where this went off.",

  // After submission (correct)
  afterSubmitCorrect: "Well done. Ready for the next one?",
}

const ClaireContext = createContext(null)

export function ClaireProvider({ children }) {
  const [state, setState] = useState(CLAIRE_STATE.IDLE)
  const [message, setMessage] = useState(CLAIRE_MESSAGES.idle)
  const [isVisible, setIsVisible] = useState(true)

  const setClaire = useCallback((newState, newMessage) => {
    setState(newState)
    if (newMessage) {
      setMessage(newMessage)
    }
  }, [])

  const setClaireMessage = useCallback((newMessage) => {
    setMessage(newMessage)
  }, [])

  const showClaire = useCallback(() => setIsVisible(true), [])
  const hideClaire = useCallback(() => setIsVisible(false), [])

  const value = {
    state,
    message,
    isVisible,
    setClaire,
    setClaireMessage,
    showClaire,
    hideClaire,
    // Convenience methods
    setIdle: () => setClaire(CLAIRE_STATE.IDLE, CLAIRE_MESSAGES.idle),
    setGuiding: (msg) => setClaire(CLAIRE_STATE.GUIDING, msg || CLAIRE_MESSAGES.path),
    setIntervening: (msg) => setClaire(CLAIRE_STATE.INTERVENING, msg),
  }

  return (
    <ClaireContext.Provider value={value}>
      {children}
    </ClaireContext.Provider>
  )
}

export function useClaire() {
  const context = useContext(ClaireContext)
  if (!context) {
    throw new Error('useClaire must be used within a ClaireProvider')
  }
  return context
}
