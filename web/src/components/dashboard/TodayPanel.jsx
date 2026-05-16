import { motion } from 'framer-motion'

function TodayPlanSection({ plan, onToggleComplete }) {
  const totalMinutes = plan.reduce((sum, item) => sum + item.duration, 0)
  const completedMinutes = plan
    .filter((item) => item.completed)
    .reduce((sum, item) => sum + item.duration, 0)

  return (
    <div className="bg-[var(--claire-gray-50)] rounded-lg border border-[var(--claire-gray-100)] p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-medium text-[var(--claire-gray-400)] uppercase tracking-wide">Today</h3>
        <span className="text-[10px] text-[var(--claire-gray-300)]">
          {completedMinutes}/{totalMinutes} min
        </span>
      </div>

      <div className="space-y-1.5">
        {plan.map((item) => (
          <motion.button
            key={item.id}
            onClick={() => onToggleComplete(item.id)}
            className={`
              w-full flex items-center gap-2 p-2 rounded text-left text-xs
              transition-colors duration-150
              ${
                item.completed
                  ? 'bg-[var(--claire-teal-muted)]/50 text-[var(--claire-teal)]'
                  : 'hover:bg-[var(--claire-gray-100)] text-[var(--claire-gray-500)]'
              }
            `}
            whileTap={{ scale: 0.98 }}
          >
            {/* Checkbox */}
            <div
              className={`
                w-3.5 h-3.5 rounded-full border flex items-center justify-center flex-shrink-0
                ${
                  item.completed
                    ? 'bg-[var(--claire-teal)] border-[var(--claire-teal)]'
                    : 'border-[var(--claire-gray-300)]'
                }
              `}
            >
              {item.completed && (
                <svg
                  className="w-2 h-2 text-white"
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
              )}
            </div>

            {/* Content */}
            <span className={`flex-1 truncate ${item.completed ? 'line-through' : ''}`}>
              {item.title}
            </span>

            {/* Duration */}
            <span className="text-[10px] opacity-60">
              {item.duration}m
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  )
}

function PastExamAccessSection({ onOpenDrawer }) {
  return (
    <button
      onClick={onOpenDrawer}
      className="w-full flex items-center gap-2 p-2.5 rounded-lg text-left text-xs text-[var(--claire-gray-400)] hover:text-[var(--claire-gray-600)] hover:bg-[var(--claire-gray-50)] transition-colors"
    >
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
      <span>Browse past exams</span>
    </button>
  )
}

function WeakSpotsSection({ weakSpots }) {
  if (!weakSpots || weakSpots.length === 0) return null

  return (
    <div className="bg-white rounded-lg border border-[var(--claire-gray-200)] p-3">
      <h3 className="text-xs font-medium text-[var(--claire-gray-400)] uppercase tracking-wide mb-2">
        Your Gaps
      </h3>
      <div className="space-y-2">
        {weakSpots.slice(0, 3).map((spot, i) => (
          <div
            key={i}
            className="flex items-start gap-2 p-2 rounded bg-red-50 border-l-2 border-[var(--claire-weak)]"
          >
            <svg
              className="w-3.5 h-3.5 text-[var(--claire-weak)] mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[var(--claire-gray-700)] truncate">
                {spot.skill}
              </p>
              <p className="text-[10px] text-[var(--claire-gray-500)]">
                {spot.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function TodayPanel({
  todayPlan,
  weakSpots,
  onTogglePlanItem,
  onOpenQuestionBank,
}) {
  return (
    <aside className="w-full space-y-3">
      <TodayPlanSection plan={todayPlan} onToggleComplete={onTogglePlanItem} />
      <WeakSpotsSection weakSpots={weakSpots} />
      <PastExamAccessSection onOpenDrawer={onOpenQuestionBank} />
    </aside>
  )
}
