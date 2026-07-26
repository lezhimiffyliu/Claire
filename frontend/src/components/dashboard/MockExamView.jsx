/**
 * MockExamView - Full mock exam experience
 *
 * Uses existing ProblemPractice for each problem (QR upload, Claire feedback, etc.)
 * Just adds exam wrapper: timer, problem index sidebar
 */

import { useState, useEffect, useRef } from 'react'
import ProblemPractice from './ProblemPractice'

// Format time as MM:SS or HH:MM:SS
function formatTime(seconds) {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Problem status indicator
function ProblemIndicator({ number, status, isActive, onClick }) {
  const baseClasses = "w-10 h-10 rounded-lg flex items-center justify-center font-semibold text-sm cursor-pointer transition-all"

  let statusClasses = ""
  if (isActive) {
    statusClasses = "bg-[var(--claire-navy)] text-white ring-2 ring-[var(--claire-navy)] ring-offset-2"
  } else if (status === 'completed') {
    statusClasses = "bg-[var(--claire-teal)] text-white"
  } else if (status === 'flagged') {
    statusClasses = "bg-amber-100 text-amber-700 border-2 border-amber-400"
  } else {
    statusClasses = "bg-[var(--claire-gray-100)] text-[var(--claire-gray-600)] hover:bg-[var(--claire-gray-200)]"
  }

  return (
    <button
      onClick={onClick}
      className={`${baseClasses} ${statusClasses}`}
    >
      {number}
    </button>
  )
}

// Timer component with warning states
function ExamTimer({ totalSeconds, onTimeUp }) {
  const [remaining, setRemaining] = useState(totalSeconds)
  const intervalRef = useRef(null)

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) {
          clearInterval(intervalRef.current)
          onTimeUp?.()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(intervalRef.current)
  }, [])

  const isWarning = remaining < 600
  const isCritical = remaining < 120

  let timerClasses = "font-mono text-2xl font-bold"
  if (isCritical) {
    timerClasses += " text-red-600 animate-pulse"
  } else if (isWarning) {
    timerClasses += " text-amber-600"
  } else {
    timerClasses += " text-[var(--claire-navy)]"
  }

  return (
    <div className="text-center">
      <p className="text-xs text-[var(--claire-gray-500)] mb-1">Time Remaining</p>
      <p className={timerClasses}>{formatTime(remaining)}</p>
    </div>
  )
}

export default function MockExamView({ examName, problems, onExit, onSubmit }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [problemStatus, setProblemStatus] = useState({}) // { index: 'completed' | 'flagged' }
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false)

  const currentProblem = problems[currentIndex]
  const completedCount = Object.values(problemStatus).filter(s => s === 'completed').length

  // When user completes a problem in ProblemPractice, mark it and go to next
  const handleProblemComplete = () => {
    setProblemStatus(prev => ({ ...prev, [currentIndex]: 'completed' }))
    if (currentIndex < problems.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  // Back from ProblemPractice just goes to next problem (don't exit exam)
  const handleBackFromProblem = () => {
    if (currentIndex < problems.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleTimeUp = () => {
    onSubmit?.({ completedCount, totalProblems: problems.length })
  }

  const handleSubmitExam = () => {
    onSubmit?.({ completedCount, totalProblems: problems.length })
  }

  return (
    <div className="min-h-screen bg-[var(--claire-bg)] flex">
      {/* Left Sidebar - Exam Navigation */}
      <div className="w-64 bg-white border-r border-[var(--claire-gray-200)] flex flex-col flex-shrink-0">
        {/* Exam Header */}
        <div className="p-4 border-b border-[var(--claire-gray-200)]">
          <h2 className="font-bold text-[var(--claire-navy)]">{examName || 'Mock Exam'}</h2>
          <p className="text-sm text-[var(--claire-gray-500)]">{problems.length} problems</p>
        </div>

        {/* Timer */}
        <div className="p-4 border-b border-[var(--claire-gray-200)]">
          <ExamTimer totalSeconds={120 * 60} onTimeUp={handleTimeUp} />
        </div>

        {/* Problem Grid */}
        <div className="p-4 flex-1 overflow-auto">
          <p className="text-xs text-[var(--claire-gray-500)] mb-3">Problems</p>
          <div className="grid grid-cols-4 gap-2">
            {problems.map((_, idx) => (
              <ProblemIndicator
                key={idx}
                number={idx + 1}
                status={problemStatus[idx]}
                isActive={idx === currentIndex}
                onClick={() => setCurrentIndex(idx)}
              />
            ))}
          </div>

          {/* Legend */}
          <div className="mt-6 space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-[var(--claire-teal)]"></div>
              <span className="text-[var(--claire-gray-600)]">Completed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-[var(--claire-gray-100)]"></div>
              <span className="text-[var(--claire-gray-600)]">Not started</span>
            </div>
          </div>
        </div>

        {/* Progress & Actions */}
        <div className="p-4 border-t border-[var(--claire-gray-200)]">
          <p className="text-sm text-[var(--claire-gray-600)] mb-3">
            {completedCount} of {problems.length} completed
          </p>
          <button
            onClick={() => setShowSubmitConfirm(true)}
            className="w-full py-3 bg-[var(--claire-navy)] text-white font-bold rounded-lg hover:bg-[var(--claire-navy)]/90 transition-colors"
          >
            Submit Exam
          </button>
          <button
            onClick={onExit}
            className="w-full py-2 mt-2 text-[var(--claire-gray-500)] text-sm hover:text-[var(--claire-navy)]"
          >
            Save & Exit
          </button>
        </div>
      </div>

      {/* Main Content - Reuse ProblemPractice */}
      <div className="flex-1 overflow-auto">
        <ProblemPractice
          key={currentProblem.id}
          problem={currentProblem}
          onBack={handleBackFromProblem}
          isExamMode={true}
        />
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-[var(--claire-navy)] mb-2">Submit Exam?</h3>
            <p className="text-[var(--claire-gray-600)] mb-4">
              You have completed {completedCount} of {problems.length} problems.
              {completedCount < problems.length && (
                <span className="text-amber-600 block mt-1">
                  {problems.length - completedCount} problems not completed.
                </span>
              )}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowSubmitConfirm(false)}
                className="flex-1 py-3 border border-[var(--claire-gray-200)] text-[var(--claire-gray-600)] rounded-lg hover:bg-[var(--claire-gray-50)]"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitExam}
                className="flex-1 py-3 bg-[var(--claire-navy)] text-white rounded-lg hover:bg-[var(--claire-navy)]/90"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
