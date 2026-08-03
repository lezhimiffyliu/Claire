/**
 * ProblemBank - Browse and practice UW Math problems
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ProblemCard from './ProblemCard'
import { loadProblems, getTopicList, getExamList, getCourseSummary } from '../../api/problemLoader'

// 格式化考试名称
function formatExamName(examId) {
  if (!examId) return ''
  const seasonMap = { au: 'Autumn', wi: 'Winter', sp: 'Spring', su: 'Summer' }
  const season = seasonMap[examId.slice(0, 2)] || ''
  const year = '20' + examId.slice(2, 4)
  return `${season} ${year}`
}

// 格式化 topic 名称
function formatTopicName(topic) {
  if (!topic) return ''
  return topic.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function ProblemBank({ course = '126', onBack }) {
  const [problems, setProblems] = useState([])
  const [topics, setTopics] = useState([])
  const [exams, setExams] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [selectedTopic, setSelectedTopic] = useState('')
  const [selectedExam, setSelectedExam] = useState('')

  // Practice mode
  const [practiceMode, setPracticeMode] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [currentPartIndex, setCurrentPartIndex] = useState(0)

  // Load initial data
  useEffect(() => {
    loadData()
  }, [course])

  // Reload problems when filters change
  useEffect(() => {
    if (!loading) {
      filterProblems()
    }
  }, [selectedTopic, selectedExam])

  async function loadData() {
    setLoading(true)
    setError(null)

    try {
      const [problemsData, topicsData, examsData, summaryData] = await Promise.all([
        loadProblems(course),
        getTopicList(course),
        getExamList(course),
        getCourseSummary(course),
      ])

      setProblems(problemsData)
      setTopics(topicsData)
      setExams(examsData)
      setSummary(summaryData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function filterProblems() {
    try {
      let data = await loadProblems(course)

      // 筛选 topic
      if (selectedTopic) {
        data = data.filter(p => p.topic === selectedTopic)
      }

      // 筛选 exam
      if (selectedExam) {
        data = data.filter(p => p.exam === selectedExam)
      }

      setProblems(data)
    } catch (err) {
      console.error('Failed to load problems:', err)
    }
  }

  function startPractice(index = 0) {
    setCurrentIndex(index)
    setCurrentPartIndex(0)
    setPracticeMode(true)
  }

  function handleNextProblem() {
    const currentProblem = problems[currentIndex]

    // Check if there are more parts in current problem
    if (currentPartIndex < currentProblem.parts.length - 1) {
      setCurrentPartIndex(currentPartIndex + 1)
    } else {
      // Move to next problem
      if (currentIndex < problems.length - 1) {
        setCurrentIndex(currentIndex + 1)
        setCurrentPartIndex(0)
      } else {
        // End of problems
        setPracticeMode(false)
      }
    }
  }

  function exitPractice() {
    setPracticeMode(false)
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading problems...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">加载失败</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-lg"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  // Practice mode
  if (practiceMode && problems.length > 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-6 px-4">
        {/* Header */}
        <div className="max-w-2xl mx-auto mb-6">
          <div className="flex items-center justify-between">
            <button
              onClick={exitPractice}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to List
            </button>
            <span className="text-gray-500 text-sm">
              {currentIndex + 1} / {problems.length}
            </span>
          </div>
        </div>

        {/* Problem card */}
        <div className="max-w-2xl mx-auto">
          <AnimatePresence mode="wait">
            <ProblemCard
              key={`${problems[currentIndex].id}-${currentPartIndex}`}
              problem={problems[currentIndex]}
              partIndex={currentPartIndex}
              onNext={handleNextProblem}
            />
          </AnimatePresence>
        </div>
      </div>
    )
  }

  // Problem list mode
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              {onBack && (
                <button
                  onClick={onBack}
                  className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100"
                >
                  <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
              )}
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  Math {course} Problem Bank
                </h1>
                {summary && (
                  <p className="text-gray-500 text-sm">
                    {summary.totalProblems} problems · {summary.totalParts} parts
                  </p>
                )}
              </div>
            </div>

            {problems.length > 0 && (
              <button
                onClick={() => startPractice(0)}
                className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start Practice
              </button>
            )}
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
            >
              <option value="">All Topics</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.displayName}
                </option>
              ))}
            </select>

            <select
              value={selectedExam}
              onChange={(e) => setSelectedExam(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
            >
              <option value="">All Exams</option>
              {exams.map((exam) => (
                <option key={exam.id} value={exam.id}>
                  {exam.displayName} ({exam.problemCount})
                </option>
              ))}
            </select>

            {(selectedTopic || selectedExam) && (
              <button
                onClick={() => {
                  setSelectedTopic('')
                  setSelectedExam('')
                }}
                className="text-blue-500 hover:text-blue-600 text-sm"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Problem list */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {problems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No problems found with these filters.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {problems.map((problem, idx) => (
              <motion.div
                key={problem.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow cursor-pointer"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                onClick={() => startPractice(idx)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">
                        {formatTopicName(problem.topic)}
                      </span>
                      <span className="text-gray-400 text-xs">
                        {formatExamName(problem.exam)} - P{problem.problem_number}
                      </span>
                    </div>

                    <p className="text-gray-800 line-clamp-2">
                      {problem.stem || problem.parts?.[0]?.question_text?.slice(0, 150)}...
                    </p>

                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                      <span>{problem.parts?.length || 0} part{(problem.parts?.length || 0) > 1 ? 's' : ''}</span>
                      <span>·</span>
                      <span>{problem.points} pts</span>
                    </div>
                  </div>

                  <div className="ml-4">
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProblemBank
