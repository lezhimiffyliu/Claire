/**
 * ClaireConceptCard - Displays a "concept_card" event from Claire
 *
 * Shows a structured concept explanation with:
 * - Title and one-liner
 * - Explanation
 * - Example
 * - Connection to current problem
 *
 * Appears in the sidebar.
 */
import { motion } from 'framer-motion'
import MathText from '../ui/MathText'

export default function ClaireConceptCard({ card, onDismiss }) {
  const { title, one_liner, explanation, example, connect_to_current } = card

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="bg-white rounded-xl border border-[var(--claire-teal)] shadow-sm overflow-hidden"
    >
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-bold text-[var(--claire-navy)]">{title}</h4>
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-gray-600 text-sm leading-none"
            aria-label="Dismiss"
          >
            x
          </button>
        </div>

        {one_liner && (
          <p className="text-sm italic text-[var(--claire-gray-500)] mb-3">
            <MathText text={one_liner} />
          </p>
        )}

        {explanation && (
          <div className="text-sm text-[var(--claire-gray-700)] mb-3 leading-relaxed">
            <MathText text={explanation} />
          </div>
        )}

        {example && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-[var(--claire-gray-400)] uppercase tracking-wide mb-1">
              Example
            </p>
            <div className="text-sm text-[var(--claire-gray-700)] bg-gray-50 p-2 rounded">
              <MathText text={example} />
            </div>
          </div>
        )}

        {connect_to_current && (
          <div className="pt-3 border-t border-gray-100">
            <p className="text-xs font-semibold text-[var(--claire-teal)] uppercase tracking-wide mb-1">
              How this helps
            </p>
            <div className="text-sm text-[var(--claire-gray-600)]">
              <MathText text={connect_to_current} />
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
