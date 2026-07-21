/**
 * ClaireSayBubble - Displays a "say" event from Claire
 *
 * Shows a brief message with tone-based styling.
 * Appears above the problem area.
 */
import { motion } from 'framer-motion'
import MathText from '../ui/MathText'

const TONE_STYLES = {
  neutral: { border: 'var(--claire-gray-400)', bg: 'var(--claire-gray-50)' },
  encouraging: { border: 'var(--claire-teal)', bg: 'var(--claire-teal-muted)' },
  playful: { border: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' },
  concerned: { border: 'var(--claire-warning)', bg: 'var(--claire-warning-bg)' },
  firm: { border: 'var(--claire-navy)', bg: 'rgba(11, 31, 58, 0.05)' },
}

export default function ClaireSayBubble({ text, tone = 'neutral', onDismiss }) {
  const style = TONE_STYLES[tone] || TONE_STYLES.neutral

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="mb-4 flex items-start gap-2 px-3 py-2 rounded-lg"
      style={{
        backgroundColor: style.bg,
        borderLeft: `3px solid ${style.border}`
      }}
    >
      <span
        className="text-xs font-semibold uppercase tracking-wide flex-shrink-0"
        style={{ color: style.border }}
      >
        Claire:
      </span>
      <span className="text-sm text-[var(--claire-gray-700)] flex-1">
        <MathText text={text} />
      </span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600 text-sm leading-none"
          aria-label="Dismiss"
        >
          x
        </button>
      )}
    </motion.div>
  )
}
