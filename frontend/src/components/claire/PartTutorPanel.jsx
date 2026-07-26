/**
 * PartTutorPanel - Teaching card for each problem part
 *
 * Shows ONE card at a time (not a chat transcript).
 * Chat input always visible - agent decides what to do after each message.
 */
import { useState } from 'react'
import MathText from '../ui/MathText'

export default function PartTutorPanel({
  panelState = 'ready',  // ready | upload | teaching
  partLabel = 'a',
  threadEvents = [],
  loading = false,
  onAction,
  onSendMessage,
  onBackToReady,
  qrUrl,
  qrLoading,
  qrStatus,
  qrError,
  onRetryQR,
}) {
  const [inputValue, setInputValue] = useState('')

  // Get only the LATEST Claire event
  const latestClaireEvent = threadEvents
    .filter(e => e.role === 'claire')
    .slice(-1)[0]

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage?.(inputValue.trim())
      setInputValue('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickReply = (reply) => {
    onSendMessage?.(reply)
  }

  return (
    <div className="bg-white rounded-2xl border-2 border-[var(--claire-ai)] overflow-hidden">
      <div className="p-6">
        {/* Ready State */}
        {panelState === 'ready' && !loading && (
          <ReadyCard partLabel={partLabel} onAction={onAction} />
        )}

        {/* Loading State */}
        {loading && (
          <LoadingCard />
        )}

        {/* Teaching State - Latest Claire response only */}
        {panelState === 'teaching' && !loading && latestClaireEvent && (
          <TeachingCard
            event={latestClaireEvent}
            onQuickReply={handleQuickReply}
          />
        )}

        {/* Upload State */}
        {panelState === 'upload' && !loading && (
          <UploadCard
            qrUrl={qrUrl}
            qrLoading={qrLoading}
            qrStatus={qrStatus}
            qrError={qrError}
            onRetry={onRetryQR}
          />
        )}
      </div>

      {/* Chat Input - ALWAYS visible */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Write the next step, or ask Claire..."
          className="w-full px-4 py-3 mb-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--claire-ai)] focus:border-transparent"
        />
        <div className="flex items-center justify-between">
          {panelState === 'teaching' && onBackToReady ? (
            <button onClick={onBackToReady} className="text-sm text-gray-400 hover:text-gray-600">
              Back to submit area
            </button>
          ) : (
            <div />
          )}
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="px-4 py-2 text-sm font-medium bg-[var(--claire-navy)] text-white rounded-lg disabled:opacity-50 hover:opacity-90 transition-opacity"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * ReadyCard
 */
function ReadyCard({ partLabel, onAction }) {
  return (
    <div>
      <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
        Claire asks
      </p>
      <p className="text-lg text-[var(--claire-navy)] mb-4">
        Ready to work on part ({partLabel})? What would you like to do?
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onAction('done')}
          className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
        >
          All done, check my answer
        </button>
        <button
          onClick={() => onAction('stuck')}
          className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
        >
          I'm stuck
        </button>
        <button
          onClick={() => onAction('hint')}
          className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
        >
          Give me a hint
        </button>
      </div>
    </div>
  )
}

/**
 * LoadingCard
 */
function LoadingCard() {
  return (
    <div>
      <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
        Claire
      </p>
      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-2 h-2 bg-[var(--claire-ai)] rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
        <span className="text-sm text-gray-500">Thinking...</span>
      </div>
    </div>
  )
}

/**
 * Try to parse JSON from text and extract meaningful content
 */
function tryParseJsonResponse(text) {
  if (!text || typeof text !== 'string') return null

  // Check if text looks like JSON
  const trimmed = text.trim()
  if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) return null

  try {
    const parsed = JSON.parse(trimmed)

    // Handle { question, hints } format
    if (parsed.question || parsed.hints) {
      return {
        question: parsed.question || '',
        hints: Array.isArray(parsed.hints) ? parsed.hints : [],
      }
    }

    // Handle { message, ... } format
    if (parsed.message) {
      return {
        question: parsed.message,
        hints: parsed.hints || parsed.quickReplies || [],
      }
    }

    // Handle { text, ... } format
    if (parsed.text) {
      return {
        question: parsed.text,
        hints: parsed.hints || [],
      }
    }

    return null
  } catch (e) {
    return null
  }
}

/**
 * TeachingCard - Latest Claire response
 *
 * Handles both:
 * - teaching_action type (from hook conversion of teaching_card events)
 * - Legacy say/ask_back/concept_card formats
 * - JSON responses that need parsing
 *
 * Default flow:
 *   concept bridge → next micro-step question → free input
 *
 * Quick replies are OPTIONAL - agent decides when to include them:
 *   - Student stuck multiple times
 *   - Need concept branching
 *   - Post-upload error analysis
 */
function TeachingCard({ event, onQuickReply }) {
  // Teaching Action format (from unified pipeline teaching_card event)
  // The hook converts teaching_card to type: 'teaching_action' for consistency
  if (event.type === 'teaching_action') {
    const { conceptBridge, nextMicroStep, quickReplies } = event
    // Agent decides whether to include quickReplies - frontend just renders if present
    const hasQuickReplies = quickReplies && quickReplies.length > 0

    return (
      <div>
        <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
          Claire
        </p>

        {/* Concept bridge - short */}
        {conceptBridge && (
          <p className="text-sm text-gray-600 mb-2">
            <MathText text={conceptBridge} />
          </p>
        )}

        {/* Next micro-step question */}
        <div className="text-lg text-[var(--claire-navy)]">
          <MathText text={nextMicroStep} />
        </div>

        {/* Quick replies - only if agent returned them */}
        {hasQuickReplies && (
          <div className="flex flex-wrap gap-2 mt-4">
            {quickReplies.map((reply, i) => (
              <button
                key={i}
                onClick={() => onQuickReply(reply)}
                className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
              >
                <MathText text={reply} />
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Legacy format (say, ask_back, concept_card events)
  let { text, question, quickReplies, conceptCard } = event

  // Try to parse JSON if text looks like raw JSON
  const parsedJson = tryParseJsonResponse(text) || tryParseJsonResponse(question)
  if (parsedJson) {
    question = parsedJson.question
    text = ''
    if (parsedJson.hints.length > 0 && !quickReplies) {
      quickReplies = parsedJson.hints
    }
  }

  const mainText = question || text || ''
  const hasQuickReplies = quickReplies && quickReplies.length > 0

  return (
    <div>
      <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
        Claire
      </p>

      <div className="text-lg text-[var(--claire-navy)]">
        <MathText text={mainText} />
      </div>

      {conceptCard && (
        <div className="mt-4 p-4 bg-[var(--claire-teal-muted)] rounded-lg border-l-4 border-[var(--claire-teal)]">
          <h4 className="font-bold text-[var(--claire-navy)] mb-1">{conceptCard.title}</h4>
          {conceptCard.one_liner && (
            <p className="text-sm italic text-gray-600 mb-2">
              <MathText text={conceptCard.one_liner} />
            </p>
          )}
          {conceptCard.explanation && (
            <div className="text-sm text-gray-700">
              <MathText text={conceptCard.explanation} />
            </div>
          )}
        </div>
      )}

      {hasQuickReplies && (
        <div className="flex flex-wrap gap-2 mt-4">
          {quickReplies.map((reply, i) => (
            <button
              key={i}
              onClick={() => onQuickReply(reply)}
              className="px-3 py-1.5 text-sm bg-[var(--claire-ai-bg)] text-[var(--claire-navy)] rounded-full hover:bg-[var(--claire-next-bg)] transition-colors"
            >
              <MathText text={reply} />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * UploadCard
 */
function UploadCard({ qrUrl, qrLoading, qrStatus, qrError, onRetry }) {
  const status = qrError ? 'error' : (qrStatus?.status || 'pending')

  const getQRCodeUrl = (url, size = 150) => {
    return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(url)}`
  }

  return (
    <div>
      <p className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide mb-2">
        Claire
      </p>
      <p className="text-lg text-[var(--claire-navy)] mb-4">
        Upload a photo of your work so I can check it.
      </p>

      <div className="bg-gray-50 rounded-lg p-4">
        {qrLoading ? (
          <div className="flex items-center justify-center gap-2 text-gray-500 py-6">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>Creating upload session...</span>
          </div>
        ) : status === 'pending' && qrUrl ? (
          <div className="text-center">
            <div className="inline-block bg-white p-2 rounded-lg border border-gray-200 mb-3">
              <img
                src={getQRCodeUrl(qrUrl, 150)}
                alt="Scan to upload"
                className="w-[150px] h-[150px]"
              />
            </div>
            <p className="text-sm font-medium text-gray-700 mb-1">
              Scan with your phone camera
            </p>
            <p className="text-xs text-gray-400">
              Point your phone camera at the QR code to open the upload page
            </p>
          </div>
        ) : status === 'processing' ? (
          <div className="text-center py-6">
            <div className="flex justify-center mb-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-amber-500 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
            <p className="text-sm font-medium text-amber-600">
              Reading your work...
            </p>
          </div>
        ) : status === 'error' || status === 'expired' ? (
          <div className="text-center py-4">
            <p className="text-sm text-red-600 mb-1">
              {status === 'expired' ? 'Session expired' : 'Something went wrong'}
            </p>
            {qrError && (
              <p className="text-xs text-gray-400 mb-3">{qrError}</p>
            )}
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-4 py-2 text-sm font-medium bg-[var(--claire-navy)] text-white rounded-lg hover:opacity-90"
              >
                Try Again
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-4">
            Connect your phone to upload your work
          </p>
        )}
      </div>
    </div>
  )
}
