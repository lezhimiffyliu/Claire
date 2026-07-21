/**
 * TutorThread - Renders the conversation thread between student and Claire
 *
 * Event types:
 * - { role: "claire", text: string, quickReplies?: string[] }
 * - { role: "user", text: string }
 * - { role: "user", imageUrl: string }
 * - { role: "claire", feedback: StepFeedback[] }  // future
 */
import { motion, AnimatePresence } from 'framer-motion'
import MathText from '../ui/MathText'

export default function TutorThread({ events = [], onQuickReply }) {
  if (events.length === 0) return null

  return (
    <div className="space-y-3">
      <AnimatePresence mode="popLayout">
        {events.map((event, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {event.role === 'user' ? (
              <UserBubble event={event} />
            ) : (
              <ClaireBubble event={event} onQuickReply={onQuickReply} />
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

/**
 * UserBubble - Student's message (text or image)
 */
function UserBubble({ event }) {
  const { text, imageUrl } = event

  return (
    <div className="flex justify-end">
      <div className="bg-[var(--claire-navy)] text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[80%]">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt="Your work"
            className="rounded-lg max-w-full"
          />
        ) : (
          <p className="text-sm">{text}</p>
        )}
      </div>
    </div>
  )
}

/**
 * ClaireBubble - Claire's message with optional quick replies
 * Uses ClaireAskBack-style card when quickReplies are present
 */
function ClaireBubble({ event, onQuickReply }) {
  const { text, quickReplies } = event

  // If has quickReplies, use card style (like ClaireAskBack)
  if (quickReplies && quickReplies.length > 0) {
    return (
      <div>
        <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
          Claire asks
        </p>
        <div className="text-lg text-[var(--claire-navy)] mb-4">
          <MathText text={text} />
        </div>
        <div className="flex flex-wrap gap-2">
          {quickReplies.map((reply, i) => (
            <button
              key={i}
              onClick={() => onQuickReply?.(reply)}
              className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
            >
              <MathText text={reply} />
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Simple text message
  return (
    <div className="flex items-start gap-2">
      <span className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide flex-shrink-0 pt-0.5">
        Claire:
      </span>
      <div className="text-sm text-[var(--claire-gray-700)]">
        <MathText text={text} />
      </div>
    </div>
  )
}
