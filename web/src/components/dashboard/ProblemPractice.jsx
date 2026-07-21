import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { useClaire, CLAIRE_MESSAGES, CLAIRE_STATE } from '../../context/ClaireContext'
import { createSolveSession, updateSolveSession } from '../../api/supabaseApi'
import { getProblemHelp, sendMessage } from '../../api/chatApi'
import { createMobileSession, pollSessionResult } from '../../api/mobileUploadApi'
import { useClaireAgent, willHydrateClaire } from '../../hooks/useClaireAgent'
import PartTutorPanel from '../claire/PartTutorPanel'
import ClaireL0Strip from '../claire/ClaireL0Strip'
import ClaireCorner from '../claire/ClaireCorner'
import WorkAreaCard from '../claire/WorkAreaCard'
import MathText from '../ui/MathText'
import MathInput from '../ui/MathInput'

// Tutor intervention levels - represents Claire's engagement intensity, NOT UI state
const TutorLevel = {
  L0_AMBIENT: 'L0_AMBIENT',           // Quiet observation, student working independently
  L1_LIGHT_INTERVENTION: 'L1_LIGHT_INTERVENTION',  // Small inline nudge (future)
  L2_TEACHING: 'L2_TEACHING',         // Deep teaching mode, Socratic dialogue
}

// Claire ambient strip - the quiet "always-on teacher" observation (L0).
// Conversation now lives in the bottom-right ClaireCorner bubble (L1), so this
// strip only surfaces the pre-authored ambient observation for the problem.
function ClaireResponseStrip({ l0Dismissed, problem, currentPart, onDismissL0 }) {
  if (l0Dismissed) return null

  return (
    <ClaireL0Strip
      problem={problem}
      currentPart={currentPart}
      onDismiss={onDismissL0}
    />
  )
}

// Format exam name for display
function formatExamName(examId) {
  if (!examId) return ''
  const parts = examId.split('_')
  const seasonCode = parts[0]?.slice(0, 2) || ''
  const year = parts[0]?.slice(2, 4) || ''
  const seasonMap = { au: 'Autumn', wi: 'Winter', sp: 'Spring' }
  const season = seasonMap[seasonCode] || seasonCode
  return `${season} 20${year}`
}

// Generate QR code URL
function getQRCodeUrl(data, size = 200) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

