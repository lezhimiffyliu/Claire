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

function PlacementComplete({ testState, onNext }) {
  const analysis = testState.analysis || {}
  const { skillEmoji = '✅', skillLevel = 'Analyzed', levelDescription = '' } = analysis

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex items-center justify-center px-4"
    >
      <div className="w-full max-w-md mx-auto text-center">
        {/* Animated checkmark */}
        <motion.div
          className="w-24 h-24 mx-auto mb-6 relative"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 15, delay: 0.1 }}
        >
          <div className="absolute inset-0 bg-[#58cc02] rounded-full flex items-center justify-center shadow-lg">
            <motion.svg
              className="w-12 h-12 text-white"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={3}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <motion.path
                d="M5 12l5 5L19 7"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              />
            </motion.svg>
          </div>
          {/* Pulse ring */}
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-[#58cc02]"
            initial={{ scale: 1, opacity: 0.6 }}
            animate={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 1, repeat: 2 }}
          />
        </motion.div>

        <motion.h1
          className="text-3xl font-bold text-gray-800 mb-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          Placement complete!
        </motion.h1>

        <motion.p
          className="text-gray-500 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          We've analyzed your calculus skills
        </motion.p>

        {/* Skill level card */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <div className="bg-[#d7ffb8] border-2 border-[#58cc02] rounded-2xl p-6">
            <div className="text-4xl mb-2">{skillEmoji}</div>
            <div className="text-xl font-bold text-[#58cc02]">{skillLevel}</div>
            {levelDescription && (
              <div className="text-sm text-gray-600 mt-2">{levelDescription}</div>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <SquishyButton onClick={onNext} className="w-full">
            CONTINUE
          </SquishyButton>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default PlacementComplete
