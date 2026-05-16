import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
}

function FeatureSection({ title, description, visual: Visual, reversed }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section ref={ref} className="py-20 md:py-24 px-6 md:px-12 lg:px-20 bg-[var(--claire-bg)]">
      <motion.div
        className={`max-w-6xl mx-auto flex flex-col ${
          reversed ? 'md:flex-row-reverse' : 'md:flex-row'
        } items-center gap-12 md:gap-16`}
        variants={containerVariants}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
      >
        {/* Text content */}
        <div className="flex-1 text-center md:text-left max-w-lg">
          <motion.h2
            className="text-2xl md:text-3xl font-semibold text-[var(--claire-navy)] mb-4 leading-tight"
            variants={itemVariants}
          >
            {title}
          </motion.h2>

          <motion.p
            className="text-base text-[var(--claire-gray-600)] leading-relaxed"
            variants={itemVariants}
          >
            {description}
          </motion.p>
        </div>

        {/* Visual component */}
        <motion.div className="flex-1 w-full max-w-md" variants={itemVariants}>
          {Visual && <Visual isInView={isInView} />}
        </motion.div>
      </motion.div>
    </section>
  )
}

// Visual: Diagnostic status panel
export function DiagnosticVisual({ isInView }) {
  return (
    <div className="bg-white rounded-xl border border-[var(--claire-gray-200)] shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
          Your Diagnosis
        </span>
        <span className="text-xs text-[var(--claire-gray-400)]">5 min scan</span>
      </div>
      <div className="space-y-3">
        {/* Weak */}
        <motion.div
          className="status-card weak"
          initial={{ opacity: 0, x: -10 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ delay: 0.2, duration: 0.2 }}
        >
          <span className="label-weak">Weak</span>
          <p className="text-sm font-medium text-[var(--claire-gray-900)] mt-1">
            Limits with L'Hôpital
          </p>
        </motion.div>

        {/* Next */}
        <motion.div
          className="status-card next"
          initial={{ opacity: 0, x: -10 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ delay: 0.3, duration: 0.2 }}
        >
          <span className="label-next">Next</span>
          <p className="text-sm font-medium text-[var(--claire-gray-900)] mt-1">
            Implicit Differentiation
          </p>
        </motion.div>

        {/* Strong */}
        <motion.div
          className="status-card strong"
          initial={{ opacity: 0, x: -10 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ delay: 0.4, duration: 0.2 }}
        >
          <span className="label-strong">Strong</span>
          <p className="text-sm text-[var(--claire-gray-600)] mt-1">
            Chain Rule · Power Rule
          </p>
        </motion.div>
      </div>
      <p className="mt-4 text-xs text-[var(--claire-gray-400)] text-center">
        Focus on Limits first for the biggest improvement
      </p>
    </div>
  )
}

// Visual: Problem cards from real exams
export function ProblemCardsVisual({ isInView }) {
  const problems = [
    { course: 'Math 124', exam: 'Final 2023', topic: 'Related Rates' },
    { course: 'Math 125', exam: 'Midterm 2', topic: 'Chain Rule' },
    { course: 'Math 126', exam: 'Final', topic: 'Double Integral' },
  ]

  return (
    <div className="space-y-3">
      {problems.map((problem, i) => (
        <motion.div
          key={i}
          className="bg-white rounded-lg border border-[var(--claire-gray-200)] p-4"
          initial={{ opacity: 0, y: 10 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2 + i * 0.1, duration: 0.2 }}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-[var(--claire-gray-500)]">
              {problem.course}
            </span>
            <span className="text-[var(--claire-gray-300)]">·</span>
            <span className="text-xs text-[var(--claire-gray-400)]">
              {problem.exam}
            </span>
          </div>
          <span className="text-sm font-medium text-[var(--claire-navy)]">
            {problem.topic}
          </span>
        </motion.div>
      ))}
      <p className="text-xs text-[var(--claire-gray-400)] text-center mt-4">
        760+ problems from 86 past UW exams
      </p>
    </div>
  )
}

// Visual: AI feedback panel
export function FeedbackVisual({ isInView }) {
  return (
    <div className="bg-white rounded-xl border border-[var(--claire-gray-200)] shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-[var(--claire-gray-100)] px-4 py-3 border-b border-[var(--claire-gray-200)]">
        <span className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
          Claire's Feedback
        </span>
      </div>

      <div className="p-4 space-y-3">
        {/* Student work */}
        <motion.div
          className="bg-[var(--claire-gray-100)] rounded-lg p-3"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.2, duration: 0.2 }}
        >
          <span className="text-xs text-[var(--claire-gray-400)] block mb-1">
            Your work
          </span>
          <p className="text-sm text-[var(--claire-gray-700)] font-mono">
            dy/dx = 2x + 2y = 0
          </p>
        </motion.div>

        {/* Error highlight */}
        <motion.div
          className="status-card weak"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.3, duration: 0.2 }}
        >
          <p className="text-sm text-[var(--claire-gray-700)]">
            <span className="font-medium text-[var(--claire-weak)]">
              Missing step:
            </span>{' '}
            When differentiating y², use the chain rule: d/dx[y²] = 2y · (dy/dx)
          </p>
        </motion.div>

        {/* AI hint */}
        <motion.div
          className="ai-thinking"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.4, duration: 0.2 }}
        >
          <p className="text-sm text-[var(--claire-gray-700)]">
            <span className="font-medium text-[var(--claire-ai)]">Hint:</span>{' '}
            Rewrite as 2x + 2y(dy/dx) = 0, then solve for dy/dx.
          </p>
        </motion.div>
      </div>
    </div>
  )
}

// Visual: Learning path/roadmap
export function RoadmapVisual({ isInView }) {
  const nodes = [
    { topic: 'Limits with algebra', status: 'done' },
    { topic: 'Implicit differentiation', status: 'current' },
    { topic: 'Related rates', status: 'next' },
    { topic: 'Optimization', status: 'locked' },
  ]

  return (
    <div className="bg-white rounded-xl border border-[var(--claire-gray-200)] shadow-sm p-5">
      <div className="mb-4">
        <span className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
          Your Path
        </span>
      </div>

      <div className="space-y-0">
        {nodes.map((node, i) => (
          <motion.div
            key={node.topic}
            className="roadmap-node py-3"
            initial={{ opacity: 0, x: -10 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.2 + i * 0.1, duration: 0.2 }}
          >
            {/* Node */}
            <div className={`roadmap-dot ${node.status}`}>
              {node.status === 'done' && (
                <svg
                  className="w-3 h-3 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>

            {/* Content */}
            <div
              className={`flex-1 ${
                node.status === 'locked' ? 'opacity-50' : ''
              }`}
            >
              <p
                className={`text-sm ${
                  node.status === 'current'
                    ? 'font-semibold text-[var(--claire-navy)]'
                    : 'text-[var(--claire-gray-600)]'
                }`}
              >
                {node.topic}
              </p>
              {node.status === 'current' && (
                <span className="text-xs text-[var(--claire-teal)]">
                  You are here
                </span>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default FeatureSection
