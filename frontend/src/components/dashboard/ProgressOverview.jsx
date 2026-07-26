import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'

/**
 * ProgressOverview - Secondary panel showing progress metrics
 *
 * Design: Brilliant.org warmth + professional restraint
 * - Urgency-colored exam countdown
 * - Gradient progress ring with count-up
 * - Trend indicators
 * - Weak spots with practice predictions
 */

// Progress ring with gradient
function ProgressRing({ percent, size = 72, strokeWidth = 6, animated = true }) {
  const [displayPercent, setDisplayPercent] = useState(animated ? 0 : percent)
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (displayPercent / 100) * circumference

  // Count-up animation
  useEffect(() => {
    if (!animated) {
      setDisplayPercent(percent)
      return
    }

    const duration = 800
    const startTime = Date.now()
    const startValue = 0

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayPercent(Math.round(startValue + (percent - startValue) * eased))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [percent, animated])

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* SVG with gradient definition */}
      <svg width={size} height={size} className="progress-ring">
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="100%" stopColor="#059669" />
          </linearGradient>
        </defs>
        <circle
          className="progress-ring-bg"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          fill="none"
          stroke="url(#progressGradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 100ms ease-out' }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-semibold text-[var(--claire-text-primary)]">
          {displayPercent}%
        </span>
      </div>
    </div>
  )
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

// Arrow up icon
function ArrowUpIcon({ className = '' }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
    </svg>
  )
}

export default function ProgressOverview({
  daysUntilExam,
  examSource = 'approximate',
  masteryPercent,
  masteredCount = 0,
  totalTopics = 30,
  weeklyGain = 0,
  weakSpots,
  streak,
  onViewWeakSpots,
  onPracticeWeakSpot,
}) {
  const isApproximate = examSource === 'approximate'
  // Urgency level
  const getUrgency = () => {
    if (daysUntilExam <= 7) return 'urgent'
    if (daysUntilExam <= 14) return 'warning'
    return 'safe'
  }
  const urgency = getUrgency()

  // Progress bar percentage (assuming 30-day prep)
  const examProgressPercent = Math.max(0, Math.min(100, 100 - (daysUntilExam / 30) * 100))

  // Mastery message
  const getMasteryMessage = () => {
    if (masteryPercent >= 80) return `Almost there — ${masteredCount} of ${totalTopics} concepts mastered`
    if (masteryPercent >= 50) return `You're ${masteryPercent}% there — ${masteredCount} of ${totalTopics} concepts mastered`
    if (masteryPercent >= 20) return `Building momentum — ${masteredCount} of ${totalTopics} concepts mastered`
    return `You're ${masteryPercent}% there — ${masteredCount} of ${totalTopics} concepts mastered`
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: 0.1, ease: 'easeOut' }}
      className="space-y-4"
    >
      {/* Days until exam - with urgency bar */}
      <div className="card-standard">
        <div className="text-section mb-3">Next Exam</div>

        <div className="flex items-baseline gap-2 mb-3">
          {isApproximate && (
            <span className="text-lg text-[var(--claire-text-muted)]">~</span>
          )}
          <span
            className={`text-3xl font-semibold ${
              urgency === 'urgent' ? 'text-[var(--claire-weak)]' :
              urgency === 'warning' ? 'text-[var(--claire-warning)]' :
              'text-[var(--claire-text-primary)]'
            }`}
          >
            D-{daysUntilExam}
          </span>
          {isApproximate && (
            <span className="text-xs text-[var(--claire-text-muted)]">approximate</span>
          )}
        </div>

        {/* Urgency progress bar */}
        <div className="progress-bar-urgency">
          <div
            className={`progress-bar-urgency-fill ${urgency}`}
            style={{ width: `${examProgressPercent}%` }}
          />
        </div>
      </div>

      {/* Mastery overview - with gradient ring */}
      <div className="card-standard">
        <div className="text-section mb-3">Mastery</div>

        <div className="flex items-center gap-4">
          <ProgressRing percent={masteryPercent} size={64} strokeWidth={5} />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-[var(--claire-text-secondary)] leading-snug">
              {getMasteryMessage()}
            </p>
            {/* Trend indicator */}
            {weeklyGain > 0 && (
              <div className="trend-up mt-2">
                <ArrowUpIcon className="w-3 h-3" />
                +{weeklyGain} this week
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Streak - with pulse animation */}
      {streak > 0 && (
        <div className="streak-badge w-full justify-center">
          <FlameIcon className="w-5 h-5" animate />
          <span className="font-semibold">{streak} day streak</span>
        </div>
      )}

      {/* Weak spots - with practice predictions */}
      {weakSpots && weakSpots.length > 0 && (
        <div className="card-standard">
          <div className="flex items-center justify-between mb-3">
            <div className="text-section">Weak Spots</div>
            <button onClick={onViewWeakSpots} className="btn-link text-xs">
              View all
            </button>
          </div>

          <div className="space-y-2">
            {weakSpots.slice(0, 3).map((spot, i) => (
              <button
                key={i}
                onClick={() => onPracticeWeakSpot?.(spot)}
                className="weak-spot-item w-full text-left"
              >
                <div className="status-dot weak mt-1" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-[var(--claire-text-primary)] truncate">
                    {spot.skill}
                  </div>
                  <div className="prediction">
                    {spot.practiceCount || 3} problems to master
                  </div>
                </div>
                <svg className="w-4 h-4 text-[var(--claire-text-muted)] flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* No diagnostic state */}
      {(!weakSpots || weakSpots.length === 0) && (
        <div className="card-subtle text-center py-3">
          <p className="text-sm text-[var(--claire-text-secondary)]">
            Complete the diagnostic to see weak spots
          </p>
        </div>
      )}
    </motion.div>
  )
}
