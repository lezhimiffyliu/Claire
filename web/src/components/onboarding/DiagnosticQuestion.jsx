import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const pageVariants = {
  initial: (direction) => ({
    x: direction > 0 ? '100%' : '-100%',
    opacity: 0,
  }),
  animate: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.2, ease: 'easeOut' },
  },
  exit: (direction) => ({
    x: direction > 0 ? '-100%' : '100%',
    opacity: 0,
    transition: { duration: 0.15, ease: 'easeIn' },
  }),
}

// Render LaTeX using KaTeX
function MathText({ text }) {
  if (!text) return null

  const renderMath = (str) => {
    const parts = str.split(/(\$[^$]+\$)/g)

    return parts.map((part, i) => {
      if (part.startsWith('$') && part.endsWith('$')) {
        const math = part.slice(1, -1)
        try {
          const html = katex.renderToString(math, {
            throwOnError: false,
            displayMode: false,
            strict: false,
          })
          return (
            <span
              key={i}
              className="mx-0.5"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          )
        } catch (e) {
          return (
            <span key={i} className="font-mono">
              {math}
            </span>
          )
        }
      }
      return <span key={i}>{part}</span>
    })
  }

  return <span className="math-text">{renderMath(text)}</span>
}

function DiagnosticQuestion({
  direction,
  question,
  questionNumber,
  totalQuestions,
  onAnswerSubmit,
  onNext,
  course,
}) {
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [hasChecked, setHasChecked] = useState(false)
  const [isCorrect, setIsCorrect] = useState(null)
  const [isSkipped, setIsSkipped] = useState(false)

  useEffect(() => {
    setSelectedAnswer(null)
    setHasChecked(false)
    setIsCorrect(null)
    setIsSkipped(false)
  }, [question.id])

  const handleCheck = () => {
    if (selectedAnswer === null) return

    const correct = selectedAnswer === question.correct
    setIsCorrect(correct)
    setHasChecked(true)
    onAnswerSubmit(question.id, correct, false)
  }

  const handleSkip = () => {
    setIsSkipped(true)
    setHasChecked(true)
    setIsCorrect(false)
    onAnswerSubmit(question.id, false, true)
  }

  const handleContinue = () => {
    onNext()
  }

  const courseLabels = {
    math124: 'MATH 124',
    math125: 'MATH 125',
    math126: 'MATH 126',
  }

  const progressPercent = (questionNumber / totalQuestions) * 100

  return (
    <motion.div
      custom={direction}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex-1 flex flex-col min-h-0"
    >
      {/* Question area */}
      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-44 min-h-0">
        <div className="w-full max-w-lg mx-auto">
          {/* Progress bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
                {courseLabels[course]}
              </span>
              <span className="text-xs text-[var(--claire-gray-400)]">
                {questionNumber} / {totalQuestions}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* SVG diagram if present */}
          {question.svg && (
            <motion.div
              className="mb-6 flex justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              dangerouslySetInnerHTML={{ __html: question.svg }}
            />
          )}

          {/* Question text */}
          <h2 className="text-xl md:text-2xl font-semibold text-[var(--claire-navy)] mb-8 leading-relaxed">
            <MathText text={question.question} />
          </h2>

          {/* Answer options */}
          <div className="space-y-3">
            {question.options.map((option, index) => {
              let optionClass = 'option-card'

              if (hasChecked && !isSkipped) {
                if (index === question.correct) {
                  optionClass += ' correct'
                } else if (index === selectedAnswer && !isCorrect) {
                  optionClass += ' incorrect'
                }
              } else if (isSkipped && index === question.correct) {
                optionClass += ' correct'
              } else if (selectedAnswer === index) {
                optionClass += ' selected'
              }

              return (
                <motion.button
                  key={index}
                  onClick={() => !hasChecked && setSelectedAnswer(index)}
                  className={`${optionClass} w-full text-left flex items-center gap-4 ${
                    hasChecked ? 'cursor-default' : ''
                  }`}
                  disabled={hasChecked}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + index * 0.05 }}
                >
                  {/* Letter badge */}
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center font-semibold text-lg shrink-0 transition-colors ${
                      (hasChecked || isSkipped) && index === question.correct
                        ? 'bg-[var(--claire-teal)] text-white'
                        : hasChecked && index === selectedAnswer && !isCorrect
                        ? 'bg-[var(--claire-weak)] text-white'
                        : selectedAnswer === index
                        ? 'bg-[var(--claire-next)] text-white'
                        : 'bg-[var(--claire-gray-100)] text-[var(--claire-gray-500)]'
                    }`}
                  >
                    {String.fromCharCode(65 + index)}
                  </div>

                  {/* Option text */}
                  <div className="flex-1 font-medium text-[var(--claire-gray-900)]">
                    <MathText text={option} />
                  </div>

                  {/* Check/X icon when checked */}
                  {(hasChecked || isSkipped) && index === question.correct && (
                    <div className="shrink-0">
                      <svg
                        className="w-5 h-5 text-[var(--claire-teal)]"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                  {hasChecked &&
                    !isSkipped &&
                    index === selectedAnswer &&
                    !isCorrect && (
                      <div className="shrink-0">
                        <svg
                          className="w-5 h-5 text-[var(--claire-weak)]"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    )}
                </motion.button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Bottom action bar */}
      <AnimatePresence mode="wait">
        {!hasChecked ? (
          <motion.div
            key="check"
            className="fixed bottom-0 left-0 right-0 bg-white border-t border-[var(--claire-gray-200)] p-4 safe-bottom"
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            transition={{ duration: 0.2 }}
          >
            <div className="max-w-lg mx-auto flex gap-3">
              <button onClick={handleSkip} className="btn-ghost px-6">
                SKIP
              </button>
              <button
                onClick={handleCheck}
                disabled={selectedAnswer === null}
                className={`flex-1 ${
                  selectedAnswer !== null ? 'btn-primary' : 'btn-ghost opacity-50'
                }`}
              >
                CHECK
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="feedback"
            className={`fixed bottom-0 left-0 right-0 p-4 safe-bottom border-t ${
              isSkipped
                ? 'bg-[var(--claire-gray-100)] border-[var(--claire-gray-300)]'
                : isCorrect
                ? 'bg-[var(--claire-teal-muted)] border-[var(--claire-teal)]'
                : 'bg-[var(--claire-weak-bg)] border-[var(--claire-weak)]'
            }`}
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            transition={{ duration: 0.2 }}
          >
            <div className="max-w-lg mx-auto">
              {/* Feedback message */}
              <div className="flex items-start gap-3 mb-4">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    isSkipped
                      ? 'bg-[var(--claire-gray-400)]'
                      : isCorrect
                      ? 'bg-[var(--claire-teal)]'
                      : 'bg-[var(--claire-weak)]'
                  }`}
                >
                  {isSkipped ? (
                    <svg
                      className="w-4 h-4 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 5l7 7-7 7M5 5l7 7-7 7"
                      />
                    </svg>
                  ) : isCorrect ? (
                    <svg
                      className="w-4 h-4 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-4 h-4 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <div className="flex-1">
                  <h3
                    className={`font-semibold text-base ${
                      isSkipped
                        ? 'text-[var(--claire-gray-700)]'
                        : isCorrect
                        ? 'text-[var(--claire-teal)]'
                        : 'text-[var(--claire-weak)]'
                    }`}
                  >
                    {isSkipped ? 'Skipped' : isCorrect ? 'Correct' : 'Incorrect'}
                  </h3>
                  <p className="text-sm text-[var(--claire-gray-600)] mt-1">
                    {isSkipped && (
                      <span>
                        Answer: {String.fromCharCode(65 + question.correct)}.{' '}
                      </span>
                    )}
                    <MathText text={question.explanation} />
                  </p>
                </div>
              </div>

              {/* Continue button */}
              <button
                onClick={handleContinue}
                className={`w-full ${
                  isCorrect ? 'btn-secondary' : 'btn-primary'
                }`}
              >
                CONTINUE
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default DiagnosticQuestion
