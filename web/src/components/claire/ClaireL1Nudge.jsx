/**
 * ClaireL1Nudge - Light Intervention Component
 *
 * A small, inline prompt that appears when Claire notices the student
 * might be stuck. NOT a full teaching card - just a gentle nudge.
 *
 * Characteristics:
 * - Compact, doesn't dominate the page
 * - Single question + input
 * - Optional quick reply chips
 * - Feels like "teacher glancing over" not "entering tutoring mode"
 */
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import MathText from '../ui/MathText'

export default function ClaireL1Nudge({
  question,
  quickReplies = [],
  onRespond,
  onDismiss,
  onEscalate, // User wants more help → go to L2
  loading = false,
}) {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef(null)

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (inputValue.trim()) {
      onRespond?.(inputValue.trim())
      setInputValue('')
    }
  }

  const handleQuickReply = (reply) => {
    onRespond?.(reply)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === 'Escape') {
      onDismiss?.()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className="mt-4 bg-white rounded-xl border border-[var(--claire-ai)] shadow-sm overflow-hidden"
    >
      {/* Compact header */}
      <div className="px-4 py-2.5 bg-[var(--claire-ai-bg)] border-b border-[var(--claire-ai)]/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-[var(--claire-ai)] flex items-center justify-center">
            <span className="text-white text-xs font-bold">C</span>
          </div>
          <span className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide">
            Claire
          </span>
        </div>
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600 transition-colors p-1"
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Question - compact */}
      <div className="px-4 py-3">
        {loading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 bg-[var(--claire-ai)] rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <span className="text-sm">Thinking...</span>
          </div>
        ) : (
          <p className="text-[var(--claire-navy)] text-sm leading-relaxed">
            <MathText text={question} />
          </p>
        )}
      </div>

      {/* Quick replies - if provided */}
      {!loading && quickReplies.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-1.5">
          {quickReplies.map((reply, i) => (
            <button
              key={i}
              onClick={() => handleQuickReply(reply)}
              className="px-2.5 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-[var(--claire-ai-bg)] hover:text-[var(--claire-navy)] transition-colors"
            >
              <MathText text={reply} />
            </button>
          ))}
        </div>
      )}

      {/* Compact input */}
      {!loading && (
        <form onSubmit={handleSubmit} className="px-4 pb-3">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your answer..."
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-[var(--claire-ai)] focus:border-[var(--claire-ai)]"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-3 py-2 text-sm font-medium bg-[var(--claire-navy)] text-white rounded-lg disabled:opacity-40 hover:opacity-90 transition-opacity"
            >
              Send
            </button>
          </div>
        </form>
      )}

      {/* Escalate to L2 option */}
      {!loading && onEscalate && (
        <div className="px-4 pb-3 border-t border-gray-100 pt-2">
          <button
            onClick={onEscalate}
            className="text-xs text-gray-400 hover:text-[var(--claire-ai)] transition-colors"
          >
            I need more help →
          </button>
        </div>
      )}
    </motion.div>
  )
}
