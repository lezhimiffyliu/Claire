/**
 * PastExamsView - Mock Exam Mode
 *
 * Design principles (v3):
 * - Clean, restrained visual style
 * - No cherry-picking - must complete full exams
 * - Charcoal primary buttons, subtle status badges
 */

// Hardcoded exam history data
const EXAM_HISTORY = [
  { id: 'wi25', name: 'Winter 2025', status: 'in_progress', score: null, progress: '3/8' },
  { id: 'sp25', name: 'Spring 2025', status: 'not_started', score: null },
  { id: 'wi24', name: 'Winter 2024', status: 'completed', score: 72 },
]

// Status badge component
function StatusBadge({ status, score }) {
  const config = {
    completed: {
      className: 'status-label success',
      label: score ? `${score}%` : 'Done',
    },
    in_progress: {
      className: 'status-label info',
      label: 'In Progress',
    },
    not_started: {
      className: 'px-2 py-0.5 rounded text-xs font-medium bg-[var(--claire-bg)] text-[var(--claire-text-muted)]',
      label: 'Not Started',
    },
  }

  const { className, label } = config[status] || config.not_started

  return (
    <span className={className}>
      {label}
    </span>
  )
}

// Continue Exam Card
function ContinueExamCard({ exam, onResume }) {
  return (
    <div className="card-standard border-[var(--claire-charcoal)]">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-[var(--claire-charcoal)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            </svg>
            <span className="text-sm font-medium text-[var(--claire-text-secondary)]">Continue</span>
          </div>
          <h2 className="text-xl font-semibold text-[var(--claire-text-primary)]">
            {exam.name}
          </h2>
          <p className="text-sm text-[var(--claire-text-muted)] mt-1">
            {exam.progress || '3/8'} completed
          </p>
        </div>
        <button
          onClick={onResume}
          className="btn-hero py-3 px-6"
        >
          Resume
        </button>
      </div>
    </div>
  )
}

// Exam History Row
function ExamRow({ exam, onSelect }) {
  const isClickable = exam.status !== 'not_started'

  return (
    <button
      className={`
        w-full flex items-center justify-between p-4 rounded-xl border
        text-left transition-all duration-200
        ${isClickable
          ? 'bg-[var(--claire-bg-card)] border-[var(--claire-border)] hover:border-[var(--claire-text-muted)] cursor-pointer'
          : 'bg-[var(--claire-bg)] border-[var(--claire-border-light)] cursor-default opacity-75'
        }
      `}
      onClick={isClickable ? () => onSelect(exam) : undefined}
      disabled={!isClickable}
    >
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-full bg-[var(--claire-bg)] flex items-center justify-center">
          {exam.status === 'completed' ? (
            <svg className="w-5 h-5 text-[var(--claire-success)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          ) : exam.status === 'in_progress' ? (
            <svg className="w-5 h-5 text-[var(--claire-info)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-[var(--claire-text-muted)]" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
        </div>
        <div>
          <h3 className="font-medium text-[var(--claire-text-primary)]">{exam.name}</h3>
          <p className="text-sm text-[var(--claire-text-muted)]">8 problems</p>
        </div>
      </div>
      <StatusBadge status={exam.status} score={exam.score} />
    </button>
  )
}

export default function PastExamsView({ onPractice }) {
  // Find in-progress exam
  const inProgressExam = EXAM_HISTORY.find(e => e.status === 'in_progress')

  const handleStartNewExam = () => {
    if (onPractice) {
      onPractice({ id: 'new_exam', isNewExam: true })
    }
  }

  const handleResumeExam = () => {
    if (onPractice) {
      onPractice({ id: 'resume_exam', isResumeExam: true })
    }
  }

  const handleSelectExam = (exam) => {
    if (exam.status === 'completed') {
      console.log('View exam results:', exam.id)
    } else if (exam.status === 'in_progress') {
      handleResumeExam()
    }
  }

  return (
    <div className="max-w-2xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--claire-text-primary)]">Practice</h1>
        <p className="text-[var(--claire-text-secondary)] mt-1">
          Full mock exams with real past problems
        </p>
      </div>

      {/* Continue Exam Card (if in progress) */}
      {inProgressExam && (
        <div className="mb-6">
          <ContinueExamCard exam={inProgressExam} onResume={handleResumeExam} />
        </div>
      )}

      {/* Start New Exam Button */}
      <div className="mb-10">
        <button
          onClick={handleStartNewExam}
          className="w-full btn-hero flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Start New Exam
        </button>
      </div>

      {/* Exam History */}
      <div>
        <h2 className="text-section mb-4">History</h2>
        <div className="space-y-3">
          {EXAM_HISTORY.map((exam) => (
            <ExamRow
              key={exam.id}
              exam={exam}
              onSelect={handleSelectExam}
            />
          ))}
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-10 p-4 card-subtle">
        <div className="flex gap-3">
          <svg className="w-5 h-5 text-[var(--claire-text-muted)] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="font-medium text-[var(--claire-text-primary)]">How it works</h3>
            <p className="text-sm text-[var(--claire-text-secondary)] mt-1">
              Each exam contains 8 problems from real UW past exams.
              Work through them one at a time with guidance when needed.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
