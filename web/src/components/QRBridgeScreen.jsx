import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import SquishyButton from './ui/SquishyButton'
import { TIER_INFO } from '../data/questionBanks'

// Study schedule recommendations based on urgency + skill level
const SCHEDULE_RECOMMENDATIONS = {
  critical: {
    '🌱 Building Foundations': {
      daily: '3-4 problems',
      focus: 'Core concepts + formula memorization',
      tip: 'Focus on T1-T2 problems only. Skip advanced topics.',
    },
    '📈 Exam Ready': {
      daily: '5-6 problems',
      focus: 'Exam-style problems + weak areas',
      tip: 'Practice full exam timing. Review mistakes immediately.',
    },
    '🏆 4.0 Candidate': {
      daily: '4-5 problems',
      focus: 'Challenge problems + edge cases',
      tip: "Focus on T4 conceptual depth. You've got this!",
    },
  },
  high: {
    '🌱 Building Foundations': {
      daily: '2-3 problems',
      focus: 'Build fundamentals systematically',
      tip: 'Spend 50% on T1-T2, 50% on T3 basics.',
    },
    '📈 Exam Ready': {
      daily: '3-4 problems',
      focus: 'UW exam patterns + timed practice',
      tip: 'Do 2 full practice exams this week.',
    },
    '🏆 4.0 Candidate': {
      daily: '3 problems',
      focus: 'Polish weak spots + review all tiers',
      tip: 'Focus on speed and accuracy, not new concepts.',
    },
  },
  moderate: {
    '🌱 Building Foundations': {
      daily: '1-2 problems',
      focus: 'Steady foundation building',
      tip: 'Master one topic before moving on.',
    },
    '📈 Exam Ready': {
      daily: '2 problems',
      focus: 'Mixed practice across all topics',
      tip: 'Alternate between computation and conceptual.',
    },
    '🏆 4.0 Candidate': {
      daily: '2 problems',
      focus: 'Deepen understanding + teach concepts',
      tip: 'Try explaining solutions to solidify mastery.',
    },
  },
  low: {
    '🌱 Building Foundations': {
      daily: '1 problem',
      focus: 'Long-term foundation building',
      tip: 'No rush. Build habits now for exam success.',
    },
    '📈 Exam Ready': {
      daily: '1-2 problems',
      focus: 'Explore advanced topics',
      tip: 'Great time to tackle challenging T4 problems.',
    },
    '🏆 4.0 Candidate': {
      daily: '1 problem',
      focus: 'Maintain and explore',
      tip: 'Help others learn to reinforce your mastery.',
    },
  },
}

