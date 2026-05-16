import { useState } from 'react'
import { motion } from 'framer-motion'
import SquishyButton from '../ui/SquishyButton'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
}

const studyPlanOptions = [
  {
    id: 'in_2_days',
    emoji: '🔥',
    label: 'Exam in 2 days',
    description: 'Intensive mode - focus on highest-impact topics',
    color: 'from-red-400 to-red-600',
    schedule: '4-5 problems per day',
  },
  {
    id: 'this_week',
    emoji: '⏰',
    label: 'Exam this week',
    description: 'Focused mode - systematic skill building',
    color: 'from-orange-400 to-orange-600',
    schedule: '2-3 problems per day',
  },
  {
    id: 'catching_up',
    emoji: '📚',
    label: 'Just catching up',
    description: 'Steady mode - thorough understanding',
    color: 'from-blue-400 to-blue-600',
    schedule: '1-2 problems per day',
  },
]

function StudyPlanSelect({ selections, updateSelection, onNext }) {
  const [selected, setSelected] = useState(selections.examTimeline || null)

  const handleSelect = (planId) => {
    setSelected(planId)
    updateSelection('examTimeline', planId)
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex items-center justify-center px-4"
    >
      <div className="w-full max-w-md mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-2"
        >
          <span className="text-4xl">📋</span>
        </motion.div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Let's build your crash plan.
        </h2>
        <p className="text-gray-500 mb-6">
          When's your exam?
        </p>

        {/* Plan options */}
        <div className="space-y-3 mb-8">
          {studyPlanOptions.map((option, index) => (
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
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${option.color} flex items-center justify-center text-2xl shadow-sm`}
              >
                {option.emoji}
              </div>
              <div className="flex-1">
                <div className="font-bold text-gray-800">{option.label}</div>
                <div className="text-sm text-gray-500">{option.description}</div>
              </div>
              {selected === option.id && (
                <div className="shrink-0">
                  <svg
                    className="w-6 h-6 text-[#58cc02]"
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
              <span className="font-medium">Your pace:</span>{' '}
              {studyPlanOptions.find((t) => t.id === selected)?.schedule}
            </p>
          </motion.div>
        )}

        <SquishyButton onClick={onNext} disabled={!selected} className="w-full">
          BUILD MY PLAN
        </SquishyButton>
      </div>
    </motion.div>
  )
}

export default StudyPlanSelect
