/**
 * ClaireIdleNudge - Low-profile nudge card when student is idle
 *
 * Appears at the top after 2 minutes of inactivity.
 * Shows a guiding question with quick reply chips.
 * Dismissible with an X button.
 */
import { motion } from 'framer-motion'
import MathText from '../ui/MathText'

export default function ClaireIdleNudge({ question, hints = [], onAnswer, onDismiss }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="mb-4 rounded-lg overflow-hidden"
      style={{
        backgroundColor: 'rgba(107, 159, 232, 0.08)',
        borderLeft: '3px solid var(--claire-ai)'
      }}
    >
      <div className="px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <span className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide">
              Claire:
            </span>
            <span className="ml-2 text-sm text-[var(--claire-gray-700)]">
              <MathText text={question} />
            </span>
          </div>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600 text-sm leading-none p-1"
              aria-label="Dismiss"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {hints.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {hints.map((hint, i) => (
              <button
                key={i}
                onClick={() => onAnswer?.(hint)}
                className="px-3 py-1.5 text-xs bg-white border border-gray-200 text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-ai-bg)] hover:border-[var(--claire-ai)] transition-colors"
              >
                <MathText text={hint} />
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}
