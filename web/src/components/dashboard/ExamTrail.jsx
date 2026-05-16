import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CHECKPOINT_STATUS,
  getCheckpointIcon,
} from '../../data/mockStudentProfile'

// Get status-based styling
function getNodeStyles(status) {
  switch (status) {
    case CHECKPOINT_STATUS.COMPLETED:
      return {
        dot: 'bg-[var(--claire-teal)] text-white',
        border: 'border-[var(--claire-teal)]',
        bg: 'bg-[var(--claire-teal-muted)]',
      }
    case CHECKPOINT_STATUS.RECOMMENDED:
      return {
        dot: 'bg-[var(--claire-next)] text-white ring-4 ring-[var(--claire-next-bg)]',
        border: 'border-[var(--claire-next)]',
        bg: 'bg-[var(--claire-next-bg)]',
      }
    case CHECKPOINT_STATUS.IN_PROGRESS:
      return {
        dot: 'bg-[var(--claire-weak)] text-white',
        border: 'border-[var(--claire-weak)]',
        bg: 'bg-[var(--claire-weak-bg)]',
      }
    case CHECKPOINT_STATUS.AVAILABLE:
      return {
        dot: 'bg-[var(--claire-navy)] text-white',
        border: 'border-[var(--claire-gray-300)]',
        bg: 'bg-white hover:bg-[var(--claire-gray-50)]',
      }
    case CHECKPOINT_STATUS.LOCKED:
      return {
        dot: 'bg-[var(--claire-gray-200)] text-[var(--claire-gray-400)]',
        border: 'border-[var(--claire-gray-200)]',
        bg: 'bg-white',
      }
    default:
      return {
        dot: 'bg-[var(--claire-navy)] text-white',
        border: 'border-[var(--claire-gray-300)]',
        bg: 'bg-white',
      }
  }
}

function CheckpointNode({ checkpoint, isExpanded, onToggle, onStart }) {
  const icon = getCheckpointIcon(checkpoint.type)
  const styles = getNodeStyles(checkpoint.status)
  const isLocked = checkpoint.status === CHECKPOINT_STATUS.LOCKED
  const isRecommended = checkpoint.status === CHECKPOINT_STATUS.RECOMMENDED

  return (
    <div className="relative">
      {/* Connector line */}
      <div className="absolute left-[22px] top-12 bottom-0 w-0.5 bg-[var(--claire-gray-200)]" />

      {/* Node */}
      <motion.div
        layout
        className={`
          relative rounded-xl border-2 transition-all duration-150
          ${styles.border} ${styles.bg}
          ${isLocked ? 'opacity-50' : 'cursor-pointer'}
        `}
        onClick={() => !isLocked && onToggle()}
      >
        {/* Collapsed view */}
        <div className="flex items-center gap-4 p-4">
          {/* Status dot */}
          <div
            className={`
              w-11 h-11 rounded-full flex items-center justify-center text-xl
              ${styles.dot}
            `}
          >
            {checkpoint.status === CHECKPOINT_STATUS.COMPLETED ? (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={3}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : isLocked ? (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            ) : (
              <span>{icon}</span>
            )}
          </div>

          {/* Title & subtitle */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3
                className={`font-semibold ${
                  isLocked
                    ? 'text-[var(--claire-gray-400)]'
                    : 'text-[var(--claire-navy)]'
                }`}
              >
                {checkpoint.title}
              </h3>
              {isRecommended && (
                <span className="label-next">Start Here</span>
              )}
            </div>
            <p
              className={`text-sm ${
                isLocked
                  ? 'text-[var(--claire-gray-300)]'
                  : 'text-[var(--claire-gray-500)]'
              } line-clamp-1`}
            >
              {checkpoint.subtitle}
            </p>
          </div>

          {/* Expand indicator */}
          {!isLocked && (
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              className="text-[var(--claire-gray-400)]"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </motion.div>
          )}
        </div>

        {/* Expanded view */}
        <AnimatePresence>
          {isExpanded && !isLocked && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 pt-0 border-t border-[var(--claire-gray-200)] mt-2">
                {/* Why recommended */}
                <div className="bg-[var(--claire-gray-100)] rounded-lg p-4 mb-4 mt-4">
                  <h4 className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider mb-1">
                    Why this checkpoint
                  </h4>
                  <p className="text-sm text-[var(--claire-gray-700)]">
                    {checkpoint.reason}
                  </p>
                </div>

                {/* Stats row */}
                <div className="flex items-center gap-6 mb-4 text-sm text-[var(--claire-gray-500)]">
                  <div className="flex items-center gap-1.5">
                    <span>{checkpoint.problemCount} problems</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span>~{checkpoint.estimatedMinutes} min</span>
                  </div>
                </div>

                {/* Past exam sources */}
                {checkpoint.pastExamSources?.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-xs font-semibold text-[var(--claire-gray-400)] uppercase tracking-wider mb-2">
                      From real UW exams
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {checkpoint.pastExamSources.map((source, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-[var(--claire-gray-100)] text-[var(--claire-gray-600)] rounded text-xs"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Start button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onStart(checkpoint)
                  }}
                  className="btn-secondary w-full"
                >
                  Start checkpoint
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

export default function ExamTrail({ checkpoints, onStartCheckpoint }) {
  const [expandedId, setExpandedId] = useState(null)

  const handleToggle = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const completedCount = checkpoints.filter(
    (c) => c.status === CHECKPOINT_STATUS.COMPLETED
  ).length

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold text-[var(--claire-navy)]">
          Your Path
        </h2>
        <span className="text-sm text-[var(--claire-gray-400)]">
          {completedCount}/{checkpoints.length} done
        </span>
      </div>

      <div className="space-y-3">
        {checkpoints.map((checkpoint) => (
          <CheckpointNode
            key={checkpoint.id}
            checkpoint={checkpoint}
            isExpanded={expandedId === checkpoint.id}
            onToggle={() => handleToggle(checkpoint.id)}
            onStart={onStartCheckpoint}
          />
        ))}
      </div>
    </div>
  )
}
