import { motion } from 'framer-motion'
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

function HeroScreen({ direction, onNext }) {
  return (
    <motion.div
      custom={direction}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="w-full max-w-md mx-auto text-center"
    >
      {/* Mascot placeholder */}
      <div className="w-48 h-48 mx-auto mb-8 bg-gradient-to-br from-[#58cc02] to-[#46a302] rounded-full flex items-center justify-center shadow-lg">
        <span className="text-7xl">📐</span>
      </div>

      {/* Headline */}
      <h1 className="text-4xl font-extrabold text-gray-800 mb-4">
        Master UW Calculus
      </h1>

      <p className="text-xl text-gray-500 mb-8">
        Learn from real past exams. <br />
        Practice with instant feedback.
      </p>

      {/* CTA Button */}
      <SquishyButton onClick={onNext} className="text-lg">
        GET STARTED
      </SquishyButton>

      {/* Social proof */}
      <p className="mt-8 text-sm text-gray-400">
        Join 1,000+ UW students who've improved their grades
      </p>
    </motion.div>
  )
}

export default HeroScreen
