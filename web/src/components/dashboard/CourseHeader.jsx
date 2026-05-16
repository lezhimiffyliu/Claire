import { motion } from 'framer-motion'

/**
 * CourseHeader - Course info display
 *
 * Design principles (v3):
 * - Clean, minimal header
 * - No internal terminology ("Tier X")
 * - Restrained urgency indicators
 */
export default function CourseHeader({
  courseName,
  examType,
  focusTopics,
  daysUntilExam,
  onChangeCourse,
}) {
  // Urgency styling - restrained
  const getUrgencyStyle = () => {
    if (daysUntilExam <= 7) {
      return {
        color: 'var(--claire-weak)',
        bg: 'var(--claire-weak-bg)',
      }
    } else if (daysUntilExam <= 14) {
      return {
        color: 'var(--claire-info)',
        bg: 'var(--claire-info-bg)',
      }
    }
    return {
      color: 'var(--claire-text-secondary)',
      bg: 'var(--claire-bg)',
    }
  }

  const urgency = getUrgencyStyle()

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="card-standard"
    >
      <div className="flex items-start justify-between">
        {/* Left: Course info */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-xl font-semibold text-[var(--claire-text-primary)]">
              {courseName} {examType}
            </h1>
            <span
              className="status-label"
              style={{ color: urgency.color, background: urgency.bg }}
            >
              {daysUntilExam} days
            </span>
          </div>

          {focusTopics && focusTopics.length > 0 && (
            <div className="flex items-center gap-2 text-[var(--claire-text-secondary)]">
              <span className="text-sm">Focus:</span>
              <div className="flex flex-wrap gap-1.5">
                {focusTopics.map((topic, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 bg-[var(--claire-bg)] text-[var(--claire-text-secondary)] rounded text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Change button */}
        <button
          onClick={onChangeCourse}
          className="btn-link flex items-center gap-1.5"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.75}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
            />
          </svg>
          Change
        </button>
      </div>
    </motion.div>
  )
}
