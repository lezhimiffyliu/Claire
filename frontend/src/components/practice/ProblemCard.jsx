/**
 * ProblemCard - Display a single problem for practice
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import katex from 'katex'
import 'katex/dist/katex.min.css'

// Render LaTeX math
function MathText({ text }) {
  if (!text) return null

  // Handle display math ($$...$$)
  let processed = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, math) => {
    try {
      return katex.renderToString(math.trim(), {
        throwOnError: false,
        displayMode: true,
      })
    } catch {
      return match
    }
  })

  // Handle inline math ($...$)
  processed = processed.replace(/\$([^$]+?)\$/g, (match, math) => {
    try {
      return katex.renderToString(math.trim(), {
        throwOnError: false,
        displayMode: false,
      })
    } catch {
      return match
    }
  })

  return (
    <div
      className="math-content leading-relaxed"
      dangerouslySetInnerHTML={{ __html: processed }}
    />
  )
}

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

function ProblemCard({ problem, partIndex = 0, onNext, onShowAnswer }) {
  const [showAnswer, setShowAnswer] = useState(false)
  const part = problem.parts?.[partIndex]

  // 生成显示用的标签
  const sourceLabel = `${formatExamName(problem.exam)} - Problem ${problem.problem_number}`
  const topicDisplay = formatTopicName(problem.topic)

  const handleShowAnswer = () => {
    setShowAnswer(true)
    onShowAnswer?.()
  }

  const handleNext = () => {
    setShowAnswer(false)
    onNext?.()
  }

  return (
    <motion.div
      className="bg-white rounded-2xl shadow-lg overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-blue-100 text-sm">{sourceLabel}</span>
            <h2 className="text-white font-bold text-lg mt-1">
              {topicDisplay}
            </h2>
          </div>
          <div className="text-right">
            <span className="bg-white/20 text-white text-sm px-3 py-1 rounded-full">
              {problem.points} pts
            </span>
          </div>
        </div>
      </div>

      {/* Problem content */}
      <div className="p-6">
        {/* Stem (shared instruction) */}
        {problem.stem && (
          <div className="mb-4 text-gray-600 text-sm border-l-4 border-blue-200 pl-4">
            <MathText text={problem.stem} />
          </div>
        )}

        {/* Part label */}
        {part.label && (
          <span className="inline-block bg-blue-100 text-blue-700 text-sm font-bold px-2 py-1 rounded mb-3">
            Part ({part.label})
          </span>
        )}

        {/* Question text */}
        <div className="text-gray-800 text-lg mb-6">
          <MathText text={part.question_text} />
        </div>

        {/* Diagram if available */}
        {part.has_diagram && part.diagram_image_url && (
          <div className="mb-6">
            <img
              src={part.diagram_image_url}
              alt="Problem diagram"
              className="max-w-full rounded-lg border border-gray-200"
            />
          </div>
        )}

        {/* Concepts/Tags */}
        {problem.concepts && problem.concepts.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {problem.concepts.map((concept, i) => (
              <span
                key={i}
                className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded"
              >
                {concept.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}

        {/* Answer section */}
        {showAnswer ? (
          <motion.div
            className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
          >
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-green-800 font-semibold mb-1">Answer</p>
                <div className="text-green-700">
                  <MathText text={part.final_answer} />
                </div>
              </div>
            </div>
          </motion.div>
        ) : null}

        {/* Action buttons */}
        <div className="flex gap-3">
          {!showAnswer ? (
            <button
              onClick={handleShowAnswer}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-xl transition-colors"
            >
              Show Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-xl transition-colors"
            >
              Next Problem
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default ProblemCard
