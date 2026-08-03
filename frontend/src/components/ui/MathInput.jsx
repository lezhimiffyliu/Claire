import { useState, useRef, useEffect } from 'react'
import katex from 'katex'

/**
 * MathInput - Simple math input with clickable keyboard and live preview
 * Uses KaTeX for rendering (already in the project)
 */
export default function MathInput({
  value = '',
  onChange,
  placeholder = 'Type your answer...',
  className = '',
  disabled = false,
}) {
  const [text, setText] = useState(value)
  const [showKeyboard, setShowKeyboard] = useState(true)
  const [preview, setPreview] = useState('')
  const inputRef = useRef(null)

  // Update preview when text changes
  useEffect(() => {
    if (!text.trim()) {
      setPreview('')
      return
    }

    try {
      const html = katex.renderToString(text, {
        throwOnError: false,
        displayMode: false,
      })
      setPreview(html)
    } catch (e) {
      setPreview('')
    }
  }, [text])

  // Notify parent of changes
  useEffect(() => {
    onChange?.({ latex: text, text })
  }, [text, onChange])

  // Insert text at cursor position
  const insertAtCursor = (insertText, moveCursorBack = 0) => {
    const input = inputRef.current
    if (!input) return

    const start = input.selectionStart
    const end = input.selectionEnd
    const before = text.substring(0, start)
    const after = text.substring(end)

    const newText = before + insertText + after
    setText(newText)

    // Set cursor position after React updates
    setTimeout(() => {
      const newPos = start + insertText.length - moveCursorBack
      input.focus()
      input.setSelectionRange(newPos, newPos)
    }, 0)
  }

  // Wrap selection with prefix/suffix
  const wrapSelection = (prefix, suffix = '') => {
    const input = inputRef.current
    if (!input) return

    const start = input.selectionStart
    const end = input.selectionEnd
    const selected = text.substring(start, end)
    const before = text.substring(0, start)
    const after = text.substring(end)

    if (selected) {
      // Wrap selected text
      const newText = before + prefix + selected + suffix + after
      setText(newText)
      setTimeout(() => {
        input.focus()
        input.setSelectionRange(start + prefix.length, end + prefix.length)
      }, 0)
    } else {
      // Insert with placeholder
      const placeholder = prefix + '□' + suffix
      insertAtCursor(placeholder, suffix.length + 1)
    }
  }

  // Keyboard buttons
  const buttons = [
    // Row 1: Powers & roots
    [
      { label: 'x²', action: () => insertAtCursor('^2') },
      { label: 'xⁿ', action: () => insertAtCursor('^{}', 1) },
      { label: '√', action: () => wrapSelection('\\sqrt{', '}') },
      { label: 'ⁿ√', action: () => insertAtCursor('\\sqrt[]{}', 3) },
      { label: 'a/b', action: () => insertAtCursor('\\frac{}{}', 3) },
      { label: '|x|', action: () => wrapSelection('|', '|') },
    ],
    // Row 2: Calculus
    [
      { label: '∫', action: () => insertAtCursor('\\int ') },
      { label: '∫ᵇₐ', action: () => insertAtCursor('\\int_{}^{} ', 5) },
      { label: 'd/dx', action: () => insertAtCursor('\\frac{d}{dx}') },
      { label: '∂', action: () => insertAtCursor('\\partial ') },
      { label: 'lim', action: () => insertAtCursor('\\lim_{x \\to }', 1) },
      { label: '∑', action: () => insertAtCursor('\\sum_{}^{}', 4) },
    ],
    // Row 3: Functions
    [
      { label: 'sin', action: () => insertAtCursor('\\sin()' , 1) },
      { label: 'cos', action: () => insertAtCursor('\\cos()', 1) },
      { label: 'tan', action: () => insertAtCursor('\\tan()', 1) },
      { label: 'ln', action: () => insertAtCursor('\\ln()', 1) },
      { label: 'eˣ', action: () => insertAtCursor('e^{}', 1) },
      { label: 'log', action: () => insertAtCursor('\\log()', 1) },
    ],
    // Row 4: Symbols
    [
      { label: 'π', action: () => insertAtCursor('\\pi ') },
      { label: 'θ', action: () => insertAtCursor('\\theta ') },
      { label: '∞', action: () => insertAtCursor('\\infty ') },
      { label: '±', action: () => insertAtCursor('\\pm ') },
      { label: '→', action: () => insertAtCursor('\\to ') },
      { label: '≠', action: () => insertAtCursor('\\neq ') },
    ],
    // Row 5: Comparisons & subscript
    [
      { label: '≤', action: () => insertAtCursor('\\leq ') },
      { label: '≥', action: () => insertAtCursor('\\geq ') },
      { label: 'xₙ', action: () => insertAtCursor('_{}', 1) },
      { label: '()', action: () => wrapSelection('(', ')') },
      { label: '[]', action: () => wrapSelection('[', ']') },
      { label: '{}', action: () => wrapSelection('\\{', '\\}') },
    ],
  ]

  return (
    <div className={className}>
      {/* Input field */}
      <div className="relative">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          rows={2}
          className="w-full px-4 py-3 text-base font-mono border-2 border-gray-200 rounded-xl focus:border-[#5B8DEF] focus:outline-none resize-none disabled:opacity-50 disabled:bg-gray-50"
          style={{ fontFamily: 'ui-monospace, monospace' }}
        />
      </div>

      {/* Live preview */}
      {preview && (
        <div className="mt-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-lg">
          <span className="text-xs text-blue-500 font-medium mr-2">Preview:</span>
          <span
            className="text-lg text-gray-800"
            dangerouslySetInnerHTML={{ __html: preview }}
          />
        </div>
      )}

      {/* Keyboard toggle */}
      <button
        type="button"
        onClick={() => setShowKeyboard(!showKeyboard)}
        className="mt-2 flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
      >
        <svg
          className={`w-4 h-4 transition-transform ${showKeyboard ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        {showKeyboard ? 'Hide keyboard' : 'Show math keyboard'}
      </button>

      {/* Virtual keyboard */}
      {showKeyboard && (
        <div className="mt-2 p-3 bg-gray-50 rounded-xl border border-gray-200">
          <div className="space-y-1.5">
            {buttons.map((row, ri) => (
              <div key={ri} className="flex gap-1 justify-center flex-wrap">
                {row.map((btn, bi) => (
                  <button
                    key={bi}
                    type="button"
                    onClick={btn.action}
                    disabled={disabled}
                    className="px-2.5 py-1.5 min-w-[42px] bg-white border border-gray-200 rounded-lg text-gray-700 font-medium text-sm hover:bg-gray-100 hover:border-gray-300 active:bg-gray-200 disabled:opacity-40 transition-colors"
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            ))}
          </div>

          <div className="mt-2.5 pt-2.5 border-t border-gray-200 flex items-center justify-between text-xs text-gray-400">
            <span>Click buttons or type LaTeX directly</span>
            <button
              type="button"
              onClick={() => {
                setText('')
                inputRef.current?.focus()
              }}
              className="hover:text-gray-600"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
