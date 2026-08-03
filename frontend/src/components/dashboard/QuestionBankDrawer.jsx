import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { loadProblems, getTopicList, getExamList } from '../../api/problemLoader'

// Difficulty estimation based on problem structure
function estimateDifficulty(problem) {
  const partCount = problem.parts?.length || 1
  const points = problem.points || 0

  if (points >= 15 || partCount >= 6) return 'hard'
  if (points >= 10 || partCount >= 3) return 'medium'
  return 'easy'
}

// Format exam name for display
function formatExamName(examId) {
  if (!examId) return ''
  const seasonMap = { au: 'Autumn', wi: 'Winter', sp: 'Spring' }
  const season = seasonMap[examId.slice(0, 2)] || ''
  const year = '20' + examId.slice(2, 4)
  return `${season} ${year}`
}

// Format topic for display
function formatTopic(topic) {
  if (!topic) return ''
  return topic.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function FilterPills({ label, options, selected, onSelect, showAll = true }) {
  return (
    <div className="mb-3">
      <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">
        {label}
      </label>
      <div className="flex flex-wrap gap-1.5">
        {showAll && (
          <button
            onClick={() => onSelect(null)}
            className={`
              px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${selected === null
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }
            `}
          >
            All
          </button>
        )}
        {options.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onSelect(opt.id)}
            className={`
              px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${selected === opt.id
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }
            `}
          >
            {opt.displayName || opt.id}
          </button>
        ))}
      </div>
    </div>
  )
}

function ProblemRow({ problem, attemptStatus, onPractice, onAddToRoadmap }) {
  const difficulty = estimateDifficulty(problem)
  const difficultyColors = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-amber-100 text-amber-700',
    hard: 'bg-red-100 text-red-700',
  }

  const statusBadge = {
    completed: { text: 'Mastered', color: 'bg-green-500 text-white' },
    attempted: { text: 'Tried', color: 'bg-amber-100 text-amber-700' },
    unseen: { text: 'New', color: 'bg-gray-100 text-gray-500' },
  }

  const status = attemptStatus || 'unseen'

  return (
    <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-gray-100 hover:border-gray-200 hover:shadow-sm transition-all">
      {/* Left: Problem info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">
          {formatExamName(problem.exam)} · Problem {problem.problem_number}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">
            {formatTopic(problem.topic)}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${difficultyColors[difficulty]}`}>
            {difficulty}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${statusBadge[status].color}`}>
            {statusBadge[status].text}
          </span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onAddToRoadmap(problem)}
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="Add to roadmap"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <button
          onClick={() => onPractice(problem)}
          className="px-3 py-1.5 bg-[#58cc02] text-white text-xs font-bold rounded-lg hover:bg-[#4db302] transition-colors"
        >
          Practice
        </button>
      </div>
    </div>
  )
}

export default function QuestionBankDrawer({
  isOpen,
  onClose,
  course,
  attemptHistory = {},
  onPractice,
  onAddToRoadmap,
}) {
  const [problems, setProblems] = useState([])
  const [topics, setTopics] = useState([])
  const [exams, setExams] = useState([])
  const [loading, setLoading] = useState(true)

  // Filters
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [selectedExam, setSelectedExam] = useState(null)
  const [selectedDifficulty, setSelectedDifficulty] = useState(null)
  const [selectedStatus, setSelectedStatus] = useState(null)

  // Load data
  useEffect(() => {
    if (!course) return

    async function load() {
      setLoading(true)
      try {
        const courseNum = course.replace('math', '')
        const [allProblems, topicList, examList] = await Promise.all([
          loadProblems(courseNum),
          getTopicList(courseNum),
          getExamList(courseNum),
        ])
        setProblems(allProblems)
        setTopics(topicList)
        setExams(examList)
      } catch (error) {
        console.error('Failed to load problems:', error)
      }
      setLoading(false)
    }

    load()
  }, [course])

  // Filter problems
  const filteredProblems = useMemo(() => {
    return problems.filter((p) => {
      if (selectedTopic && p.topic !== selectedTopic) return false
      if (selectedExam && p.exam !== selectedExam) return false

      if (selectedDifficulty) {
        const diff = estimateDifficulty(p)
        if (diff !== selectedDifficulty) return false
      }

      if (selectedStatus) {
        const status = attemptHistory[p.id]?.status || 'unseen'
        if (status !== selectedStatus) return false
      }

      return true
    })
  }, [problems, selectedTopic, selectedExam, selectedDifficulty, selectedStatus, attemptHistory])

  const difficultyOptions = [
    { id: 'easy', displayName: 'Easy' },
    { id: 'medium', displayName: 'Medium' },
    { id: 'hard', displayName: 'Hard' },
  ]

  const statusOptions = [
    { id: 'unseen', displayName: 'New' },
    { id: 'attempted', displayName: 'Tried' },
    { id: 'completed', displayName: 'Mastered' },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-50"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-gray-50 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
              <div>
                <h2 className="text-lg font-bold text-gray-800">Question Bank</h2>
                <p className="text-sm text-gray-500">
                  {filteredProblems.length} problems found
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Filters */}
            <div className="p-4 bg-white border-b border-gray-200 overflow-x-auto">
              <FilterPills
                label="Topic"
                options={topics.slice(0, 8)}
                selected={selectedTopic}
                onSelect={setSelectedTopic}
              />
              <FilterPills
                label="Exam"
                options={exams.slice(0, 6)}
                selected={selectedExam}
                onSelect={setSelectedExam}
              />
              <div className="flex gap-4">
                <div className="flex-1">
                  <FilterPills
                    label="Difficulty"
                    options={difficultyOptions}
                    selected={selectedDifficulty}
                    onSelect={setSelectedDifficulty}
                  />
                </div>
                <div className="flex-1">
                  <FilterPills
                    label="Status"
                    options={statusOptions}
                    selected={selectedStatus}
                    onSelect={setSelectedStatus}
                  />
                </div>
              </div>
            </div>

            {/* Problem list */}
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="w-8 h-8 border-4 border-[#58cc02] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : filteredProblems.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-2">🔍</div>
                  <p className="text-gray-500">No problems match your filters</p>
                  <button
                    onClick={() => {
                      setSelectedTopic(null)
                      setSelectedExam(null)
                      setSelectedDifficulty(null)
                      setSelectedStatus(null)
                    }}
                    className="mt-2 text-sm text-[#58cc02] hover:underline"
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredProblems.map((problem) => (
                    <ProblemRow
                      key={problem.id}
                      problem={problem}
                      attemptStatus={attemptHistory[problem.id]?.status}
                      onPractice={onPractice}
                      onAddToRoadmap={onAddToRoadmap}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
