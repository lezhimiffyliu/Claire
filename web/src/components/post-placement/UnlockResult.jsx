import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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

function UnlockResult({ testState, onNext }) {
  const [unlocked, setUnlocked] = useState(false)
  const analysis = testState.analysis || {}
  const { skillLevel, skillEmoji, skillColor } = analysis

  useEffect(() => {
    const timer = setTimeout(() => setUnlocked(true), 600)
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
      <div className="w-full max-w-md mx-auto text-center">
        {/* Lock animation */}
        <div className="relative w-32 h-32 mx-auto mb-6">
          <AnimatePresence mode="wait">
            {!unlocked ? (
              <motion.div
                key="locked"
                className="absolute inset-0 flex items-center justify-center"
                initial={{ scale: 1 }}
                exit={{ scale: 0.8, opacity: 0, rotate: -10 }}
                transition={{ duration: 0.3 }}
              >
                <div className="w-24 h-24 bg-gray-200 rounded-2xl flex items-center justify-center shadow-lg">
                  <svg
                    className="w-12 h-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="unlocked"
                className="absolute inset-0 flex items-center justify-center"
                initial={{ scale: 0, rotate: -30 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 400, damping: 15 }}
              >
                <div
                  className="w-28 h-28 rounded-2xl flex items-center justify-center shadow-xl"
                  style={{ backgroundColor: skillColor || '#58cc02' }}
                >
                  <span className="text-5xl">{skillEmoji || '📈'}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Sparkles on unlock */}
          {unlocked && (
            <>
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: ['#58cc02', '#1cb0f6', '#ff9600', '#ce82ff'][i % 4],
                    top: '50%',
                    left: '50%',
                  }}
                  initial={{ x: 0, y: 0, scale: 0 }}
                  animate={{
                    x: Math.cos((i * Math.PI) / 3) * 60,
                    y: Math.sin((i * Math.PI) / 3) * 60,
                    scale: [0, 1, 0],
                  }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                />
              ))}
            </>
          )}
        </div>

        <motion.p
          className="text-gray-500 mb-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          We found your fastest path to points.
        </motion.p>

        <AnimatePresence>
          {unlocked && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
            >
              <h1
                className="text-3xl font-bold mb-8"
                style={{ color: skillColor || '#1cb0f6' }}
              >
                {skillLevel || 'Exam Ready'}
              </h1>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: unlocked ? 1 : 0, y: unlocked ? 0 : 20 }}
          transition={{ delay: 0.5 }}
        >
          <SquishyButton onClick={onNext} className="w-full" disabled={!unlocked}>
            CONTINUE
          </SquishyButton>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default UnlockResult
