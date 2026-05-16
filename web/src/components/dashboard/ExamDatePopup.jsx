import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { saveStudentPreferences } from '../../api/problemApi'

const EXAM_OPTIONS = [
  { id: 'midterm_1', label: 'Midterm I' },
  { id: 'midterm_2', label: 'Midterm II' },
  { id: 'final', label: 'Final' },
]

/**
 * ExamDatePopup - Collects exam type and date from student
 *
 * Asks two questions:
 * 1. Which exam are you preparing for? (Midterm I / Midterm II / Final)
 * 2. When is the exam? (date picker)
 *
 * Returns { examType, examDate, daysUntil } via onSave callback
 */
export default function ExamDatePopup({ isOpen, onClose, onSave }) {
  const [examType, setExamType] = useState('')
  const [date, setDate] = useState('')
  const [saving, setSaving] = useState(false)

  // Load existing values from localStorage when opened
  useEffect(() => {
    if (isOpen) {
      const savedType = localStorage.getItem('claire_exam_type')
      const savedDate = localStorage.getItem('claire_exam_date')

      if (savedType) {
        setExamType(savedType)
      }

      if (savedDate) {
        setDate(savedDate)
      } else {
        // Default to 2 weeks from now if no saved date
        const twoWeeksFromNow = new Date()
        twoWeeksFromNow.setDate(twoWeeksFromNow.getDate() + 14)
        setDate(twoWeeksFromNow.toISOString().split('T')[0])
      }
    }
  }, [isOpen])

  const handleSave = async () => {
    if (!examType || !date) return
    setSaving(true)

    // Get display label
    const examLabel = EXAM_OPTIONS.find(e => e.id === examType)?.label || examType

    // Calculate days until exam
    const examDateObj = new Date(date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const daysUntil = Math.ceil((examDateObj - today) / (1000 * 60 * 60 * 24))

    // Save to backend (for logged-in users) and localStorage (fallback)
    try {
      await saveStudentPreferences({
        exam_type: examType,
        exam_date: date,
      })
    } catch (e) {
      // If API fails (e.g., not logged in), fall back to localStorage only
      console.log('Saving to localStorage only:', e.message)
    }

    // Always save to localStorage as fallback
    localStorage.setItem('claire_exam_type', examType)
    localStorage.setItem('claire_exam_label', examLabel)
    localStorage.setItem('claire_exam_date', date)

    setSaving(false)
    onSave({
      examType,
      examLabel,
      examDate: date,
      daysUntil,
    })
    onClose()
  }

  // Calculate days until exam for preview
  const getDaysUntil = () => {
    if (!date) return null
    const examDate = new Date(date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const diffTime = examDate - today
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const daysUntil = getDaysUntil()
  const canSave = examType && date && (daysUntil === null || daysUntil >= 0)

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl"
          >
            {/* Header */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-[var(--claire-navy)]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-[var(--claire-navy)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-[var(--claire-navy)] mb-2">
                Set up your exam
              </h2>
              <p className="text-gray-500 text-sm">
                We'll create a personalized study plan based on your timeline.
              </p>
            </div>

            {/* Exam Type Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Which exam are you preparing for?
              </label>
              <select
                value={examType}
                onChange={(e) => setExamType(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-[var(--claire-navy)] focus:border-transparent bg-white"
              >
                <option value="">Select exam...</option>
                {EXAM_OPTIONS.map((exam) => (
                  <option key={exam.id} value={exam.id}>
                    {exam.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                When is the exam?
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full p-3 border border-gray-200 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-[var(--claire-navy)] focus:border-transparent"
              />
            </div>

            {/* Days preview - simple, no scary colors */}
            {daysUntil !== null && daysUntil >= 0 && (
              <div className="text-center py-3 px-4 rounded-lg mb-4 bg-gray-50 text-gray-600">
                <span className="font-medium">{daysUntil} days until exam</span>
              </div>
            )}

            {/* Past date warning */}
            {daysUntil !== null && daysUntil < 0 && (
              <div className="text-center py-3 px-4 rounded-lg mb-4 bg-gray-50 text-gray-500">
                <span>This date has passed. Please select a future date.</span>
              </div>
            )}

            {/* Action buttons */}
            <div className="space-y-3">
              <button
                onClick={handleSave}
                disabled={!canSave || saving}
                className={`w-full py-3.5 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ${
                  canSave && !saving
                    ? 'bg-[var(--claire-navy)] text-white hover:opacity-90'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {saving ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Continue'
                )}
              </button>

              <button
                onClick={onClose}
                className="w-full py-3 text-gray-500 hover:text-gray-700 text-sm transition-colors"
              >
                Skip for now
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
