import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { TIER_INFO, QUESTION_BANKS } from '../../data/questionBanks'

const analysisSteps = [
  'Analyzing performance...',
  'Mapping knowledge gaps...',
  'Comparing to UW exam patterns...',
  'Building your path...',
]

function ReportGenerating({ testState, course, onComplete }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  const courseNames = {
    math124: 'Math 124',
    math125: 'Math 125',
    math126: 'Math 126',
  }

  const correctCount = useMemo(() => {
    return testState.answers.filter((a) => a.isCorrect).length
  }, [testState.answers])

  useEffect(() => {
    // Progress animation
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 2.5
      })
    }, 50)

    // Step through messages
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= analysisSteps.length - 1) {
          clearInterval(stepInterval)
          return prev
        }
        return prev + 1
      })
    }, 500)

    // Complete after 2.2 seconds
    const completeTimeout = setTimeout(() => {
      onComplete()
    }, 2200)

    return () => {
      clearInterval(progressInterval)
      clearInterval(stepInterval)
      clearTimeout(completeTimeout)
    }
  }, [onComplete])

  // Calculate tier-by-tier results for preview
  const bank = QUESTION_BANKS[course] || []
  const tierPreview = [1, 2, 3, 4].map((tier) => {
    const answer = testState.answers.find((a) => {
      const question = bank.find((q) => q.id === a.questionId)
      return question?.tier === tier
    })
    const question = answer ? bank.find((q) => q.id === answer.questionId) : null
    return {
      tier,
      info: TIER_INFO[tier],
      passed: answer?.isCorrect || false,
      answered: !!answer && !!question,
    }
  })

  return (
    <motion.div
      className="flex-1 flex flex-col items-center justify-center px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="w-full max-w-md text-center">
        {/* Animated processing indicator */}
        <div className="w-24 h-24 mx-auto mb-6 relative">
          {/* Outer ring */}
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-[var(--claire-teal)] border-t-transparent"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />

          {/* Inner circle */}
          <div className="absolute inset-3 bg-[var(--claire-navy)] rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-2xl">
              {Math.round(progress)}%
            </span>
          </div>
        </div>

        <h2 className="text-xl font-semibold text-[var(--claire-navy)] mb-2">
          Generating Your {courseNames[course]} Report
        </h2>

        {/* Current step */}
        <motion.p
          key={currentStep}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm text-[var(--claire-gray-500)] mb-6"
        >
          {analysisSteps[currentStep]}
        </motion.p>

        {/* Progress bar */}
        <div className="progress-bar w-full mb-6">
          <motion.div
            className="progress-bar-fill"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Tier preview */}
        <motion.div
          className="grid grid-cols-4 gap-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.2 }}
        >
          {tierPreview.map(({ tier, info, passed, answered }) => (
            <motion.div
              key={tier}
              className={`p-3 rounded-lg border ${
                answered
                  ? passed
                    ? 'bg-[var(--claire-teal-muted)] border-[var(--claire-teal)]'
                    : 'bg-[var(--claire-weak-bg)] border-[var(--claire-weak)]'
                  : 'bg-[var(--claire-gray-100)] border-[var(--claire-gray-200)]'
              }`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 + tier * 0.1, duration: 0.15 }}
            >
              <div
                className={`text-sm font-bold mb-1 ${
                  answered
                    ? passed
                      ? 'text-[var(--claire-teal)]'
                      : 'text-[var(--claire-weak)]'
                    : 'text-[var(--claire-gray-400)]'
                }`}
              >
                T{tier}
              </div>
              <div className="text-xs text-[var(--claire-gray-500)]">
                {info.name}
              </div>
              {answered && (
                <div className="mt-1">
                  {passed ? (
                    <svg
                      className="w-4 h-4 text-[var(--claire-teal)] mx-auto"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-4 h-4 text-[var(--claire-weak)] mx-auto"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>

        <motion.p
          className="mt-6 text-xs text-[var(--claire-gray-400)]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          {correctCount}/{testState.answers.length} correct
        </motion.p>
      </div>
    </motion.div>
  )
}

export default ReportGenerating
