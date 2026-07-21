/**
 * ClaireL0Strip - Lightweight observation strip for L0 Ambient Presence
 *
 * Shows a pre-authored observation about the problem - like a teacher
 * glancing at the question and noting something helpful, NOT starting a dialogue.
 *
 * Observations are loaded from tutorAssets/l0Observations.js, keyed by
 * problemId or partId. If no observation exists for the current problem,
 * this component renders nothing (page stays quiet).
 */
import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import MathText from '../ui/MathText'
import { getL0Observation } from '../../data/tutorAssets/l0Observations'

export default function ClaireL0Strip({ problem, currentPart, onDismiss }) {
  const [dismissed, setDismissed] = useState(false)

  // Look up observation from tutor assets (partId first, then problemId)
  const observation = useMemo(() => {
    const problemId = problem?.id
    const partLabel = currentPart?.label
    return getL0Observation(problemId, partLabel)
  }, [problem?.id, currentPart?.label])

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss?.()
  }

  // Don't render if no observation exists for this problem/part
  if (!observation) return null

  return (
    <AnimatePresence>
      {!dismissed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="mb-3 flex items-center gap-2 px-3 py-1.5 rounded text-xs"
          style={{
            backgroundColor: 'rgba(47, 191, 159, 0.06)',
            borderLeft: '2px solid var(--claire-teal)'
          }}
        >
          <span
            className="font-semibold uppercase tracking-wide flex-shrink-0"
            style={{ color: 'var(--claire-teal)', fontSize: '10px' }}
          >
            Claire:
          </span>
          <span className="text-gray-600 flex-1">
            <MathText text={observation} />
          </span>
          <button
            onClick={handleDismiss}
            className="text-gray-300 hover:text-gray-500 leading-none ml-1"
            aria-label="Dismiss"
          >
            ×
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
