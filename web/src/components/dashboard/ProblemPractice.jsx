import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { useClaire, CLAIRE_MESSAGES, CLAIRE_STATE } from '../../context/ClaireContext'
import { createSolveSession, updateSolveSession } from '../../api/supabaseApi'
import { getProblemHelp, sendMessage } from '../../api/chatApi'
import { createMobileSession, pollSessionResult } from '../../api/mobileUploadApi'
import ClaireHint from '../claire/ClaireHint'
import MathInput from '../ui/MathInput'
import katex from 'katex'
import 'katex/dist/katex.min.css'

// Render LaTeX using KaTeX
function MathText({ text, className = '' }) {
  if (!text) return null

  const renderMath = (str) => {
    const parts = str.split(/(\$\$[^$]+\$\$|\$[^$]+\$|\\[[^\]]+\\]|\\\\[[^\]]+\\\\])/g)

    return parts.map((part, i) => {
      if ((part.startsWith('$$') && part.endsWith('$$')) ||
          (part.startsWith('\\[') && part.endsWith('\\]'))) {
        const math = part.startsWith('$$') ? part.slice(2, -2) : part.slice(2, -2)
        try {
          const html = katex.renderToString(math, {
            throwOnError: false,
            displayMode: true,
            strict: false,
          })
          return (
            <span
              key={i}
              className="block my-3"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          )
        } catch (e) {
          return <span key={i} className="font-mono">{math}</span>
        }
      }
      if (part.startsWith('$') && part.endsWith('$')) {
        const math = part.slice(1, -1)
        try {
          const html = katex.renderToString(math, {
            throwOnError: false,
            displayMode: false,
            strict: false,
          })
          return (
            <span
              key={i}
              className="mx-0.5"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          )
        } catch (e) {
          return <span key={i} className="font-mono">{math}</span>
        }
      }
      return <span key={i} dangerouslySetInnerHTML={{ __html: part }} />
    })
  }

  return <span className={`math-text ${className}`}>{renderMath(text)}</span>
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
              <>
                <button
                  onClick={onTryAgain}
                  className="px-5 py-2.5 bg-[var(--claire-navy)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
                >
                  Try again
                </button>
                <button
                  onClick={onContinue}
                  className="px-5 py-2.5 text-gray-500 font-medium hover:text-gray-700 transition-colors"
                >
                  Skip this part
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Step Progress Dot Component
function StepDot({ label, status, isMain }) {
  const baseClasses = "flex items-center justify-center rounded-full font-bold text-xs transition-all"
  const sizeClasses = isMain ? "w-8 h-8" : "w-6 h-6"

  const statusClasses = {
    completed: "bg-[var(--claire-teal)] text-white",
    current: "bg-[var(--claire-navy)] text-white ring-4 ring-[var(--claire-next-bg)]",
    upcoming: "bg-gray-100 text-gray-400 border-2 border-gray-200",
    locked: "bg-gray-50 text-gray-300 border border-gray-100",
  }

  return (
    <div className={`${baseClasses} ${sizeClasses} ${statusClasses[status]}`}>
      {status === 'completed' ? (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        label
      )}
    </div>
  )
}

