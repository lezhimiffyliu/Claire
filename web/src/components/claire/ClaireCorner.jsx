/**
 * ClaireCorner - Always-on teacher presence (L1 surface)
 *
 * A small persona pinned to the bottom-right corner of the page (chat-head
 * style, like a Snapchat/Instagram DM bubble). It is always present so the
 * student feels the teacher is nearby, but it stays quiet and peripheral.
 *
 * - Collapsed: just the avatar. A teal dot signals an unseen message.
 * - Expanded: a speech bubble above the avatar with Claire's message,
 *   optional quick replies, a text input, and an "I need more help" link
 *   that escalates to L2 teaching mode.
 *
 * The bubble auto-opens when a new message arrives (so replies aren't missed)
 * and when `autoOpen` flips true (e.g. an idle nudge fired). The student can
 * always minimize it back to the avatar.
 */
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import MathText from '../ui/MathText'

export default function ClaireCorner({
  message = '',
  quickReplies = [],
  loading = false,
  autoOpen = false,
  placeholder = 'Let me take a look at this one…',
  onOpen,
  onRespond,
  onEscalate,
}) {
  const [expanded, setExpanded] = useState(false)
  const [hasUnseen, setHasUnseen] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef(null)
  const lastMessageRef = useRef(message)

  // Auto-open when a new (non-empty) message arrives so the student sees the reply.
  useEffect(() => {
    if (message && message !== lastMessageRef.current) {
      lastMessageRef.current = message
      setExpanded(true)
    }
  }, [message])

  // Auto-open on an external nudge (e.g. idle peek) — also asks the parent
  // to fetch an L1 nudge so the bubble leads with real teaching content.
  useEffect(() => {
    if (autoOpen) {
      setExpanded(true)
      onOpen?.()
    }
  }, [autoOpen]) // eslint-disable-line react-hooks/exhaustive-deps

  // Clear the unseen dot and focus the input whenever the bubble opens.
  useEffect(() => {
    if (expanded) {
      setHasUnseen(false)
      inputRef.current?.focus()
    } else if (loading) {
      // A reply is on the way while collapsed — flag it.
      setHasUnseen(true)
    }
  }, [expanded, loading])

  const submit = (text) => {
    const value = (text ?? inputValue).trim()
    if (!value) return
    onRespond?.(value)
    setInputValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
    if (e.key === 'Escape') setExpanded(false)
  }

  const chips = quickReplies

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2">
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.96 }}
            transition={{ duration: 0.18 }}
            className="w-80 max-w-[calc(100vw-2.5rem)] bg-white rounded-2xl border border-[var(--claire-ai)]/30 shadow-xl overflow-hidden"
          >
            {/* Header */}
            <div className="px-4 py-2.5 bg-[var(--claire-ai-bg)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-[var(--claire-ai)] flex items-center justify-center">
                  <span className="text-white text-xs font-bold">C</span>
                </div>
                <span className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide">
                  Claire
                </span>
              </div>
              <button
                onClick={() => setExpanded(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1"
                aria-label="Minimize"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            {/* Message */}
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
              ) : message ? (
                <p className="text-[var(--claire-navy)] text-sm leading-relaxed whitespace-pre-line">
                  <MathText text={message} />
                </p>
              ) : (
                <p className="text-gray-400 text-sm italic leading-relaxed">
                  {placeholder}
                </p>
              )}
            </div>

            {/* Quick replies / starter chips */}
            {!loading && chips.length > 0 && (
              <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                {chips.map((reply, i) => (
                  <button
                    key={i}
                    onClick={() => submit(reply)}
                    className="px-2.5 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-[var(--claire-ai-bg)] hover:text-[var(--claire-navy)] transition-colors"
                  >
                    <MathText text={reply} />
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            {!loading && (
              <form
                onSubmit={(e) => { e.preventDefault(); submit() }}
                className="px-4 pb-3"
              >
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

            {/* Escalate to L2 */}
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
        )}
      </AnimatePresence>

      {/* Avatar */}
      <button
        onClick={() => setExpanded(v => {
          const next = !v
          if (next) onOpen?.()
          return next
        })}
        className="relative w-14 h-14 rounded-full bg-[var(--claire-navy)] shadow-lg flex items-center justify-center hover:scale-105 transition-transform"
        aria-label="Claire tutor"
      >
        <span className="text-white text-xl font-bold">C</span>
        {hasUnseen && !expanded && (
          <span className="absolute top-0 right-0 w-3.5 h-3.5 bg-[var(--claire-teal)] rounded-full border-2 border-white" />
        )}
      </button>
    </div>
  )
}
