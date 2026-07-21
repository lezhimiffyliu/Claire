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

const examOptions = [
  { id: 'midterm1', label: 'Midterm 1', description: 'Velocity, Quadric Surfaces, Lines & Planes', emoji: '📝', color: 'from-blue-400 to-blue-600' },
  { id: 'midterm2', label: 'Midterm 2', description: 'Tangent Planes, Double Integrals, Optimization', emoji: '📋', color: 'from-amber-400 to-amber-600' },
  { id: 'final', label: 'Final Exam', description: 'Comprehensive - All Topics', emoji: '🎯', color: 'from-emerald-400 to-emerald-600' },
]

function ExamSelection({ direction, onNext, selections, updateSelection }) {
  const [selected, setSelected] = useState(selections.exam || null)

  const handleSelect = (examId) => {
    setSelected(examId)
    updateSelection('exam', examId)
  }

  const handleContinue = () => {
    if (selected) {
      onNext()
    }
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
          <span className="text-4xl">🎓</span>
        </motion.div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Which exam are you preparing for?
        </h2>
        <p className="text-gray-500 mb-6">
          We'll focus on topics covered in that exam
        </p>

        {/* Exam options */}
        <div className="space-y-3 mb-8">
          {examOptions.map((exam, index) => (
            <motion.button
              key={exam.id}
              onClick={() => handleSelect(exam.id)}
              className={`option-card w-full text-left flex items-center gap-4 ${
                selected === exam.id ? 'selected' : ''
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + index * 0.08 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${exam.color} flex items-center justify-center text-2xl shadow-sm`}>
                {exam.emoji}
              </div>
              <div className="flex-1">
                <div className="font-bold text-gray-800">{exam.label}</div>
                <div className="text-sm text-gray-500">{exam.description}</div>
              </div>
              {selected === exam.id && (
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

        <SquishyButton
          onClick={handleContinue}
          disabled={!selected}
          className="w-full"
        >
          CONTINUE
        </SquishyButton>
      </div>
    </motion.div>
  )
}

export default ExamSelection
