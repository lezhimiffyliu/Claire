import { motion } from 'framer-motion'

/**
 * TodayTaskCard - The hero component of the dashboard
 *
 * Design: Brilliant.org meets Notion
 * - Vibrant green CTA with lift effect
 * - Emotional motivation line based on user state
 * - Achievement preview showing what completion unlocks
 * - Quick entry links at bottom
 */

// Generate motivational message based on user state
function getMotivation({ daysUntilExam, streak, weakTopic, task }) {
  // Priority 1: Streak continuation
  if (streak >= 5) {
    return `${streak} days in a row. Don't break the chain.`
  }

  // Priority 2: Weak spot breakthrough
  if (weakTopic) {
    return `You struggled with ${weakTopic} last time. Let's fix that today.`
  }

  // Priority 3: Exam countdown
  if (daysUntilExam <= 3) {
    return `${daysUntilExam} days left. Every minute counts.`
  }
  if (daysUntilExam <= 7) {
    return `${daysUntilExam} days left. Today's practice could mean 5 extra points.`
  }
  if (daysUntilExam <= 14) {
    return `${daysUntilExam} days left. 15 minutes today gets you closer to 90%.`
  }

  // Default: Task-based
  if (task?.isWeak) {
    return `Time to conquer your weak spot. You've got this.`
  }

  return `Stay consistent. A little progress every day.`
}

// Flame icon with pulse
function FlameIcon({ className = '', animate = false }) {
  return (
    <svg
      className={`${className} ${animate ? 'animate-fire-pulse' : ''}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"
      />
    </svg>
  )
}

// Trophy icon for achievement
function TrophyIcon({ className = '' }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-4.5A3.75 3.75 0 0019.5 10.5h.75a.75.75 0 00.75-.75V6a.75.75 0 00-.75-.75h-.75A3.75 3.75 0 0016.5 9v.75m-9 9v-4.5A3.75 3.75 0 004.5 10.5h-.75a.75.75 0 01-.75-.75V6a.75.75 0 01.75-.75h.75A3.75 3.75 0 007.5 9v.75m9 9h-9" />
    </svg>
  )
}

export default function TodayTaskCard({
  dailyMinutes,
  task,
  hasDiagnostic,
  todayCompleted,
  todayStats,
  onStart,
  onStartDiagnostic,
  onExtraProblems,
  onViewLastSession,
  onViewWeekReview,
  courseName,
  daysUntilExam = 14,
  streak = 0,
  weakTopic = null,
}) {
  const motivation = getMotivation({ daysUntilExam, streak, weakTopic, task })
  const nextStreak = streak + 1

  // State 1: No diagnostic - show onboarding prompt
  if (!hasDiagnostic) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="card-hero"
      >
        <div className="text-section mb-4">{courseName}</div>

        <h1 className="text-hero mb-3">
          Find your weak spots
        </h1>
        <p className="text-motivation mb-6 max-w-md">
          Take a quick diagnostic to discover what you need to focus on. It only takes about 5 minutes.
        </p>

        <button onClick={onStartDiagnostic} className="btn-hero">
          Start Diagnostic
          <span className="btn-hero-subtitle">4 questions, ~5 min</span>
        </button>
      </motion.div>
    )
  }

  // State 3: Today completed
  if (todayCompleted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="card-hero"
      >
        <div className="text-section mb-4">{courseName}</div>

        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-[var(--claire-success-bg)] flex items-center justify-center">
            <svg className="w-5 h-5 text-[var(--claire-success)]" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-hero">Done for today</h1>
        </div>

        <div className="bg-[var(--claire-bg-warm)] rounded-xl p-5 mb-6">
          <div className="flex items-center gap-8">
            <div>
              <div className="text-2xl font-semibold text-[var(--claire-text-primary)] animate-count-up">
                {todayStats.problems}
              </div>
              <div className="text-sm text-[var(--claire-text-secondary)]">problems</div>
            </div>
            <div className="w-px h-10 bg-[var(--claire-border)]" />
            <div>
              <div className="text-2xl font-semibold text-[var(--claire-text-primary)] animate-count-up">
                {todayStats.correct > 0 && todayStats.problems > 0
                  ? `${Math.round((todayStats.correct / todayStats.problems) * 100)}%`
                  : '-'}
              </div>
              <div className="text-sm text-[var(--claire-text-secondary)]">accuracy</div>
            </div>
            {streak > 0 && (
              <>
                <div className="w-px h-10 bg-[var(--claire-border)]" />
                <div>
                  <div className="text-2xl font-semibold text-[var(--claire-fire)] flex items-center gap-1 animate-count-up">
                    <FlameIcon className="w-5 h-5" />
                    {streak}
                  </div>
                  <div className="text-sm text-[var(--claire-text-secondary)]">day streak</div>
                </div>
              </>
            )}
          </div>
        </div>

        <button onClick={onExtraProblems} className="btn-secondary-v3">
          Want more practice?
        </button>
      </motion.div>
    )
  }

  // State 2: Normal - show today's task
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="card-hero"
    >
      <div className="text-section mb-4">{courseName}</div>

      {/* Main title */}
      <h1 className="text-hero mb-2">
        Today · {dailyMinutes} min
      </h1>

      {/* Motivational line */}
      <p className="text-motivation mb-5">
        {motivation}
      </p>

      {/* Task info */}
      {task && (
        <div className="flex items-center gap-3 mb-6">
          <span className="text-[var(--claire-text-primary)] font-medium">
            {task.problemCount} {task.topic} {task.problemCount === 1 ? 'problem' : 'problems'}
          </span>
          {task.hasReview && (
            <span className="text-[var(--claire-text-secondary)]">+ review</span>
          )}
          {task.isWeak && (
            <span className="status-label weak">Weak spot</span>
          )}
        </div>
      )}

      {/* Primary CTA */}
      <button
        onClick={onStart}
        className="btn-hero"
        disabled={!task || task.problemCount === 0}
      >
        Start today's practice
        <span className="btn-hero-subtitle">
          {task ? `${task.problemCount} problems, ~${dailyMinutes} min` : 'Get your practice ready'}
        </span>
      </button>

      {/* Achievement preview */}
      {streak >= 0 && (
        <div className="achievement-preview mt-6">
          <div className="icon">
            {streak >= 6 ? <TrophyIcon className="w-[18px] h-[18px] text-[var(--claire-fire)]" /> : <FlameIcon className="w-[18px] h-[18px] text-[var(--claire-fire)]" animate />}
          </div>
          <div>
            <span className="text-[var(--claire-text-primary)]">Complete today</span>
            <span className="mx-1">→</span>
            <span className="font-medium text-[var(--claire-text-primary)]">{nextStreak} day streak</span>
            {nextStreak === 7 && <span className="text-[var(--claire-fire)]">, unlock Week Champion</span>}
            {nextStreak === 14 && <span className="text-[var(--claire-fire)]">, unlock Fortnight Legend</span>}
            {nextStreak === 30 && <span className="text-[var(--claire-fire)]">, unlock Monthly Master</span>}
          </div>
        </div>
      )}

      {/* Quick entry links */}
      <div className="flex gap-3 mt-6 pt-5 border-t border-[var(--claire-border-light)]">
        <button onClick={onViewLastSession} className="quick-entry flex-1">
          <svg fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Last session
        </button>
        <button onClick={onViewWeekReview} className="quick-entry flex-1">
          <svg fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Week review
        </button>
      </div>
    </motion.div>
  )
}
