import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { useClaire, CLAIRE_MESSAGES, CLAIRE_STATE } from '../../context/ClaireContext'
import { createSolveSession, updateSolveSession } from '../../api/supabaseApi'
import { submitAttempt, continueTeaching } from '../../api/attemptApi'
import { createMobileSession, pollSessionResult } from '../../api/mobileUploadApi'
import PartTutorPanel from '../claire/PartTutorPanel'
import ClaireL0Strip from '../claire/ClaireL0Strip'
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
// It only surfaces the pre-authored ambient observation for the problem.
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
// Humanize a snake_case enum value ("give_hint" -> "Give hint").
function humanizeToken(token) {
  if (!token) return ''
  return token
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function ClaireFeedback({ result, onContinue, onTryAgain }) {
  if (!result) return null

  const isCorrect = result.isCorrect
  const isUncertain = result.isUncertain
  const resolved = result.resolved ?? isCorrect
  const message = result.teachingMessage
  const recommendations = result.recommendations || []
  const showHintLevel = result.hintLevel && result.hintLevel !== 'none'

  const tone = isCorrect
    ? 'correct'
    : isUncertain
      ? 'uncertain'
      : 'review'
  const toneStyles = {
    correct: 'bg-[var(--claire-teal-muted)] border-[var(--claire-teal)]',
    uncertain: 'bg-blue-50 border-blue-400',
    review: 'bg-amber-50 border-amber-400',
  }
  const headingStyles = {
    correct: 'text-[var(--claire-teal)]',
    uncertain: 'text-blue-700',
    review: 'text-amber-700',
  }
  const headingText = {
    correct: 'Correct!',
    uncertain: "Let's clarify",
    review: "Let's review this",
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-6 rounded-xl border-l-4 ${toneStyles[tone]}`}
    >
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isCorrect ? 'bg-[var(--claire-teal)] text-white' : (isUncertain ? 'bg-blue-400 text-white' : 'bg-amber-400 text-white')
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
          <h4 className={`font-bold text-lg ${headingStyles[tone]}`}>
            {headingText[tone]}
          </h4>

          <div className="mt-3 text-gray-700 leading-relaxed whitespace-pre-wrap">
            {message}
          </div>

          {/* Structured teaching signals from run_tutor_turn (no client grading). */}
          {(result.action || showHintLevel) && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              {result.action && (
                <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-700 font-medium">
                  {humanizeToken(result.action)}
                </span>
              )}
              {showHintLevel && (
                <span className="px-2 py-1 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                  Hint: {humanizeToken(result.hintLevel)}
                </span>
              )}
              {resolved && (
                <span className="px-2 py-1 rounded-full bg-[var(--claire-teal-muted)] text-[var(--claire-teal)] font-medium">
                  Resolved
                </span>
              )}
            </div>
          )}

          {/* Misconception — debug / collapsible detail. */}
          {result.misconception && (
            <details className="mt-2 text-xs text-gray-500">
              <summary className="cursor-pointer select-none">Diagnosis</summary>
              <span className="ml-1">{humanizeToken(result.misconception)}</span>
            </details>
          )}

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

          {/* Next-problem recommendations (shown once the problem resolves). */}
          {resolved && recommendations.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Recommended next
              </p>
              <div className="mt-2 space-y-1">
                {recommendations.slice(0, 3).map((rec, i) => (
                  <div key={rec.id || rec.question_id || i} className="text-sm text-gray-700">
                    • {rec.title || rec.topic || rec.question_id || rec.id}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-5 flex gap-3">
            {resolved ? (
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

// Teaching-episode reply thread. Rendered under the graded feedback for a
// wrong/uncertain attempt: the student's follow-up replies here go to
// POST /api/attempt/continue (run_teaching_turn) — not the /api/attempt grader.
// Input is a controlled value owned by the parent so it survives a failed request.
function TeachingReply({
  turns,
  input,
  onInputChange,
  onSend,
  loading,
  error,
  ended,
  needsResubmit,
  onResubmit,
}) {
  const canSend = input.trim().length > 0 && !loading && !ended
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSend()
    }
  }

  return (
    <div className="mt-4 border-t border-gray-200 pt-4">
      {/* Follow-up dialogue (student ↔ tutor), oldest first. */}
      {turns.length > 0 && (
        <div className="space-y-2 mb-3">
          {turns.map((t, i) => (
            <div
              key={i}
              className={`text-sm rounded-lg px-3 py-2 whitespace-pre-wrap ${
                t.role === 'student'
                  ? 'bg-gray-100 text-gray-800 ml-8'
                  : 'bg-[var(--claire-next-bg)] text-gray-800 mr-8'
              }`}
            >
              {t.text}
              {t.role === 'tutor' && t.toolUsed && (
                <span className="ml-2 text-[10px] uppercase tracking-wide text-gray-400">
                  · {humanizeToken(t.toolUsed)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Redirect: a full answer was pasted — must be graded via /api/attempt. */}
      {needsResubmit && (
        <div className="mb-3 p-3 rounded-lg bg-blue-50 border border-blue-200 text-sm text-blue-800">
          That looks like a complete answer. To have it checked, re-enter it in
          the answer box and submit it for grading.
          {onResubmit && (
            <button
              onClick={onResubmit}
              className="ml-2 underline font-medium hover:no-underline"
            >
              Open answer box
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="mb-3 px-3 py-2 bg-red-50 text-red-600 text-sm rounded-lg">
          {error}
        </div>
      )}

      {ended ? (
        <p className="text-xs text-gray-400 italic">
          This teaching session has ended. Pick the next part or a new problem to
          keep going.
        </p>
      ) : (
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            placeholder="Reply, ask a question, or share your next step…"
            disabled={loading}
            className="flex-1 resize-none rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--claire-navy)] disabled:opacity-60"
          />
          <button
            onClick={onSend}
            disabled={!canSend}
            className="px-4 py-2 bg-[var(--claire-navy)] text-white text-sm font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending…' : 'Send'}
          </button>
        </div>
      )}
    </div>
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
  // Teaching-session id for typed grading: scopes progression across the
  // consecutive submissions of one problem, and isolates one problem from the
  // next. A new id is minted whenever the active problem changes (or on an
  // explicit restart), which the backend reads as "start a fresh session".
  const [attemptSessionId, setAttemptSessionId] = useState(null)

  // Teaching-episode state: the multi-turn follow-up dialogue that runs AFTER a
  // graded wrong/uncertain attempt. Replies here go to POST /api/attempt/continue
  // (kept strictly separate from the /api/attempt grader). The episode is scoped
  // to the current problem + attemptSessionId;
  // it is reset on every new submission, part change, and problem change. There is
  // no server GET for teaching state, so it does NOT survive a page refresh.
  const [episodeTurns, setEpisodeTurns] = useState([])
  const [episodeInput, setEpisodeInput] = useState('')
  const [episodeLoading, setEpisodeLoading] = useState(false)
  const [episodeError, setEpisodeError] = useState(null)
  const [episodeEnded, setEpisodeEnded] = useState(false)
  const [episodeNeedsResubmit, setEpisodeNeedsResubmit] = useState(false)

  // Clear the follow-up teaching dialogue. Called on a new submission, part
  // change, problem change, and "Try again" — a fresh graded result always
  // starts a fresh episode.
  const resetTeachingEpisode = () => {
    setEpisodeTurns([])
    setEpisodeInput('')
    setEpisodeLoading(false)
    setEpisodeError(null)
    setEpisodeEnded(false)
    setEpisodeNeedsResubmit(false)
  }

  // QR Upload state
  const [qrModalOpen, setQrModalOpen] = useState(false)
  const [qrSession, setQrSession] = useState(null)
  const [qrStatus, setQrStatus] = useState(null)
  const [qrLoading, setQrLoading] = useState(false)
  const [qrError, setQrError] = useState(null)
  const pollIntervalRef = useRef(null)
  const pollCountRef = useRef(0)
  const MAX_POLLS = 120

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

  const parts = problem?.parts || []
  const currentPart = parts[currentStepIndex]
  const totalSteps = parts.length

  // Mint a fresh teaching-session id whenever the active problem changes.
  useEffect(() => {
    if (problem?.id) {
      setAttemptSessionId(`att_${problem.id}_${Date.now()}`)
    }
  }, [problem?.id])

  // NOTE: Future work — treat one part (e.g. part b) as the "main" question and the
  // others as scaffolding/auxiliary parts. Deferred for now; all parts are shown as
  // equal peers. See docs/TUTOR_LAYERS.md ("Main-part assumption — deferred").

  // Track previous step/problem to detect actual changes (not just re-renders)
  const prevStepRef = useRef(currentStepIndex)
  const prevProblemRef = useRef(currentProblemIndex)

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
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    setTutorLevel(TutorLevel.L0_AMBIENT)
    setIsUploadOpen(false)
    setQrSession(null)
    setQrStatus(null)
    setQrError(null)
    setL0Dismissed(false)
    resetTeachingEpisode()
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
  }, [currentStepIndex])

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
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    setTutorLevel(TutorLevel.L0_AMBIENT)
    setIsUploadOpen(false)
    setQrSession(null)
    setQrStatus(null)
    setQrError(null)
    setL0Dismissed(false)
    resetTeachingEpisode()
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
  }, [currentProblemIndex])

  // Wrapper for back navigation - marks session as intentionally ended
  const handleBackNavigation = (reason) => {
    console.log('[ProblemPractice] Back navigation', { reason, instanceId })
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

  const handleSubmitTypedAnswer = async () => {
    if (!typedAnswer.latex && !typedAnswer.text) return

    setSubmittingAnswer(true)
    // A fresh graded result starts a fresh teaching episode.
    resetTeachingEpisode()
    try {
      // Prefer LaTeX; fall back to the plain-text representation.
      const answerText = typedAnswer.latex || typedAnswer.text
      const partLabel =
        currentPart?.label || String.fromCharCode(97 + currentStepIndex)

      // The SINGLE grading path: run_tutor_turn behind /api/attempt.
      // Correctness is decided server-side by the SymPy verifier; we do NOT
      // string-match prose, grade locally, or send the official answer.
      const result = await submitAttempt({
        problemId: problem.id,
        answer: answerText,
        course: problem.course,
        partLabel,
        attemptSessionId,
        source: 'practice',
      })

      setClaireFeedback({
        episodeType: 'attempt',   // enables the /api/attempt/continue reply thread
        isCorrect: result.is_correct,
        isUncertain: result.is_uncertain,
        gradeStatus: result.grade_status,
        teachingMessage: result.message,
        action: result.action,
        hintLevel: result.hint_level,
        misconception: result.misconception,
        phase: result.phase,
        resolved: result.phase === 'resolved',
        recommendations: result.recommendations || [],
        persisted: result.persisted,
        status: 'completed',
      })
      setShowManualInput(false)
    } catch (error) {
      console.error('[ProblemPractice] Submit answer failed:', error)
      setClaireFeedback({
        isCorrect: false,
        gradeStatus: 'error',
        teachingMessage:
          error.message ||
          'Something went wrong grading your answer. Please try again.',
        status: 'error',
      })
    } finally {
      setSubmittingAnswer(false)
    }
  }

  // Send one follow-up reply within the current teaching episode. Uses the
  // dedicated /api/attempt/continue path (run_teaching_turn) — it never grades
  // the final answer. Guards against concurrent sends and preserves the input
  // on failure so nothing the student typed is lost.
  const handleSendTeachingReply = async () => {
    const text = episodeInput.trim()
    if (!text || episodeLoading || episodeEnded) return

    setEpisodeLoading(true)
    setEpisodeError(null)
    try {
      const partLabel =
        currentPart?.label || String.fromCharCode(97 + currentStepIndex)
      const res = await continueTeaching({
        problemId: problem.id,
        message: text,
        course: problem.course,
        partLabel,
        attemptSessionId,
      })

      // Success: commit both turns and clear the input.
      setEpisodeTurns((prev) => [
        ...prev,
        { role: 'student', text },
        { role: 'tutor', text: res.message, action: res.action, toolUsed: res.tool_used },
      ])
      setEpisodeInput('')

      // A pasted full answer must go through the grader, not this path — flag it
      // WITHOUT presenting anything as graded.
      if (res.redirect_to_submit) setEpisodeNeedsResubmit(true)
      // Problem resolved/abandoned: stop treating replies as episode continuations.
      if (res.ended) setEpisodeEnded(true)
    } catch (error) {
      console.error('[ProblemPractice] Teaching reply failed:', error)
      // Keep episodeInput intact so the student can retry without retyping.
      setEpisodeError(
        error.message || 'Could not send your reply. Please try again.'
      )
    } finally {
      setEpisodeLoading(false)
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
                        resetTeachingEpisode()
                        // Stay in L0_AMBIENT - student continues working
                        // Clear QR session for fresh start
                        setQrSession(null)
                        setQrStatus(null)
                        setQrError(null)
                      }}
                    />

                    {/* Multi-turn teaching: only for a graded attempt that is not
                        resolved. Replies go to /api/attempt/continue. */}
                    {claireFeedback.episodeType === 'attempt' &&
                      claireFeedback.status === 'completed' &&
                      !claireFeedback.resolved && (
                        <TeachingReply
                          turns={episodeTurns}
                          input={episodeInput}
                          onInputChange={setEpisodeInput}
                          onSend={handleSendTeachingReply}
                          loading={episodeLoading}
                          error={episodeError}
                          ended={episodeEnded}
                          needsResubmit={episodeNeedsResubmit}
                          onResubmit={() => setShowManualInput(true)}
                        />
                      )}
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

    </div>
  )
}