// QR Upload Modal Component
function QRUploadModal({ isOpen, onClose, qrUrl, sessionStatus, onRetry }) {
  if (!isOpen) return null

  const statusConfig = {
    pending: {
      icon: '📱',
      title: 'Waiting for your phone...',
      subtitle: 'Scan the QR code to open the upload page',
      color: 'text-[var(--claire-navy)]',
      bgColor: 'bg-[var(--claire-next-bg)]',
    },
    processing: {
      icon: '🔍',
      title: 'Claire is reading your work...',
      subtitle: 'Analyzing your handwritten solution',
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    completed: {
      icon: '✓',
      title: 'Analysis complete',
      subtitle: 'Check Claire\'s feedback below',
      color: 'text-[var(--claire-teal)]',
      bgColor: 'bg-[var(--claire-teal-muted)]',
    },
    error: {
      icon: '!',
      title: 'Something went wrong',
      subtitle: sessionStatus?.error || 'Please try again',
      color: 'text-[var(--claire-weak)]',
      bgColor: 'bg-[var(--claire-weak-bg)]',
    },
    expired: {
      icon: '⏱',
      title: 'Session expired',
      subtitle: 'Generate a new QR code to continue',
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
    },
  }

  const status = sessionStatus?.status || 'pending'
  const config = statusConfig[status] || statusConfig.pending

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden"
      >
        {/* Header */}
        <div className="bg-[var(--claire-navy)] text-white px-5 py-4 flex items-center justify-between">
          <h3 className="font-bold">Scan to Submit</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-full transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-5">
          {/* QR Code */}
          {status === 'pending' && qrUrl && (
            <div className="flex flex-col items-center mb-5">
              <div className="bg-white p-3 rounded-xl border-2 border-gray-100 shadow-sm">
                <img
                  src={getQRCodeUrl(qrUrl, 180)}
                  alt="Scan to upload"
                  className="w-[180px] h-[180px]"
                />
              </div>
              <p className="text-sm text-gray-500 mt-4 text-center">
                Point your phone camera at the QR code
              </p>
              <p className="text-xs text-gray-400 mt-1 text-center">
                You can upload multiple photos of your work
              </p>
            </div>
          )}

          {/* Status indicator */}
          <div className={`p-4 rounded-xl ${config.bgColor}`}>
            <div className="flex items-center gap-3">
              <span className="text-xl">{config.icon}</span>
              <div>
                <p className={`font-semibold ${config.color}`}>{config.title}</p>
                <p className="text-sm text-gray-600">{config.subtitle}</p>
              </div>
            </div>

            {status === 'processing' && (
              <div className="mt-3 flex justify-center">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 bg-amber-500 rounded-full"
                      animate={{ y: [0, -6, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mt-4">
            {(status === 'error' || status === 'expired') && (
              <button
                onClick={onRetry}
                className="w-full py-3 bg-[var(--claire-navy)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
              >
                Generate New QR Code
              </button>
            )}
            {status === 'completed' && (
              <button
                onClick={onClose}
                className="w-full py-3 bg-[var(--claire-teal)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
              >
                View Feedback
              </button>
            )}
            {(status === 'pending' || status === 'processing') && (
              <button
                onClick={onClose}
                className="w-full py-2.5 text-gray-500 font-medium hover:text-gray-700 transition-colors"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}

// Claire Feedback Component
function ClaireFeedback({ result, onContinue, onTryAgain }) {
  if (!result) return null

  const isCorrect = result.isCorrect
  const message = result.teachingMessage

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-6 rounded-xl border-l-4 ${
        isCorrect
          ? 'bg-[var(--claire-teal-muted)] border-[var(--claire-teal)]'
          : 'bg-amber-50 border-amber-400'
      }`}
    >
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isCorrect ? 'bg-[var(--claire-teal)] text-white' : 'bg-amber-400 text-white'
        }`}>
          {isCorrect ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6v6m0 4h.01" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          <h4 className={`font-bold text-lg ${isCorrect ? 'text-[var(--claire-teal)]' : 'text-amber-700'}`}>
            {isCorrect ? 'Correct!' : 'Let\'s review this'}
          </h4>

          <div className="mt-3 text-gray-700 leading-relaxed whitespace-pre-wrap">
            {message}
          </div>

          {result.partsSummary && result.partsSummary.length > 0 && (
            <div className="mt-4 space-y-2">
              {result.partsSummary.map((part, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-2 p-2 rounded-lg text-sm ${
                    part.correct ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  <span className="font-bold">{part.correct ? '✓' : '✗'}</span>
                  <span>Part ({part.label || String.fromCharCode(97 + i)})</span>
                  {part.feedback && <span className="text-gray-600">— {part.feedback}</span>}
                </div>
              ))}
            </div>
          )}

          <div className="mt-5 flex gap-3">
            {isCorrect ? (
              <button
                onClick={onContinue}
                className="px-5 py-2.5 bg-[var(--claire-teal)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
              >
                Continue to next part
              </button>
            ) : (
              <button
                onClick={onTryAgain}
                className="px-5 py-2.5 bg-[var(--claire-navy)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
              >
                Try again
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Step Progress Dot Component
function StepDot({ label, status, onClick }) {
  const baseClasses = "flex items-center justify-center rounded-full font-bold text-xs transition-all w-8 h-8"
  const interactiveClasses = onClick ? "cursor-pointer hover:ring-4 hover:ring-[var(--claire-next-bg)] hover:scale-105" : ""

  const statusClasses = {
    completed: "bg-[var(--claire-teal)] text-white",
    current: "bg-[var(--claire-navy)] text-white ring-4 ring-[var(--claire-next-bg)]",
    upcoming: "bg-gray-100 text-gray-400 border-2 border-gray-200",
    locked: "bg-gray-50 text-gray-300 border border-gray-100",
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Go to part ${label}`}
      aria-current={status === 'current' ? 'step' : undefined}
      className={`${baseClasses} ${interactiveClasses} ${statusClasses[status]}`}
    >
      {status === 'completed' ? (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        label
      )}
    </button>
  )
}

export default function ProblemPractice({ section, problem: directProblem, onBack, isExamMode = false }) {
  const { user } = useAuth()
  const { setClaire } = useClaire()

  // Generate unique instance ID for this practice session (stable across remounts)
  const instanceIdRef = useRef(`practice_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`)
  const instanceId = instanceIdRef.current

  // Track mount/unmount with detailed logging
  useEffect(() => {
    console.log('[ProblemPractice] MOUNT', {
      instanceId,
      problemId: directProblem?.id || section?.section_id,
      timestamp: Date.now()
    })
    return () => {
      console.log('[ProblemPractice] UNMOUNT', {
        instanceId,
        timestamp: Date.now()
      })
    }
  }, [instanceId, directProblem?.id, section?.section_id])

  // Section context with filtered problems (or single direct problem for exam mode)
  const sectionProblems = directProblem ? [directProblem] : (section?.problems || [])
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const problem = sectionProblems[currentProblemIndex] || null

  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [completedSteps, setCompletedSteps] = useState(new Set())
  const [session, setSession] = useState(null)
  const [claireFeedback, setClaireFeedback] = useState(null)

  // QR Upload state
  const [qrModalOpen, setQrModalOpen] = useState(false)
  const [qrSession, setQrSession] = useState(null)
  const [qrStatus, setQrStatus] = useState(null)
  const [qrLoading, setQrLoading] = useState(false)
  const [qrError, setQrError] = useState(null)
  const pollIntervalRef = useRef(null)
  const pollCountRef = useRef(0)
  const MAX_POLLS = 120

  // AI Help state
  const [aiHelp, setAiHelp] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [showHintPanel, setShowHintPanel] = useState(false)

  // Give up / show answer state
  const [showAnswer, setShowAnswer] = useState(false)

  // Manual input state
  const [showManualInput, setShowManualInput] = useState(false)
  const [typedAnswer, setTypedAnswer] = useState({ latex: '', text: '' })
  const [submittingAnswer, setSubmittingAnswer] = useState(false)

  // Tutor level - Claire's intervention intensity (NOT UI state)
  // Default is L0_AMBIENT (quiet observation)
  // Only escalate to L2_TEACHING when student needs deep help
  const [tutorLevel, setTutorLevel] = useState(TutorLevel.L0_AMBIENT)

  // Upload modal state - separate from tutor level (upload is a UI action, not a mode)
  const [isUploadOpen, setIsUploadOpen] = useState(false)

  // L0 observation strip state
  const [l0Dismissed, setL0Dismissed] = useState(false)

  // ClaireCorner (L1): idle-peek opens the bubble once per part ("teacher
  // glances over") and triggers an L1 nudge fetch. nudgeRequestedRef guards
  // against re-fetching the nudge each time the bubble is reopened.
  const [cornerAutoOpen, setCornerAutoOpen] = useState(false)
  const nudgeRequestedRef = useRef(false)

  const parts = problem?.parts || []
  const currentPart = parts[currentStepIndex]
  const totalSteps = parts.length

  // NOTE: Future work — treat one part (e.g. part b) as the "main" question and the
  // others as scaffolding/auxiliary parts. Deferred for now; all parts are shown as
  // equal peers. See docs/TUTOR_LAYERS.md ("Main-part assumption — deferred").

  // Claire agent hook - pass instanceId for session tracking
  const claire = useClaireAgent({
    sessionId: problem?.id,
    problemContext: problem,
    userId: user?.id,
    instanceId
  })

  // RENDER STATE LOGGING - helps debug hydration timing
  console.log('[ProblemPractice] render', {
    tutorLevel,
    isUploadOpen,
    threadLength: claire.thread.length,
    isHydrated: claire.isHydrated,
    loading: claire.loading,
    problemId: problem?.id
  })

  // Track previous step/problem to detect actual changes (not just re-renders)
  const prevStepRef = useRef(currentStepIndex)
  const prevProblemRef = useRef(currentProblemIndex)

  // Thread growth no longer triggers tutorLevel change
  // Student asking questions stays in L0_AMBIENT - Claire responds in the strip
  // Only explicit escalation (repeated errors, deep help request) goes to L2_TEACHING

  // Idle-peek for the ClaireCorner bubble. Opens once ~75s into a part if the
  // student hasn't finished / given up. Reset on part or problem change.
  useEffect(() => {
    setCornerAutoOpen(false)
    nudgeRequestedRef.current = false
    if (showAnswer || claireFeedback) return
    const timer = setTimeout(() => setCornerAutoOpen(true), 75000)
    return () => clearTimeout(timer)
  }, [currentStepIndex, currentProblemIndex, showAnswer, claireFeedback])

  // Create solve_session on mount
  useEffect(() => {
    async function initSession() {
      if (!problem?.id || !user?.id) return
      try {
        const newSession = await createSolveSession(user.id, problem.id, problem)
        setSession(newSession)
      } catch (error) {
        console.error('[ProblemPractice] Failed to create session:', error)
      }
    }
    initSession()
  }, [problem?.id, user?.id])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [])

  // Reset UI state when step changes (within same problem)
  useEffect(() => {
    // Skip if step hasn't actually changed
    if (prevStepRef.current === currentStepIndex) {
      return
    }

    const oldStep = prevStepRef.current
    prevStepRef.current = currentStepIndex

    console.log('[ProblemPractice] Step changed', { from: oldStep, to: currentStepIndex })

    // Reset UI state for new step
    setClaireFeedback(null)
    setShowAnswer(false)
    setAiHelp(null)
    setShowHintPanel(false)
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    setTutorLevel(TutorLevel.L0_AMBIENT)
    setIsUploadOpen(false)
    setQrSession(null)
    setQrStatus(null)
    setQrError(null)
    setL0Dismissed(false)
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)

    // Reset Claire session for new step
    claire.reset('step_changed')
  }, [currentStepIndex, claire])

  // Reset UI state when problem changes (different problem in section)
  useEffect(() => {
    // Skip if problem hasn't actually changed
    if (prevProblemRef.current === currentProblemIndex) {
      return
    }

    const oldProblem = prevProblemRef.current
    prevProblemRef.current = currentProblemIndex

    console.log('[ProblemPractice] Problem changed', { from: oldProblem, to: currentProblemIndex })

    // Reset all state for new problem
    setCurrentStepIndex(0)
    setCompletedSteps(new Set())
    setClaireFeedback(null)
    setShowAnswer(false)
    setAiHelp(null)
    setShowHintPanel(false)
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    setTutorLevel(TutorLevel.L0_AMBIENT)
    setIsUploadOpen(false)
    setQrSession(null)
    setQrStatus(null)
    setQrError(null)
    setL0Dismissed(false)
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)

    // Reset Claire session for new problem
    claire.reset('problem_changed')
  }, [currentProblemIndex, claire])

  // Wrapper for back navigation - marks session as intentionally ended
  const handleBackNavigation = (reason) => {
    console.log('[ProblemPractice] Back navigation', { reason, instanceId })
    claire.markSessionEnded(reason)
    onBack()
  }

  const handleNextProblem = () => {
    if (currentProblemIndex < sectionProblems.length - 1) {
      setCurrentProblemIndex(currentProblemIndex + 1)
    } else {
      // All problems done, go back to dashboard
      handleBackNavigation('all_problems_complete')
    }
  }

  const handlePrevProblem = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(currentProblemIndex - 1)
    }
  }

  // Panel action handler (for upload)
  const handlePanelAction = async (action) => {
    if (action === 'done') {
      setIsUploadOpen(true)
      handleStartQRUpload()
    }
  }

  // Handle message from work area input - stays in L0_AMBIENT, shows response in strip
  const handlePanelMessage = async (text) => {
    claire.appendUserMessage(text)

    // Check if user wants to submit their work
    const submitPatterns = /^(done|finished|i'?m done|check|submit|all done|ready)/i
    if (submitPatterns.test(text.trim())) {
      setIsUploadOpen(true)
      handleStartQRUpload()
      return
    }

    // Send to Claire, stay in L0_AMBIENT - response shows in strip
    claire.sendMessage(text, {
      actionType: 'followup',
      partId: currentStepIndex.toString(),
      stepIndex: claire.thread.length,
    })
  }

  // Update Claire's panel message when feedback is received
  useEffect(() => {
    if (claireFeedback) {
      if (claireFeedback.isCorrect) {
        setClaire(CLAIRE_STATE.GUIDING, CLAIRE_MESSAGES.afterSubmitCorrect)
      } else {
        setClaire(CLAIRE_STATE.INTERVENING, CLAIRE_MESSAGES.afterSubmitIncorrect)
      }
    }
  }, [claireFeedback, setClaire])

  const handleStartQRUpload = async () => {
    setQrLoading(true)
    setQrError(null)
    setQrStatus(null)
    pollCountRef.current = 0

    try {
      const displayParts = []
      if (problem.stem) displayParts.push(problem.stem)
      if (currentPart) {
        const label = currentPart.label || String.fromCharCode(97 + currentStepIndex)
        displayParts.push(`(${label}) ${currentPart.question_text}`)
      }
      const displayText = displayParts.join('\n\n').slice(0, 500)

      if (!user?.id) {
        throw new Error('Please sign in to use QR upload')
      }

      const sessionData = await createMobileSession({
        userId: user.id,
        solveSessionId: session?.id || `solve_${Date.now()}`,
        questionId: problem.id,
        course: problem.course || '126',
        displayText,
      })

      setQrSession(sessionData)
      // Don't open modal - show QR inline in PartTutorPanel
      setQrStatus({ status: 'pending' })
      startPolling(sessionData.sessionId)

    } catch (error) {
      console.error('[ProblemPractice] QR session failed:', error)
      setQrError(error.message)
    } finally {
      setQrLoading(false)
    }
  }

  const startPolling = (sessionId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)

    pollIntervalRef.current = setInterval(async () => {
      pollCountRef.current += 1
      if (pollCountRef.current > MAX_POLLS) {
        clearInterval(pollIntervalRef.current)
        setQrStatus({ status: 'expired', error: 'Session timed out.' })
        return
      }

      try {
        const result = await pollSessionResult(sessionId)
        setQrStatus(result)

        if (['completed', 'error', 'expired'].includes(result.status)) {
          clearInterval(pollIntervalRef.current)
          if (result.status === 'completed') {
            setClaireFeedback(result)
            setIsUploadOpen(false)
            setQrModalOpen(false)

            // For now, stay in L0_AMBIENT and show feedback
            // Future: escalate to L2_TEACHING if repeated errors or needs deep help
            if (!result.isCorrect && result.teachingMessage) {
              // Add Claire's feedback to thread for context
              claire.sendMessage(
                `The student just submitted work and got feedback: ${result.teachingMessage}. They might need guidance on the next step.`
              )
            }
          }
        }
      } catch (error) {
        console.error('[ProblemPractice] Poll error:', error)
      }
    }, 2500)
  }

  const handleRetryQR = () => {
    setQrSession(null)
    setQrStatus(null)
    setQrError(null)
    handleStartQRUpload()
  }

  const handleAskClaire = async () => {
    setAiLoading(true)
    try {
      const response = await getProblemHelp(problem, currentStepIndex)
      setAiHelp(response.output)
      setShowHintPanel(true)
    } catch (error) {
      console.error('[ProblemPractice] AI help failed:', error)
    } finally {
      setAiLoading(false)
    }
  }

  const handleSubmitTypedAnswer = async () => {
    if (!typedAnswer.latex && !typedAnswer.text) return

    setSubmittingAnswer(true)
    try {
      // Build the problem context
      let problemText = ''
      if (problem.stem) problemText += problem.stem + '\n\n'
      if (currentPart) {
        const label = currentPart.label || String.fromCharCode(97 + currentStepIndex)
        problemText += `Part (${label}): ${currentPart.question_text}`
      }

      // Use LaTeX if available, otherwise use text representation
      const answerText = typedAnswer.latex || typedAnswer.text

      // Build the check request
      const message = `I'm working on this problem:

${problemText}

My answer is: $${answerText}$

Please check if my answer is correct. If it's correct, confirm it. If it's wrong, explain what I got wrong and give me a hint for the right approach.`

      const response = await sendMessage(message)

      // Parse response to determine if correct
      // This is a simple heuristic - look for positive/negative indicators
      const responseText = response.output || ''
      const lowerResponse = responseText.toLowerCase()
      const isCorrect = (
        lowerResponse.includes('correct') ||
        lowerResponse.includes('right') ||
        lowerResponse.includes('good job') ||
        lowerResponse.includes('well done')
      ) && !(
        lowerResponse.includes('not correct') ||
        lowerResponse.includes('incorrect') ||
        lowerResponse.includes('not quite') ||
        lowerResponse.includes('not right')
      )

      setClaireFeedback({
        isCorrect,
        teachingMessage: responseText,
        status: 'completed',
      })
      setShowManualInput(false)
    } catch (error) {
      console.error('[ProblemPractice] Submit answer failed:', error)
    } finally {
      setSubmittingAnswer(false)
    }
  }

  const handleNextStep = () => {
    setCompletedSteps(prev => new Set([...prev, currentStepIndex]))
    if (currentStepIndex < totalSteps - 1) {
      setCurrentStepIndex(currentStepIndex + 1)
    } else {
      // All parts done for this problem, move to next problem in section
      handleNextProblem()
    }
  }

  const handleSelectPart = (index) => {
    if (index === currentStepIndex) return
    // Clear any in-progress feedback / answer state when switching parts
    setClaireFeedback(null)
    setShowAnswer(false)
    setCurrentStepIndex(index)
  }

  const handleMarkComplete = async () => {
    if (session?.id) {
      try {
        await updateSolveSession(session.id, { status: 'completed' })
      } catch (error) {
        console.error('[ProblemPractice] Failed to update session:', error)
      }
    }
    handleBackNavigation('marked_complete')
  }

  const getStepStatus = (index) => {
    if (completedSteps.has(index)) return 'completed'
    if (index === currentStepIndex) return 'current'
    if (index < currentStepIndex || completedSteps.size > 0) return 'upcoming'
    return 'locked'
  }

  const currentLabel = currentPart?.label || String.fromCharCode(97 + currentStepIndex)

  // Handle empty section state
  if (!problem) {
    return (
      <div className="min-h-screen bg-[var(--claire-bg)] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="text-6xl mb-4">📚</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">
            No problems loaded for this topic yet
          </h2>
          <p className="text-gray-500 mb-6">
            {section?.display_name ? `"${section.display_name}" ` : ''}
            doesn't have any practice problems available right now.
          </p>
          <button
            onClick={() => handleBackNavigation('back_button')}
            className="px-6 py-3 bg-[var(--claire-navy)] text-white font-semibold rounded-lg hover:opacity-90"
          >
            Back to Roadmap
          </button>
        </div>
      </div>
    )
  }

  // Latest Claire turn drives the corner bubble (L1 nudge surface).
  // For a teaching-card nudge we lead with the concept bridge (what's going on /
  // the analogy), then the first-step scaffold — never a full solution.
  const lastClaireTurn = [...claire.thread].reverse().find(e => e.role === 'claire')
  let cornerMessage = ''
  if (lastClaireTurn?.type === 'teaching_action') {
    cornerMessage = [lastClaireTurn.conceptBridge, lastClaireTurn.nextMicroStep]
      .filter(Boolean)
      .join('\n\n')
  } else if (lastClaireTurn) {
    cornerMessage = lastClaireTurn.text || lastClaireTurn.question || lastClaireTurn.nextMicroStep || ''
  }
  const cornerReplies = lastClaireTurn?.quickReplies || []

  // First time the bubble opens on a part (idle peek or click), fetch an L1
  // nudge: clarify the problem + give the first-step scaffold / guiding question.
  const handleCornerOpen = () => {
    const hasClaireTurn = claire.thread.some(e => e.role === 'claire')
    if (hasClaireTurn || claire.loading || nudgeRequestedRef.current) return
    nudgeRequestedRef.current = true
    claire.executeTeachingAction('student_stuck', currentStepIndex)
  }

  // Student follow-up after seeing the nudge — free interaction.
  // sendMessage records the user turn itself, so don't append it again here
  // (a double record would duplicate the message in the context we send back).
  const handleCornerRespond = (text) => {
    claire.sendMessage(text, {
      actionType: 'followup',
      partId: currentStepIndex.toString(),
      stepIndex: claire.thread.length,
    })
  }

  return (
    <div className="min-h-screen bg-[var(--claire-bg)]">
      {/* Top Bar - hidden in exam mode (sidebar has navigation) */}
      {!isExamMode && (
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => handleBackNavigation('back_button')}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="font-medium">Back</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-[var(--claire-navy)] font-bold">
              {section?.section_id} {section?.display_name}
            </span>
            <span className="text-gray-400">·</span>
            <span className="text-gray-600 font-medium">
              {formatExamName(problem.exam)} Problem {problem.problem_number}
            </span>
            {totalSteps > 1 && (
              <span className="text-gray-400 font-medium">
                · Part {currentLabel}
              </span>
            )}
          </div>

          <div className="w-20" /> {/* Spacer for centering */}
        </div>
      </div>
      )}

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex gap-8">
          {/* Main Content */}
          <div className="flex-1 max-w-2xl">
            {/* Claire's say bubble or fallback hint */}
            {/* Claire error display */}
            {claire.error && (
              <div className="mb-4 px-3 py-2 bg-red-50 text-red-600 text-sm rounded-lg">
                Error: {claire.error}
              </div>
            )}

            {/* Claire Strip - shows observation or latest response (L0_AMBIENT) */}
            {tutorLevel === TutorLevel.L0_AMBIENT && !claireFeedback && !showAnswer && (
              <ClaireResponseStrip
                l0Dismissed={l0Dismissed}
                problem={problem}
                currentPart={currentPart}
                onDismissL0={() => setL0Dismissed(true)}
              />
            )}

            {/* Problem Stem (if exists) */}
            {problem.stem && (
              <div className="mb-6 text-gray-600 leading-relaxed">
                <MathText text={problem.stem} />
              </div>
            )}

            {/* Current Step Card */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStepIndex}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Step Label */}
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1.5 rounded-full font-bold text-sm bg-[var(--claire-navy)] text-white">
                    Part ({currentLabel})
                  </span>
                </div>

                {/* Question Text */}
                <div className="text-xl text-gray-800 leading-relaxed mb-8">
                  <MathText text={currentPart?.question_text || problem.stem || 'No problem text'} />
                </div>

                {/* Diagram if exists */}
                {currentPart?.diagram_image_url && (
                  <div className="mb-8 rounded-lg overflow-hidden border border-gray-200 inline-block">
                    <img src={currentPart.diagram_image_url} alt="Problem diagram" className="max-w-md" />
                  </div>
                )}

                {/* Claire Feedback (shows after submission) */}
                {claireFeedback && (
                  <div className="mb-8">
                    <ClaireFeedback
                      result={claireFeedback}
                      onContinue={handleNextStep}
                      onTryAgain={() => {
                        setClaireFeedback(null)
                        // Stay in L0_AMBIENT - student continues working
                        // Clear QR session for fresh start
                        setQrSession(null)
                        setQrStatus(null)
                        setQrError(null)
                      }}
                    />
                  </div>
                )}

                {/* Default: Minimal work area (L0_AMBIENT, not uploading) */}
                {!claireFeedback && !showAnswer && tutorLevel === TutorLevel.L0_AMBIENT && !isUploadOpen && (
                  <div className="space-y-6">
                    <WorkAreaCard
                      onShowClaire={() => {
                        setIsUploadOpen(true)
                        handleStartQRUpload()
                      }}
                      onMessage={handlePanelMessage}
                      loading={qrLoading}
                    />
                  </div>
                )}

                {/* Upload UI: Show QR panel (isUploadOpen, not a mode) */}
                {!claireFeedback && !showAnswer && isUploadOpen && (
                  <PartTutorPanel
                    panelState="upload"
                    partLabel={currentPart?.label || String.fromCharCode(97 + currentStepIndex)}
                    threadEvents={[]}
                    loading={false}
                    onAction={handlePanelAction}
                    onSendMessage={handlePanelMessage}
                    onBackToReady={() => setIsUploadOpen(false)}
                    qrUrl={qrSession?.qrUrl}
                    qrLoading={qrLoading}
                    qrStatus={qrStatus}
                    qrError={qrError}
                    onRetryQR={handleRetryQR}
                  />
                )}

                {/* Show Answer State */}
                {showAnswer && currentPart?.final_answer && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--claire-teal-muted)] border border-[var(--claire-teal)] rounded-xl p-5"
                  >
                    <p className="text-xs font-bold text-[var(--claire-teal)] uppercase tracking-wide mb-2">
                      Answer
                    </p>
                    <div className="text-gray-800 text-lg">
                      <MathText text={currentPart.final_answer} />
                    </div>
                    <button
                      onClick={handleNextStep}
                      className="mt-4 px-5 py-2 bg-[var(--claire-teal)] text-white font-semibold rounded-lg hover:opacity-90"
                    >
                      {currentStepIndex < totalSteps - 1 ? 'Next part' : 'Done'}
                    </button>
                  </motion.div>
                )}

              </motion.div>
            </AnimatePresence>
          </div>

          {/* Right Sidebar - minimal */}
          <div className="w-64 flex-shrink-0">
            <div className="sticky top-24 space-y-4">
              {/* Progress Indicator */}
              {totalSteps > 1 && (
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
                    Progress
                  </p>
                  <div className="flex items-center justify-center gap-3">
                    {parts.map((part, index) => {
                      const label = part.label || String.fromCharCode(97 + index)
                      const status = getStepStatus(index)
                      return (
                        <div key={index} className="flex flex-col items-center gap-1">
                          <StepDot label={label} status={status} onClick={() => handleSelectPart(index)} />
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Problem Navigation (when multiple problems in section) */}
              {sectionProblems.length > 1 && (
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                    PROBLEMS IN THIS SECTION
                  </p>
                  <div className="flex items-center justify-between">
                    <button
                      onClick={handlePrevProblem}
                      disabled={currentProblemIndex === 0}
                      className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                      </svg>
                    </button>
                    <span className="text-sm font-medium text-gray-700">
                      {currentProblemIndex + 1} of {sectionProblems.length}
                    </span>
                    <button
                      onClick={handleNextProblem}
                      disabled={currentProblemIndex === sectionProblems.length - 1}
                      className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* QR Upload Modal */}
      <QRUploadModal
        isOpen={qrModalOpen}
        onClose={() => {
          setQrModalOpen(false)
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
        }}
        qrUrl={qrSession?.qrUrl}
        sessionStatus={qrStatus}
        onRetry={handleRetryQR}
      />

      {/* Always-on Claire (L1) - bottom-right corner presence */}
      {!isExamMode && !isUploadOpen && (
        <ClaireCorner
          message={cornerMessage}
          quickReplies={cornerReplies}
          loading={claire.loading}
          autoOpen={cornerAutoOpen}
          onOpen={handleCornerOpen}
          onRespond={handleCornerRespond}
          onEscalate={() => setTutorLevel(TutorLevel.L2_TEACHING)}
        />
      )}
    </div>
  )
}
