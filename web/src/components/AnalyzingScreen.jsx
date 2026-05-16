import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SquishyButton from './ui/SquishyButton'

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

const analysisSteps = [
  { text: 'Loading UW past papers...', icon: '📄' },
  { text: 'Analyzing question patterns...', icon: '🔍' },
  { text: 'Mapping difficulty levels...', icon: '📊' },
  { text: 'Building your study plan...', icon: '✨' },
]

function AnalyzingScreen({ direction, selections, onNext }) {
  const [currentAnalysis, setCurrentAnalysis] = useState(0)
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    // Progress animation
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 1
      })
    }, 30)

    // Step through analysis messages
    const stepInterval = setInterval(() => {
      setCurrentAnalysis((prev) => {
        if (prev >= analysisSteps.length - 1) {
          clearInterval(stepInterval)
          return prev
        }
        return prev + 1
      })
    }, 800)

    // Complete after 3 seconds
    const completeTimeout = setTimeout(() => {
      setIsComplete(true)
    }, 3200)

    return () => {
      clearInterval(progressInterval)
      clearInterval(stepInterval)
      clearTimeout(completeTimeout)
    }
  }, [])

  // Get course display name
  const courseNames = {
    math124: 'Math 124',
    math125: 'Math 125',
    math126: 'Math 126',
  }
  const courseName = courseNames[selections?.course] || 'Calculus'

  // Get problem count based on course
  const problemCounts = {
    math124: 189,
    math125: 234,
    math126: 247,
  }
  const problemCount = problemCounts[selections?.course] || 247

  return (
    <motion.div
      custom={direction}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="w-full max-w-md mx-auto text-center px-4"
    >
      <AnimatePresence mode="wait">
        {!isComplete ? (
          <motion.div
            key="analyzing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {/* Animated icon */}
            <motion.div
              className="w-24 h-24 mx-auto mb-8 bg-gradient-to-br from-[#58cc02] to-[#46a302] rounded-2xl flex items-center justify-center shadow-lg"
              animate={{
                scale: [1, 1.05, 1],
                rotate: [0, 3, -3, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <motion.span
                className="text-4xl"
                key={currentAnalysis}
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 300 }}
              >
                {analysisSteps[currentAnalysis].icon}
              </motion.span>
            </motion.div>

            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Preparing {courseName}...
            </h2>

            {/* Current step text */}
            <motion.p
              key={currentAnalysis}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-gray-500 mb-8"
            >
              {analysisSteps[currentAnalysis].text}
            </motion.p>

            {/* Progress bar */}
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-4">
              <motion.div
                className="h-full bg-[#58cc02] rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ ease: 'linear' }}
              />
            </div>

            <p className="text-sm text-gray-400">
              Scanning 10+ years of midterms and finals
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="complete"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            {/* Success icon */}
            <motion.div
              className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-[#58cc02] to-[#46a302] rounded-2xl flex items-center justify-center shadow-lg"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 300, delay: 0.1 }}
            >
              <svg
                className="w-12 h-12 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={3}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </motion.div>

            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              You're all set! 🎉
            </h2>

            <p className="text-gray-500 mb-6">
              We found <span className="font-bold text-[#58cc02]">{problemCount} problems</span> from past exams
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8 p-4 bg-gray-50 rounded-2xl">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">12</div>
                <div className="text-xs text-gray-500">Years</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">8</div>
                <div className="text-xs text-gray-500">Topics</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[#58cc02]">AI</div>
                <div className="text-xs text-gray-500">Tutor</div>
              </div>
            </div>

            <SquishyButton onClick={onNext} className="w-full text-lg">
              START FREE EVALUATION
            </SquishyButton>

            <p className="mt-4 text-xs text-gray-400">
              5 free problems • No credit card required
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default AnalyzingScreen
