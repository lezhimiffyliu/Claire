import { useState } from 'react'
import { motion } from 'framer-motion'
import SquishyButton from '../ui/SquishyButton'

const pageVariants = {
  initial: (direction) => ({
    x: direction > 0 ? '100%' : '-100%',
    opacity: 0,
  }),
  animate: {
    x: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
    },
  },
  exit: (direction) => ({
    x: direction > 0 ? '-100%' : '100%',
    opacity: 0,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
    },
  }),
}

const timelineOptions = [
  {
    id: 'urgent',
    emoji: '🔥',
    label: '< 1 week',
    description: 'Exam is coming up fast',
    days: 7,
    color: 'from-red-400 to-red-600',
    urgency: 'critical',
    schedule: 'Intensive daily practice',
  },
  {
    id: 'soon',
    emoji: '⏰',
    label: '1-2 weeks',
    description: 'Time to focus',
    days: 14,
    color: 'from-orange-400 to-orange-600',
    urgency: 'high',
    schedule: '2-3 problems per day',
  },
  {
    id: 'moderate',
    emoji: '📅',
    label: '2-4 weeks',
    description: 'Good runway to prepare',
    days: 28,
    color: 'from-blue-400 to-blue-600',
    urgency: 'moderate',
    schedule: '1-2 problems per day',
  },
  {
    id: 'relaxed',
    emoji: '🌱',
    label: '1+ month',
    description: 'Plenty of time to master',
    days: 45,
    color: 'from-green-400 to-green-600',
    urgency: 'low',
    schedule: 'Steady weekly practice',
  },
]

function TimelineSelection({ direction, onNext, onSkipDiagnostic, selections, updateSelection }) {
  const [selected, setSelected] = useState(selections.timeline)

  const handleSelect = (timelineId) => {
    setSelected(timelineId)
    const option = timelineOptions.find(t => t.id === timelineId)
    updateSelection('timeline', timelineId)
    updateSelection('daysUntilExam', option.days)
    updateSelection('urgency', option.urgency)
    // Store the target exam date so we can calculate days remaining dynamically
    const targetDate = new Date()
    targetDate.setDate(targetDate.getDate() + option.days)
    updateSelection('examTargetDate', targetDate.toISOString())
  }

  return (
    <motion.div
      custom={direction}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 overflow-y-auto px-4 py-8"
    >
      <div className="w-full max-w-md mx-auto text-center min-h-full flex flex-col justify-center">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-2"
        >
          <span className="text-4xl">📆</span>
        </motion.div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          When's your exam?
        </h2>
        <p className="text-gray-500 mb-6">
          We'll optimize your study schedule
        </p>

        {/* Timeline options */}
        <div className="space-y-3 mb-8">
          {timelineOptions.map((option, index) => (
            <motion.button
              key={option.id}
              onClick={() => handleSelect(option.id)}
              className={`option-card w-full text-left flex items-center gap-4 ${
                selected === option.id ? 'selected' : ''
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + index * 0.08 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${option.color} flex items-center justify-center text-2xl shadow-sm`}>
                {option.emoji}
              </div>
              <div className="flex-1">
                <div className="font-bold text-gray-800">{option.label}</div>
                <div className="text-sm text-gray-500">{option.description}</div>
              </div>
              {selected === option.id && (
                <div className="shrink-0">
                  <svg
                    className="w-6 h-6 text-[#2FBF9F]"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </motion.button>
          ))}
        </div>

        {/* Schedule preview */}
        {selected && (
          <motion.div
            className="mb-6 p-3 bg-gray-50 rounded-xl"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
          >
            <p className="text-sm text-gray-600">
              <span className="font-medium">Recommended:</span>{' '}
              {timelineOptions.find(t => t.id === selected)?.schedule}
            </p>
          </motion.div>
        )}

        <SquishyButton
          onClick={onNext}
          disabled={!selected}
          className="w-full"
        >
          CONTINUE
        </SquishyButton>

        {/* Skip diagnostic option */}
        <motion.button
          onClick={onSkipDiagnostic}
          className="mt-4 text-sm text-gray-400 hover:text-gray-600 transition-colors"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          disabled={!selected}
        >
          Skip diagnostic test →
        </motion.button>
      </div>
    </motion.div>
  )
}

export default TimelineSelection
