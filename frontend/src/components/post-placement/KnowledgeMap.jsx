import { motion } from 'framer-motion'
import SquishyButton from '../ui/SquishyButton'

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

function SkillRow({ item, isStrength, delay }) {
  const color = item.color || (isStrength ? '#58cc02' : '#ff9600')
  const tierName = item.tierName || (isStrength ? 'Strength' : 'Focus')
  const skill = item.skill || item.skillGap || 'Unknown skill'

  return (
    <motion.div
      className={`flex items-center gap-4 p-3 rounded-xl border-2 ${
        isStrength
          ? 'bg-[#d7ffb8] border-[#58cc02]'
          : 'bg-[#fff3e0] border-[#ff9600]'
      }`}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
    >
      {/* Status icon */}
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center ${
          isStrength ? 'bg-[#58cc02]' : 'bg-[#ff9600]'
        }`}
      >
        {isStrength ? (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <span className="text-white text-lg font-bold">!</span>
        )}
      </div>

      {/* Skill info */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-0.5 rounded text-xs font-bold uppercase"
            style={{ backgroundColor: `${color}20`, color: color }}
          >
            {tierName}
          </span>
        </div>
        <div className="font-medium text-gray-800 mt-1">{skill}</div>
        {item.topic && <div className="text-sm text-gray-500">{item.topic}</div>}
      </div>
    </motion.div>
  )
}

function KnowledgeMap({ testState, selections, onNext }) {
  const analysis = testState.analysis || {}
  const {
    skillLevel = 'Analyzed',
    skillEmoji = '📊',
    levelDescription = '',
    gaps = [],
    strengths = [],
    blockerMessage,
  } = analysis
  const course = selections?.course || 'math126'

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex flex-col px-4 py-6 overflow-auto"
    >
      <div className="w-full max-w-md mx-auto">
        {/* Header with skill level */}
        <motion.div
          className="text-center mb-6"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className="text-4xl mb-2 block">{skillEmoji}</span>
          <h1 className="text-2xl font-bold text-gray-800">
            {skillLevel}
          </h1>
          <p className="text-gray-500 mt-1 text-sm">{levelDescription}</p>
          <p className="text-xs text-gray-400 mt-2">{courseNames[course]} Skill Map</p>
        </motion.div>

        {/* Strengths section */}
        {strengths.length > 0 && (
          <div className="mb-4">
            <h2 className="text-sm font-bold text-[#58cc02] uppercase mb-2">✓ Strengths</h2>
            <div className="space-y-2">
              {strengths.map((item, index) => (
                <SkillRow
                  key={item.skill}
                  item={item}
                  isStrength={true}
                  delay={0.1 + index * 0.08}
                />
              ))}
            </div>
          </div>
        )}

        {/* Gaps section */}
        {gaps.length > 0 && (
          <div className="mb-4">
            <h2 className="text-sm font-bold text-[#ff9600] uppercase mb-2">⚠ Focus Areas</h2>
            <div className="space-y-2">
              {gaps.map((item, index) => (
                <SkillRow
                  key={item.skill || item.skillGap || `gap-${index}`}
                  item={item}
                  isStrength={false}
                  delay={0.2 + strengths.length * 0.08 + index * 0.08}
                />
              ))}
            </div>
          </div>
        )}

        {/* Blocker highlight */}
        {blockerMessage && (
          <motion.div
            className="bg-[#fff3e0] border-2 border-[#ff9600] rounded-xl p-4 mb-6"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">🎯</span>
              <div>
                <div className="font-bold text-[#ff9600] mb-1">Your Priority</div>
                <p className="text-sm text-gray-700">{blockerMessage}</p>
              </div>
            </div>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <SquishyButton onClick={onNext} className="w-full">
            CONTINUE
          </SquishyButton>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default KnowledgeMap
