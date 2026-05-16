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
  { id: 'math124', label: 'Math 124', description: 'Calculus I' },
  { id: 'math125', label: 'Math 125', description: 'Calculus II' },
  { id: 'math126', label: 'Math 126', description: 'Calculus III' },
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
      className="w-full max-w-md mx-auto text-center"
    >
      <h2 className="text-2xl font-bold text-gray-800 mb-2">
        What's your current course?
      </h2>
      <p className="text-gray-500 mb-8">
        We'll customize your experience
      </p>

      {/* Course options */}
      <div className="space-y-3 mb-8">
        {courses.map((course) => (
          <motion.button
            key={course.id}
            onClick={() => handleSelect(course.id)}
            className={`option-card w-full text-left flex items-center gap-4 ${
              selected === course.id ? 'selected' : ''
            }`}
            whileTap={{ scale: 0.98 }}
          >
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
              {course.label.split(' ')[1]}
            </div>
            <div>
              <div className="font-bold text-gray-800">{course.label}</div>
              <div className="text-sm text-gray-500">{course.description}</div>
            </div>
            {selected === course.id && (
              <div className="ml-auto">
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

      <SquishyButton
        onClick={onNext}
        disabled={!selected}
        className="w-full"
      >
        CONTINUE
      </SquishyButton>
    </motion.div>
  )
}

export default PathSelection
