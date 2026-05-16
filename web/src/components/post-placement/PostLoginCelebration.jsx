import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import SquishyButton from '../ui/SquishyButton'
import ConfettiLite from './shared/ConfettiLite'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
}

function PostLoginCelebration({ onNext }) {
  const [showConfetti, setShowConfetti] = useState(false)

  useEffect(() => {
    // Trigger confetti after component mounts
    const timer = setTimeout(() => setShowConfetti(true), 200)
    return () => clearTimeout(timer)
  }, [])

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex items-center justify-center px-4"
    >
      <ConfettiLite trigger={showConfetti} particleCount={40} />

      <div className="w-full max-w-md mx-auto text-center">
        {/* Celebration animation */}
        <motion.div
          className="relative w-32 h-32 mx-auto mb-6"
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 15, delay: 0.2 }}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-[#58cc02] to-[#46a302] rounded-full flex items-center justify-center shadow-xl">
            <motion.span
              className="text-6xl"
              animate={{
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 0.5,
                delay: 0.5,
                times: [0, 0.5, 1],
              }}
            >
              🎉
            </motion.span>
          </div>

          {/* Pulse rings */}
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-0 rounded-full border-4 border-[#58cc02]"
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 2, opacity: 0 }}
              transition={{
                duration: 1.5,
                delay: 0.3 + i * 0.3,
                repeat: Infinity,
                repeatDelay: 0.9,
              }}
            />
          ))}
        </motion.div>

        <motion.h1
          className="text-3xl font-bold text-gray-800 mb-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          You're ready to start.
        </motion.h1>

        <motion.p
          className="text-gray-500 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          Your personalized study plan is waiting
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <SquishyButton onClick={onNext} className="w-full text-lg">
            START FIRST PROBLEM
          </SquishyButton>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default PostLoginCelebration
