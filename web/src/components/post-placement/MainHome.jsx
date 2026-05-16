import { motion } from 'framer-motion'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
}

const courseNames = {
  math124: 'Math 124',
  math125: 'Math 125',
  math126: 'Math 126',
}

const examTimelineLabels = {
  in_2_days: 'Exam in 2 days',
  this_week: 'Exam this week',
  catching_up: 'Catching up',
}

function StudyPathNode({ icon, title, subtitle, status, index, onClick }) {
  const isLocked = status === 'locked'
  const isCurrent = status === 'current'

  return (
    <motion.div
      className="study-path-node relative pl-14"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + index * 0.1 }}
    >
      {/* Connector line */}
      {index > 0 && (
        <div
          className={`absolute left-[22px] -top-6 w-1 h-6 ${
            isLocked ? 'bg-gray-200' : 'bg-[#58cc02]'
          }`}
        />
      )}

      {/* Node circle */}
      <div
        className={`absolute left-2 top-3 w-8 h-8 rounded-full border-4 flex items-center justify-center ${
          isCurrent
            ? 'border-[#58cc02] bg-[#58cc02]'
            : isLocked
            ? 'border-gray-200 bg-white'
            : 'border-[#58cc02] bg-white'
        }`}
      >
        {isCurrent && <span className="text-white text-sm">{icon}</span>}
        {isLocked && (
          <svg className="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
        {status === 'completed' && (
          <svg className="w-4 h-4 text-[#58cc02]" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Content card */}
      <button
        onClick={onClick}
        disabled={isLocked}
        className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
          isCurrent
            ? 'bg-[#d7ffb8] border-[#58cc02] shadow-md'
            : isLocked
            ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
            : 'bg-white border-gray-200 hover:border-[#58cc02] hover:bg-[#f7fff0]'
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div className="flex-1">
            <div className={`font-bold ${isLocked ? 'text-gray-400' : 'text-gray-800'}`}>
              {title}
            </div>
            <div className="text-sm text-gray-500">{subtitle}</div>
          </div>
          {isCurrent && (
            <div className="shrink-0">
              <svg
                className="w-6 h-6 text-[#58cc02]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          )}
        </div>
      </button>
    </motion.div>
  )
}

function MainHome({ testState, selections, onComplete }) {
  const course = selections?.course || 'math126'
  const examTimeline = selections?.examTimeline || 'this_week'
  const analysis = testState.analysis || {}
  const primaryGap = analysis.gaps?.[0]

  const studyPath = [
    {
      icon: '🎯',
      title: primaryGap ? `Fix: ${primaryGap.skill}` : 'Master core concepts',
      subtitle: 'Your priority blocker',
      status: 'current',
    },
    {
      icon: '📝',
      title: 'Practice UW midterm problem',
      subtitle: 'Real exam-style question',
      status: 'locked',
    },
    {
      icon: '✍️',
      title: 'Upload handwritten work',
      subtitle: 'Get feedback on your solution',
      status: 'locked',
    },
    {
      icon: '🔄',
      title: 'Review mistake patterns',
      subtitle: 'Learn from your errors',
      status: 'locked',
    },
  ]

  const handleNodeClick = (index) => {
    if (index === 0) {
      // Navigate to main app
      onComplete()
    }
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex flex-col overflow-auto"
    >
      {/* Header */}
      <motion.header
        className="px-4 py-4 border-b border-gray-100"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-800">{courseNames[course]}</h1>
              <p className="text-sm text-gray-500">{examTimelineLabels[examTimeline]}</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 text-sm text-gray-600">
                <span>{analysis.skillEmoji || '📊'}</span>
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <div className="flex-1 px-4 py-6 overflow-auto">
        <div className="max-w-md mx-auto">
          {/* Priority blocker card */}
          {primaryGap && (
            <motion.div
              className="bg-gradient-to-r from-[#ff9600] to-[#ffb347] rounded-2xl p-4 mb-6 text-white shadow-lg"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">⚡</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm opacity-80">Priority Blocker</div>
                  <div className="font-bold text-lg">{primaryGap.skill}</div>
                </div>
                <button
                  onClick={() => onComplete()}
                  className="px-4 py-2 bg-white text-[#ff9600] font-bold rounded-xl shadow-sm hover:bg-gray-50 transition-colors"
                >
                  Fix Now
                </button>
              </div>
            </motion.div>
          )}

          {/* Study path title */}
          <motion.h2
            className="text-lg font-bold text-gray-800 mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Your Study Path
          </motion.h2>

          {/* Study path nodes */}
          <div className="space-y-4">
            {studyPath.map((node, index) => (
              <StudyPathNode
                key={index}
                {...node}
                index={index}
                onClick={() => handleNodeClick(index)}
              />
            ))}
          </div>

          {/* Bottom encouragement */}
          <motion.div
            className="mt-8 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <p className="text-sm text-gray-400">
              Complete your first problem to unlock more content
            </p>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

export default MainHome