function QRBridgeScreen({ testState, selections, onComplete }) {
  const [showQR, setShowQR] = useState(false)

  const courseNames = {
    math124: 'Math 124',
    math125: 'Math 125',
    math126: 'Math 126',
  }

  const timelineLabels = {
    urgent: '< 1 week',
    soon: '1-2 weeks',
    moderate: '2-4 weeks',
    relaxed: '1+ month',
  }

  // Use the pre-analyzed results
  const analysis = testState.analysis || {
    skillLevel: 'Analyzing...',
    skillEmoji: '📊',
    skillColor: '#1cb0f6',
    gaps: [],
    strengths: [],
    blockerMessage: '',
    passedCount: 0,
    totalCount: 4,
  }

  // Get schedule recommendation
  const urgency = selections.urgency || 'moderate'
  const schedule = SCHEDULE_RECOMMENDATIONS[urgency]?.[analysis.skillLevel] || {
    daily: '2 problems',
    focus: 'Mixed practice',
    tip: 'Consistent practice is key!',
  }

  // Calculate days until exam dynamically from stored target date
  const calculateDaysUntilExam = () => {
    if (selections.examTargetDate) {
      const target = new Date(selections.examTargetDate)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      target.setHours(0, 0, 0, 0)
      const diffTime = target - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return Math.max(0, diffDays)
    }
    return selections.daysUntilExam || '?'
  }
  const daysUntilExam = calculateDaysUntilExam()

  useEffect(() => {
    const timer = setTimeout(() => setShowQR(true), 600)
    return () => clearTimeout(timer)
  }, [])

  // Generate a session ID for the QR code
  const sessionId = Math.random().toString(36).substring(2, 8).toUpperCase()

  // Find the primary blocker
  const primaryGap = analysis.gaps[0]

  return (
    <motion.div
      className="flex-1 flex flex-col items-center px-4 py-6 overflow-y-auto"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="w-full max-w-md">
        {/* Skill Level Badge */}
        <motion.div
          className="text-center mb-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full mb-2 shadow-sm"
            style={{ backgroundColor: `${analysis.skillColor}15` }}
          >
            <span className="text-2xl">{analysis.skillEmoji}</span>
            <span className="font-bold text-lg" style={{ color: analysis.skillColor }}>
              {analysis.skillLevel}
            </span>
          </div>

          <h2 className="text-xl font-bold text-gray-800 mb-1">
            Your {courseNames[selections.course]} Profile
          </h2>

          <div className="flex items-center justify-center gap-3 text-sm text-gray-500">
            <span>{analysis.passedCount}/{analysis.totalCount} tiers</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <span>📆</span>
              {timelineLabels[selections.timeline] || 'TBD'}
            </span>
          </div>
        </motion.div>

        {/* Study Schedule Card */}
        <motion.div
          className="bg-gradient-to-br from-[#1cb0f6] to-[#0a8cd8] rounded-2xl p-4 mb-4 text-white"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">📋</span>
            <h3 className="font-bold">Your Study Plan</h3>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white/20 rounded-xl p-3 text-center">
              <div className="text-2xl font-bold">{schedule.daily}</div>
              <div className="text-xs opacity-80">per day</div>
            </div>
            <div className="bg-white/20 rounded-xl p-3 text-center">
              <div className="text-2xl font-bold">{daysUntilExam}</div>
              <div className="text-xs opacity-80">days left</div>
            </div>
          </div>

          <div className="bg-white/10 rounded-xl p-3">
            <div className="text-sm font-medium mb-1">Focus: {schedule.focus}</div>
            <div className="text-xs opacity-80">💡 {schedule.tip}</div>
          </div>
        </motion.div>

        {/* Knowledge Gap Map */}
        <motion.div
          className="bg-gray-50 rounded-2xl p-4 mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>📊</span> Skill Breakdown
          </h3>

          <div className="space-y-2">
            {[1, 2, 3, 4].map((tier) => {
              const tierInfo = TIER_INFO[tier]
              const tierResult = analysis.tierResults?.[tier]
              const passed = tierResult?.passed || false
              const question = tierResult?.question

              return (
                <motion.div
                  key={tier}
                  className="flex items-center gap-2"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + tier * 0.08 }}
                >
                  <div
                    className="w-12 shrink-0 text-xs font-bold py-1 px-2 rounded text-center"
                    style={{
                      backgroundColor: `${tierInfo.color}20`,
                      color: tierInfo.color,
                    }}
                  >
                    T{tier}
                  </div>

                  <div className="flex-1 h-6 bg-white rounded-lg border border-gray-200 relative overflow-hidden">
                    <motion.div
                      className="absolute inset-y-0 left-0 rounded-lg"
                      style={{
                        backgroundColor: passed ? '#58cc02' : '#ff4b4b',
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: passed ? '100%' : '25%' }}
                      transition={{ delay: 0.4 + tier * 0.08, duration: 0.4 }}
                    />
                    <div className="relative z-10 h-full flex items-center px-2">
                      <span className={`text-xs font-medium truncate ${passed ? 'text-white' : 'text-gray-500'}`}>
                        {question?.skill || tierInfo.skill}
                      </span>
                    </div>
                  </div>

                  <div className="w-5 shrink-0 text-center">
                    {passed ? (
                      <span className="text-[#58cc02]">✓</span>
                    ) : (
                      <span className="text-[#ff4b4b]">✗</span>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        {/* Primary Blocker */}
        {primaryGap && (
          <motion.div
            className="bg-gradient-to-r from-[#fff3e0] to-[#ffe0b2] border border-[#ff9600] rounded-2xl p-4 mb-4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#ff9600] rounded-full flex items-center justify-center shrink-0">
                <span className="text-base">🎯</span>
              </div>
              <div>
                <h4 className="font-bold text-[#e65100] text-sm mb-1">
                  Your Growth Area
                </h4>
                <p className="text-xs text-[#bf360c]">
                  <strong>{primaryGap.skill}</strong> needs work.
                  {selections.urgency === 'critical' && ' Focus here first!'}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* All passed */}
        {analysis.passedCount === 4 && (
          <motion.div
            className="bg-gradient-to-r from-[#d7ffb8] to-[#b8f397] border border-[#58cc02] rounded-2xl p-4 mb-4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#58cc02] rounded-full flex items-center justify-center shrink-0">
                <span className="text-base">🏆</span>
              </div>
              <div>
                <h4 className="font-bold text-[#2e7d32] text-sm mb-1">Outstanding!</h4>
                <p className="text-xs text-[#1b5e20]">
                  You've mastered all tiers. Ready for advanced practice!
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* QR Code section */}
        <motion.div
          className="bg-white border-2 border-gray-200 rounded-2xl p-4 mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: showQR ? 1 : 0, y: showQR ? 0 : 20 }}
          transition={{ delay: 0.6 }}
        >
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-lg">📱</span>
            <h3 className="font-bold text-gray-800 text-sm">Connect Phone</h3>
          </div>

          <p className="text-xs text-gray-500 mb-3 text-center">
            Upload handwritten work for AI feedback
            {primaryGap && (
              <span className="block text-[#ff9600] mt-1">
                Fix your {primaryGap.topic} mistakes
              </span>
            )}
          </p>

          {/* QR Code */}
          <div className="bg-gray-50 p-3 rounded-xl flex justify-center mb-2">
            <div className="w-28 h-28 relative">
              <svg viewBox="0 0 100 100" className="w-full h-full">
                <rect x="0" y="0" width="30" height="30" fill="#000" />
                <rect x="5" y="5" width="20" height="20" fill="#fff" />
                <rect x="10" y="10" width="10" height="10" fill="#000" />
                <rect x="70" y="0" width="30" height="30" fill="#000" />
                <rect x="75" y="5" width="20" height="20" fill="#fff" />
                <rect x="80" y="10" width="10" height="10" fill="#000" />
                <rect x="0" y="70" width="30" height="30" fill="#000" />
                <rect x="5" y="75" width="20" height="20" fill="#fff" />
                <rect x="10" y="80" width="10" height="10" fill="#000" />
                {[...Array(100)].map((_, i) => (
                  <rect
                    key={i}
                    x={35 + (i % 10) * 3}
                    y={5 + Math.floor(i / 10) * 3}
                    width="2"
                    height="2"
                    fill={Math.random() > 0.5 ? '#000' : '#fff'}
                  />
                ))}
                <rect x="40" y="40" width="20" height="20" fill="#58cc02" rx="4" />
              </svg>
              <motion.div
                className="absolute inset-0 border-2 border-[#58cc02] rounded-lg"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
          </div>

          <p className="text-xs text-gray-400 text-center">
            Session: <span className="font-mono font-bold">{sessionId}</span>
          </p>
        </motion.div>

        {/* Continue button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <SquishyButton onClick={onComplete} className="w-full">
            START PRACTICING
          </SquishyButton>

          <p className="mt-3 text-xs text-gray-400 text-center">
            📸 Connect phone anytime from settings
          </p>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default QRBridgeScreen
