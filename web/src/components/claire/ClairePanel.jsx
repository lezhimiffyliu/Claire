import { motion, AnimatePresence } from 'framer-motion'
import { useClaire, CLAIRE_STATE } from '../../context/ClaireContext'

/**
 * ClairePanel - A subtle auxiliary guidance component
 *
 * Appears in the bottom-right corner as a small, unobtrusive hint.
 * This is NOT the main entry point - just supplementary context.
 * The main Claire interaction is via ClaireCoachCard on the Path page.
 */
export default function ClairePanel() {
  const { state, message, isVisible } = useClaire()

  // Only show in certain states, not on path page where coach card is primary
  const shouldShow = isVisible && state !== CLAIRE_STATE.IDLE

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 0.85, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          transition={{ duration: 0.15 }}
          className="fixed bottom-4 right-4 z-30 pointer-events-none"
        >
          <div
            className="bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-[var(--claire-gray-200)] px-3 py-2 max-w-[200px]"
          >
            <p className="text-xs text-[var(--claire-gray-500)] leading-relaxed">
              <span className="font-medium text-[var(--claire-gray-600)]">Claire:</span>{' '}
              {message}
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
