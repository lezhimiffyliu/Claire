/**
 * MockExamsPage - Real UW Finals browser (supports Math 124/125/126)
 *
 * Shows all available past finals with real data from /problems/*.json
 * Connects to existing MockExamView for the exam-taking experience
 */

import { useState, useEffect } from 'react'
import { getCourseFinals } from '../../api/problemLoader'
import { useAuth } from '../../context/AuthContext'
import { findSectionForProblem } from '../../utils/conceptAliases'

// Format duration as "Xh Ym"
function formatDuration(minutes) {
  const hrs = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hrs > 0 && mins > 0) return `${hrs}h ${mins}m`
  if (hrs > 0) return `${hrs}h 00m`
  return `${mins}m`
}

// View Topics Modal - shows which section each problem belongs to
function ViewTopicsModal({ isOpen, onClose, examName, problems }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">{examName} — Topics</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Problem list */}
        <div className="p-5 overflow-y-auto flex-1">
          <div className="space-y-3">
            {problems.map((problem) => {
              const section = findSectionForProblem(problem)
              return (
                <div key={problem.id} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-sm font-semibold text-gray-600 flex-shrink-0">
                    {problem.problem_number}
                  </div>
                  <div className="flex-1 min-w-0">
                    {section ? (
                      <>
                        <p className="font-medium text-gray-900">{section.id} {section.display_name}</p>
                        <p className="text-sm text-gray-500">{problem.points} pts · {problem.parts?.length || 1} part{(problem.parts?.length || 1) > 1 ? 's' : ''}</p>
                      </>
                    ) : (
                      <p className="text-gray-500 italic">Unknown section</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-[#0B1F3A] text-white font-semibold rounded-lg hover:bg-[#0B1F3A]/90 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// Topic tag component
function TopicTag({ topic }) {
  return (
    <span className="px-2 py-0.5 bg-[var(--claire-bg)] text-[var(--claire-text-secondary)] text-xs rounded-md">
      {topic}
    </span>
  )
}

// Status badge component
function StatusBadge({ status, progress, score }) {
  const configs = {
    not_started: {
      dot: 'bg-gray-400',
      text: 'text-gray-600',
      label: 'Not started',
    },
    in_progress: {
      dot: 'bg-blue-500',
      text: 'text-blue-600',
      label: 'In progress',
    },
    completed: {
      dot: 'bg-emerald-500',
      text: 'text-emerald-600',
      label: 'Completed',
    },
  }

  const config = configs[status] || configs.not_started

  return (
    <div className="flex flex-col items-end">
      <div className="flex items-center gap-1.5">
        <span className={`w-2 h-2 rounded-full ${config.dot}`} />
        <span className={`text-sm font-medium ${config.text}`}>{config.label}</span>
      </div>
      {status === 'in_progress' && progress && (
        <span className="text-xs text-gray-500 mt-0.5">{progress}</span>
      )}
      {status === 'completed' && score !== null && (
        <span className="text-sm font-semibold text-gray-700 mt-0.5">Score: {score}%</span>
      )}
    </div>
  )
}

// Recommended exam hero card
// Reads from normalizedExam = { exam_metadata, recommendation_metadata }
function RecommendedExamCard({ normalizedExam, onStart, onViewTopics }) {
  const { exam_metadata, recommendation_metadata } = normalizedExam

  return (
    <div className="bg-[#0B1F3A] rounded-2xl p-6 text-white mb-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Badge */}
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/20 rounded-full mb-3">
            <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
            <span className="text-xs font-medium text-emerald-300">RECOMMENDED NEXT</span>
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold mb-2">{exam_metadata.course_display} {exam_metadata.display_name}</h2>

          {/* Description */}
          <p className="text-white/70 text-sm mb-4">
            {recommendation_metadata.reason}
          </p>

          {/* Stats */}
          <div className="flex items-center gap-4 text-sm text-white/80 mb-4">
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{exam_metadata.problem_count} problems · {exam_metadata.part_count} parts</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              <span>{exam_metadata.total_points} points</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>~{formatDuration(exam_metadata.duration_minutes)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{exam_metadata.source}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 ml-6">
          <button
            onClick={() => onStart(normalizedExam)}
            className="flex items-center gap-2 px-5 py-2.5 bg-white text-[#0B1F3A] font-semibold rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
            Start Exam
          </button>
          <button
            onClick={() => onViewTopics(normalizedExam)}
            className="px-5 py-2.5 bg-white/10 text-white font-medium rounded-lg hover:bg-white/20 transition-colors"
          >
            View Topics
          </button>
        </div>
      </div>
    </div>
  )
}

// Single exam row in the list
function ExamRow({ exam, onStart, userProgress, courseDisplay }) {
  const status = userProgress?.status || 'not_started'
  const progress = userProgress?.progress
  const score = userProgress?.score

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between">
        {/* Left: Exam info */}
        <div className="flex gap-4">
          {/* Icon */}
          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>

          {/* Info */}
          <div>
            <h3 className="font-semibold text-gray-900">{exam.displayName}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{courseDisplay} • Real UW past final</p>

            {/* Stats */}
            <div className="flex items-center gap-4 text-sm text-gray-500 mt-2">
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>{exam.questionCount} questions</span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
                <span>{exam.totalPoints} points</span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{formatDuration(exam.estimatedMinutes)}</span>
              </div>
            </div>

            {/* Topics */}
            <div className="flex flex-wrap gap-1.5 mt-3">
              {exam.topics.slice(0, 3).map((topic, idx) => (
                <TopicTag key={idx} topic={topic} />
              ))}
              {exam.topics.length > 3 && (
                <span className="text-xs text-gray-400">+{exam.topics.length - 3} more</span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Status and action */}
        <div className="flex items-center gap-4">
          <StatusBadge status={status} progress={progress} score={score} />

          <button
            onClick={() => onStart(exam)}
            className={`px-5 py-2.5 rounded-lg font-semibold transition-colors ${
              status === 'completed'
                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                : status === 'in_progress'
                ? 'bg-[#0B1F3A] text-white hover:bg-[#0B1F3A]/90'
                : 'bg-[#0B1F3A] text-white hover:bg-[#0B1F3A]/90'
            }`}
          >
            {status === 'completed' ? 'Review' : status === 'in_progress' ? 'Resume' : 'Start'}
          </button>
        </div>
      </div>
    </div>
  )
}

// Right sidebar component
function RightSidebar({ user, examCountdown }) {
  const userName = user?.email?.split('@')[0] || 'Student'
  const initial = userName.charAt(0).toUpperCase()

  return (
    <div className="w-72 flex-shrink-0">
      {/* User info */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-semibold">
          {initial}
        </div>
        <div>
          <p className="font-medium text-gray-900">{userName}</p>
          <p className="text-sm text-gray-500">{examCountdown?.course_display || 'Math 126'}</p>
        </div>
      </div>

      {/* Upcoming exam */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <p className="text-xs text-gray-500 font-medium mb-2">UPCOMING EXAM</p>
        <div className="flex items-baseline justify-between">
          <span className="text-sm text-gray-700">{examCountdown?.course_display || 'Math 126'} {examCountdown?.next_exam_display || 'Final'}</span>
          <div className="text-right">
            <span className="text-2xl font-bold text-gray-900">{examCountdown?.days_until || 14}</span>
            <span className="text-sm text-gray-500 ml-1">days left</span>
          </div>
        </div>
        <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0B1F3A] rounded-full"
            style={{ width: `${Math.max(10, 100 - (examCountdown?.days_until || 14) * 3)}%` }}
          />
        </div>
      </div>

      {/* Premium CTA */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="font-medium text-gray-900">Go Premium</p>
          <svg className="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
          </svg>
        </div>
        <p className="text-sm text-gray-600 mb-3">Unlimited practice & AI help</p>
        <button className="w-full py-2.5 bg-[#0B1F3A] text-white font-semibold rounded-lg hover:bg-[#0B1F3A]/90 transition-colors">
          Try 1 Week Free
        </button>
      </div>
    </div>
  )
}

export default function MockExamsPage({ onStartExam, examCountdown, courseCode = '126', hideSidebar = false }) {
  const { user } = useAuth()
  const [exams, setExams] = useState([])
  const [loading, setLoading] = useState(true)
  const [userProgress, setUserProgress] = useState({}) // { examId: { status, progress, score } }
  const [viewTopicsExam, setViewTopicsExam] = useState(null) // exam to show in View Topics modal

  // Load exams for the selected course
  useEffect(() => {
    async function loadExams() {
      console.log('[MockExamsPage] Loading finals for course:', courseCode)
      try {
        const data = await getCourseFinals(courseCode)
        console.log('[MockExamsPage] Loaded', data.length, 'finals')
        setExams(data)
      } catch (error) {
        console.error('Failed to load exams:', error)
      } finally {
        setLoading(false)
      }
    }
    loadExams()
  }, [courseCode])

  // Load user progress from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('claire_exam_progress')
    if (saved) {
      try {
        setUserProgress(JSON.parse(saved))
      } catch (e) {
        console.warn('Failed to parse exam progress')
      }
    }
  }, [])

  const handleStartExam = (examOrNormalized) => {
    if (onStartExam) {
      // Handle both raw exam objects (from ExamRow) and normalized objects (from RecommendedExamCard)
      if (examOrNormalized.exam_metadata) {
        // Normalized object - find the original exam
        const exam = exams.find(e => e.id === examOrNormalized.exam_metadata.exam_id)
        if (exam) {
          onStartExam(exam)
        }
      } else {
        // Raw exam object - use directly
        onStartExam(examOrNormalized)
      }
    }
  }

  const handleViewTopics = (normalizedExam) => {
    const exam = exams.find(e => e.id === normalizedExam.exam_metadata.exam_id)
    if (exam) {
      setViewTopicsExam(exam)
    }
  }

  // Find recommended exam (first not-started, newest)
  const recommendedExam = exams.find(e => !userProgress[e.id] || userProgress[e.id].status === 'not_started')

  // Build normalized object for RecommendedExamCard
  const normalizedRecommendedExam = recommendedExam ? {
    exam_metadata: {
      exam_id: recommendedExam.id,
      course_display: examCountdown?.course_display || recommendedExam.courseDisplay || 'Math 126',
      display_name: recommendedExam.displayName,
      source: 'Real UW past final',
      duration_minutes: recommendedExam.estimatedMinutes,
      total_points: recommendedExam.totalPoints,
      problem_count: recommendedExam.problemCount,
      part_count: recommendedExam.questionCount,
      topics: recommendedExam.topics,
    },
    recommendation_metadata: {
      recommendation_type: 'next_exam',
      reason: "A full past final is the best next step before your exam.",
      generated_from: {
        days_until_exam: examCountdown?.days_until || 14,
        roadmap_completion: 0.85, // mock
        weak_topics: ['double_integrals', 'taylor_series'], // mock
      },
    },
  } : null

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#0B1F3A] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex gap-8">
      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Mock Exams</h1>
          <p className="text-gray-600 mt-1">
            Practice with real past finals. Start a full exam, resume an attempt, or review your last result.
          </p>
        </div>

        {/* Recommended exam card */}
        {normalizedRecommendedExam && (
          <RecommendedExamCard
            normalizedExam={normalizedRecommendedExam}
            onStart={handleStartExam}
            onViewTopics={handleViewTopics}
          />
        )}

        {/* Section header */}
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Past Final Exams</h2>

        {/* Exam list */}
        <div className="space-y-3">
          {exams.map((exam) => (
            <ExamRow
              key={exam.id}
              exam={exam}
              onStart={handleStartExam}
              userProgress={userProgress[exam.id]}
              courseDisplay={examCountdown?.course_display || exam.courseDisplay}
            />
          ))}
        </div>

        {/* View all link */}
        {exams.length > 4 && (
          <div className="text-center mt-6">
            <button className="text-sm text-[#0B1F3A] hover:underline">
              View all past finals
            </button>
          </div>
        )}
      </div>

      {/* Right sidebar - only show if not hidden */}
      {!hideSidebar && <RightSidebar user={user} examCountdown={examCountdown} />}

      {/* View Topics Modal */}
      <ViewTopicsModal
        isOpen={!!viewTopicsExam}
        onClose={() => setViewTopicsExam(null)}
        examName={viewTopicsExam?.displayName || ''}
        problems={viewTopicsExam?.problems || []}
      />
    </div>
  )
}
