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

const courses = [
  { id: 'math124', label: 'Calc I', description: 'Differential Calculus (Math 124)', emoji: '🌱', color: 'from-blue-400 to-blue-600' },
  { id: 'math125', label: 'Calc II', description: 'Integral Calculus (Math 125)', emoji: '📈', color: 'from-amber-400 to-amber-600' },
  { id: 'math126', label: 'Calc III', description: 'Multivariable Calculus (Math 126)', emoji: '🚀', color: 'from-emerald-400 to-emerald-600' },
]

function PathSelection({ direction, onNext, selections, updateSelection }) {
  const [selected, setSelected] = useState(selections.course)

  const handleSelect = (courseId) => {
    setSelected(courseId)
    updateSelection('course', courseId)
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
          <span className="text-4xl">📚</span>
        </motion.div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          What's your current course?
        </h2>
        <p className="text-gray-500 mb-6">
          We'll customize your experience
        </p>

        {/* Course options */}
        <div className="space-y-3 mb-8">
          {courses.map((course, index) => (
            <motion.button
              key={course.id}
              onClick={() => handleSelect(course.id)}
              className={`option-card w-full text-left flex items-center gap-4 ${
                selected === course.id ? 'selected' : ''
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + index * 0.08 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${course.color} flex items-center justify-center text-2xl shadow-sm`}>
                {course.emoji}
              </div>
              <div className="flex-1">
                <div className="font-bold text-gray-800">{course.label}</div>
                <div className="text-sm text-gray-500">{course.description}</div>
              </div>
              {selected === course.id && (
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
          onClick={onNext}
          disabled={!selected}
          className="w-full"
        >
          CONTINUE
        </SquishyButton>
      </div>
    </motion.div>
  )
}

export default PathSelection
