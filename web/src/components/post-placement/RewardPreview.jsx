import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import SquishyButton from '../ui/SquishyButton'

// Real problem counts from /problems directory
const PROBLEM_STATS = {
  math124: { problems: 136, exams: 17 },
  math125: { problems: 299, exams: 30 },
  math126: { problems: 333, exams: 39 },
}

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
}

function AnimatedCounter({ value, delay = 0 }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const timeout = setTimeout(() => {
      const duration = 1000
      const steps = 20
      const stepValue = value / steps
      const stepDuration = duration / steps
      let current = 0

      const interval = setInterval(() => {
        current += stepValue
        if (current >= value) {
          setCount(value)
          clearInterval(interval)
        } else {
          setCount(Math.floor(current))
        }
      }, stepDuration)

      return () => clearInterval(interval)
    }, delay)

    return () => clearTimeout(timeout)
  }, [value, delay])

  return <span>{count}</span>
}

function RewardCard({ icon, value, label, color, delay }) {
  return (
    <motion.div
      className="bg-white border-2 rounded-2xl p-4 text-center"
      style={{ borderColor: color }}
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, type: 'spring', stiffness: 300, damping: 20 }}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold" style={{ color }}>
        <AnimatedCounter value={value} delay={delay * 1000} />
      </div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </motion.div>
  )
}

function RewardPreview({ testState, selections, onNext }) {
  const analysis = testState.analysis || {}
  const gapCount = analysis.gaps?.length || 2

  // Get real problem stats for the selected course
  const course = selections?.course || 'math126'
  const stats = PROBLEM_STATS[course] || PROBLEM_STATS.math126

  const rewards = [
    {
      icon: '📝',
      value: stats.problems,
      label: 'Past Exam problems',
      color: '#58cc02',
    },
    {
      icon: '📋',
      value: stats.exams,
      label: 'UW exams (2015-2025)',
      color: '#ff9600',
    },
    {
      icon: '✍️',
      value: 1,
      label: 'handwriting grader',
      color: '#1cb0f6',
    },
  ]

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
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', stiffness: 400 }}
          className="mb-2"
        >
          <span className="text-5xl">🎁</span>
        </motion.div>

        <motion.h1
          className="text-2xl font-bold text-gray-800 mb-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          Your first rescue plan is ready.
        </motion.h1>

        <motion.p
          className="text-gray-500 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Here's what we've prepared for you
        </motion.p>

        {/* Reward cards */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          {rewards.map((reward, index) => (
            <RewardCard key={index} {...reward} delay={0.4 + index * 0.15} />
          ))}
        </div>

        {/* Subtitle */}
        <motion.p
          className="text-sm text-gray-400 mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          Personalized based on your placement results
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
        >
          <SquishyButton onClick={onNext} className="w-full">
            CONTINUE
          </SquishyButton>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default RewardPreview
