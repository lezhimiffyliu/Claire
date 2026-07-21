/**
 * ClaireAskBack - Displays an "ask_back" event from Claire
 *
 * Shows a question with optional hint chips and an input field.
 * Replaces the submit area when active.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import MathText from '../ui/MathText'

export default function ClaireAskBack({ question, hints = [], onAnswer, onSkip }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim()) {
      onAnswer(input.trim())
      setInput('')
    }
  }

  const handleHintClick = (hint) => {
    onAnswer(hint)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="bg-white rounded-2xl border-2 border-[var(--claire-ai)] overflow-hidden"
    >
      <div className="p-6">
        <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
          Claire asks
        </p>
        <div className="text-lg text-[var(--claire-navy)] mb-4">
          <MathText text={question} />
        </div>

        {hints.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {hints.map((hint, i) => (
              <button
                key={i}
                onClick={() => handleHintClick(hint)}
                className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
              >
                {hint}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Or type your own answer..."
            className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--claire-ai)] focus:border-transparent"
          />
        </form>
      </div>

      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex justify-between">
        <button
          onClick={onSkip}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          Back to submit area
        </button>
        <button
          onClick={handleSubmit}
          disabled={!input.trim()}
          className="px-4 py-1.5 text-sm font-medium bg-[var(--claire-navy)] text-white rounded-lg disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </motion.div>
  )
}
