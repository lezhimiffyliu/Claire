import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { saveStudentPreferences } from '../../api/problemApi'

/**
 * PrepLevelPopup - Collects preparation level from student
 *
 * Four-tier system for honest self-assessment:
 * 1. no_class_no_homework - Missed most classes/homework
 * 2. some_class_some_homework - Sporadic attendance
 * 3. attended_but_weak - Attended but feel weak
 * 4. confident_need_practice - Confident, need practice
 */

const PREP_LEVELS = [
  {
    id: 'no_class_no_homework',
    emoji: '😭',
    label: 'Missed most classes & homework',
    description: "No judgment - let's get you caught up!",
    tier: 1,
  },
  {
    id: 'some_class_some_homework',
    emoji: '😐',
    label: 'Missed some lectures',
    description: 'Some gaps to fill, but not starting from zero',
    tier: 2,
  },
  {
    id: 'attended_but_weak',
    emoji: '🤔',
    label: 'Attended but feeling weak',
    description: 'Concepts heard but not solid yet',
    tier: 3,
  },
  {
    id: 'confident_need_practice',
    emoji: '💪',
    label: 'Confident, need practice',
    description: 'Just need to build fluency',
    tier: 4,
  },
]

export default function PrepLevelPopup({ isOpen, onClose, onSave }) {
  const [selected, setSelected] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!selected) return
    setSaving(true)

    // Save to localStorage
    localStorage.setItem('claire_prep_level', selected)

    // Save to backend (if authenticated)
    try {
      await saveStudentPreferences({ prep_level: selected })
    } catch (e) {
      console.log('Backend save skipped (anonymous user or error):', e.message)
    }

    setSaving(false)
    onSave(selected)
    onClose()
  }

  const selectedLevel = PREP_LEVELS.find(l => l.id === selected)

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
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-[var(--claire-navy)] mb-2">
                How prepared do you feel?
              </h2>
              <p className="text-gray-500 text-sm">
                Be honest - this helps us create the right study plan for you.
              </p>
            </div>

            {/* Options */}
            <div className="space-y-3 mb-6">
              {PREP_LEVELS.map((level) => (
                <button
                  key={level.id}
                  onClick={() => setSelected(level.id)}
                  className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                    selected === level.id
                      ? 'border-[var(--claire-navy)] bg-[var(--claire-navy)]/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{level.emoji}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-800">
                        {level.label}
                      </div>
                    </div>
                    {selected === level.id && (
                      <svg className="w-5 h-5 text-[var(--claire-navy)]" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Selected description */}
            {selectedLevel && (
              <div className="text-center py-3 px-4 bg-blue-50 text-blue-700 rounded-lg mb-4 text-sm">
                {selectedLevel.description}
              </div>
            )}

            {/* Action buttons */}
            <div className="space-y-3">
              <button
                onClick={handleSave}
                disabled={!selected || saving}
                className={`w-full py-3.5 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ${
                  selected && !saving
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
