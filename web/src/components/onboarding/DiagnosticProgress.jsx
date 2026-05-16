import { motion } from 'framer-motion'

/**
 * Clean progress bar for diagnostic test.
 * Uses progressPercent from adaptive engine.
 * No mascots, no emojis - just clean status indication.
 */
function DiagnosticProgress({
  questionNumber,
  totalQuestions,
  progressPercent,
  answers,
}) {
  const correctCount = answers.filter((a) => a.isCorrect).length

  return (
    <div className="flex items-center gap-3">
      {/* Progress indicator node */}
      <div className="relative">
        <div className="w-10 h-10 bg-[var(--claire-navy)] rounded-lg flex items-center justify-center">
          <span className="text-white font-semibold text-sm">
            {questionNumber}
          </span>
        </div>

        {/* Correct count badge */}
        {correctCount > 0 && (
          <motion.div
            className="absolute -top-1 -right-1 w-5 h-5 bg-[var(--claire-teal)] rounded-full flex items-center justify-center text-xs font-bold text-white"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.15 }}
          >
            {correctCount}
          </motion.div>
        )}
      </div>

      {/* Progress bar */}
      <div className="flex-1 progress-bar h-2">
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${progressPercent}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        />
      </div>

      {/* Question counter */}
      <div className="text-sm font-medium text-[var(--claire-gray-500)] whitespace-nowrap">
        {questionNumber} / {totalQuestions}
      </div>
    </div>
  )
}

export default DiagnosticProgress