export default function ProblemPractice({ section, problem: directProblem, onBack, isExamMode = false }) {
  const { user } = useAuth()
  const { setClaire } = useClaire()

  // Section context with filtered problems (or single direct problem for exam mode)
  const sectionProblems = directProblem ? [directProblem] : (section?.problems || [])
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const problem = sectionProblems[currentProblemIndex] || null

  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [completedSteps, setCompletedSteps] = useState(new Set())
  const [session, setSession] = useState(null)
  const [claireFeedback, setClaireFeedback] = useState(null)
  const [claireHintMessage, setClaireHintMessage] = useState(CLAIRE_MESSAGES.problemHint)

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

  const parts = problem?.parts || []
  const currentPart = parts[currentStepIndex]
  const totalSteps = parts.length

  // Find the "main" question - typically (b) or the second part
  const mainQuestionIndex = parts.length > 1 ? 1 : 0

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

  // Reset state when step changes
  useEffect(() => {
    setClaireFeedback(null)
    setShowAnswer(false)
    setAiHelp(null)
    setShowHintPanel(false)
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    // Reset hint message for new step
    setClaireHintMessage(CLAIRE_MESSAGES.problemHint)
  }, [currentStepIndex])

  // Reset state when problem changes
  useEffect(() => {
    setCurrentStepIndex(0)
    setCompletedSteps(new Set())
    setClaireFeedback(null)
    setShowAnswer(false)
    setAiHelp(null)
    setShowHintPanel(false)
    setShowManualInput(false)
    setTypedAnswer({ latex: '', text: '' })
    setClaireHintMessage(CLAIRE_MESSAGES.problemHint)
  }, [currentProblemIndex])

  const handleNextProblem = () => {
    if (currentProblemIndex < sectionProblems.length - 1) {
      setCurrentProblemIndex(currentProblemIndex + 1)
    } else {
      // All problems done, go back
      onBack()
    }
  }

  const handlePrevProblem = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(currentProblemIndex - 1)
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
      // Clear the inline hint since we have feedback
      setClaireHintMessage(null)
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
      setQrModalOpen(true)
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
    setQrModalOpen(false)
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

  const handleSkipStep = () => {
    if (currentStepIndex < totalSteps - 1) {
      setCurrentStepIndex(currentStepIndex + 1)
    } else {
      onBack()
    }
  }

  const handleMarkComplete = async () => {
    if (session?.id) {
      try {
        await updateSolveSession(session.id, { status: 'completed' })
      } catch (error) {
        console.error('[ProblemPractice] Failed to update session:', error)
      }
    }
    onBack()
  }

  const getStepStatus = (index) => {
    if (completedSteps.has(index)) return 'completed'
    if (index === currentStepIndex) return 'current'
    if (index < currentStepIndex || completedSteps.size > 0) return 'upcoming'
    return 'locked'
  }

  const currentLabel = currentPart?.label || String.fromCharCode(97 + currentStepIndex)
  const isMainQuestion = currentStepIndex === mainQuestionIndex

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
            onClick={onBack}
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
            onClick={onBack}
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
            {sectionProblems.length > 1 && (
              <span className="text-gray-400 font-medium">
                ({currentProblemIndex + 1}/{sectionProblems.length})
              </span>
            )}
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
            {/* Claire's hint at the top (before submission) */}
            {!claireFeedback && claireHintMessage && (
              <ClaireHint message={claireHintMessage} />
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
                  <span className={`px-3 py-1.5 rounded-full font-bold text-sm ${
                    isMainQuestion
                      ? 'bg-[var(--claire-navy)] text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    Part ({currentLabel})
                  </span>
                  {isMainQuestion && (
                    <span className="text-xs font-semibold text-[var(--claire-navy)] uppercase tracking-wide">
                      Main Question
                    </span>
                  )}
                  {currentStepIndex === 0 && totalSteps > 1 && (
                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                      Warm-up
                    </span>
                  )}
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
                      onTryAgain={() => setClaireFeedback(null)}
                    />
                  </div>
                )}

                {/* Main Submission Area */}
                {!claireFeedback && !showAnswer && (
                  <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                    <div className="p-6">
                      <div className="flex items-start gap-6">
                        {/* Left: Instructions */}
                        <div className="flex-1">
                          <h3 className="font-bold text-gray-800 mb-2">Write it on paper</h3>
                          <p className="text-gray-500 text-sm leading-relaxed">
                            Solve on paper like you would in an exam. Show your full work —
                            Claire will check each step and explain any mistakes.
                          </p>
                        </div>

                        {/* Right: Scan Button */}
                        <button
                          onClick={handleStartQRUpload}
                          disabled={qrLoading || !user}
                          className="flex-shrink-0 px-6 py-4 bg-[var(--claire-navy)] text-white font-bold rounded-xl hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-3 shadow-md"
                        >
                          {qrLoading ? (
                            <>
                              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                              <span>Creating...</span>
                            </>
                          ) : (
                            <>
                              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                              </svg>
                              <span>Scan to Submit</span>
                            </>
                          )}
                        </button>
                      </div>

                      {!user && (
                        <p className="mt-4 text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
                          Sign in to submit your work
                        </p>
                      )}

                      {qrError && (
                        <p className="mt-4 text-sm text-[var(--claire-weak)] bg-[var(--claire-weak-bg)] px-3 py-2 rounded-lg">
                          {qrError}
                        </p>
                      )}
                    </div>

                    {/* Secondary: Type answer */}
                    <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
                      <button
                        onClick={() => setShowManualInput(!showManualInput)}
                        className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        {showManualInput ? '← Back to scan' : 'Or type your answer manually →'}
                      </button>
                    </div>

                    {/* Manual Input Area */}
                    <AnimatePresence>
                      {showManualInput && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="p-6 border-t border-gray-100">
                            <label className="block text-sm font-medium text-gray-700 mb-3">
                              Your answer
                            </label>
                            <MathInput
                              value={typedAnswer.latex}
                              onChange={setTypedAnswer}
                              placeholder="Type or click buttons to enter math..."
                              disabled={submittingAnswer}
                            />
                            <div className="mt-4 flex items-center justify-end">
                              <button
                                onClick={handleSubmitTypedAnswer}
                                disabled={(!typedAnswer.latex && !typedAnswer.text) || submittingAnswer}
                                className="px-6 py-3 bg-[var(--claire-navy)] text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
                              >
                                {submittingAnswer ? (
                                  <>
                                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Checking...
                                  </>
                                ) : (
                                  'Check my answer'
                                )}
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
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

                {/* Step Navigation (at bottom of current step) */}
                {!claireFeedback && !showAnswer && (
                  <div className="mt-6 flex items-center justify-between">
                    <button
                      onClick={handleSkipStep}
                      className="text-gray-400 hover:text-gray-600 text-sm font-medium transition-colors"
                    >
                      Skip this part
                    </button>
                    <button
                      onClick={() => setShowAnswer(true)}
                      className="text-gray-400 hover:text-gray-600 text-sm font-medium transition-colors"
                    >
                      I give up, show answer
                    </button>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Right Sidebar */}
          <div className="w-72 flex-shrink-0">
            <div className="sticky top-24 space-y-6">
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
                      const isMain = index === mainQuestionIndex
                      return (
                        <div key={index} className="flex flex-col items-center gap-1">
                          <StepDot label={label} status={status} isMain={isMain} />
                          {isMain && (
                            <span className="text-[10px] font-medium text-[var(--claire-navy)]">
                              main
                            </span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Tip about warm-up */}
              {currentStepIndex === 0 && totalSteps > 1 && (
                <div className="bg-[var(--claire-next-bg)] rounded-xl p-4">
                  <p className="text-sm text-gray-600 leading-relaxed">
                    <span className="font-semibold text-[var(--claire-navy)]">Tip:</span> Part (a)
                    helps you build up to the main question. You can skip it or come back anytime.
                  </p>
                </div>
              )}

              {/* What happens next */}
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
                  What happens next?
                </p>
                <div className="space-y-3">
                  {[
                    { icon: '📱', text: 'Scan your handwritten work' },
                    { icon: '🔍', text: 'Claire reads and checks it' },
                    { icon: '💬', text: 'Get step-by-step feedback' },
                  ].map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-lg">{step.icon}</span>
                      <span className="text-sm text-gray-600">{step.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ask Claire for hint */}
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Need a hint?
                </p>
                <button
                  onClick={handleAskClaire}
                  disabled={aiLoading}
                  className="w-full py-2.5 text-sm font-medium text-[var(--claire-navy)] bg-[var(--claire-ai-bg)] rounded-lg hover:bg-[var(--claire-next-bg)] transition-colors disabled:opacity-50"
                >
                  {aiLoading ? 'Thinking...' : 'Ask Claire for a hint'}
                </button>

                {showHintPanel && aiHelp && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600 leading-relaxed"
                  >
                    {aiHelp}
                  </motion.div>
                )}
              </div>

              {/* Problem Navigation (when multiple problems in section) */}
              {sectionProblems.length > 1 && (
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                    Problems in this section
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
