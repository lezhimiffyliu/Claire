/**
 * WorkAreaCard - Simple, natural work area
 *
 * NOT a submission form. NOT a workflow step.
 * Just a quiet place to work, with an option to show Claire.
 */
import { useState } from 'react'

export default function WorkAreaCard({
  onShowClaire,
  onMessage,
  loading,
}) {
  const [inputValue, setInputValue] = useState('')

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && inputValue.trim()) {
      e.preventDefault()
      onMessage?.(inputValue.trim())
      setInputValue('')
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-medium text-gray-800 mb-1">Work on paper</h3>
      <p className="text-sm text-gray-500 mb-5">
        Work through the problem like you would on an exam.
      </p>

      <button
        onClick={onShowClaire}
        disabled={loading}
        className="px-4 py-2.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 mb-4"
      >
        {loading ? 'Loading...' : 'Show Claire your work'}
      </button>

      {/* Simple input for asking Claire */}
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Write the next step, or ask Claire..."
        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-gray-300"
      />
    </div>
  )
}
