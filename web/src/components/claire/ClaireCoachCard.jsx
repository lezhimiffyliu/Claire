/**
 * ClaireCoachCard - Main coach entry point on Path page
 *
 * This is the primary action point - Claire tells the user
 * what to do next. The user doesn't need to choose.
 */
export default function ClaireCoachCard({ onContinue, nextTopicName }) {
  return (
    <div className="bg-white rounded-2xl border-2 border-[var(--claire-teal)] p-6 mb-8">
      <div className="flex items-start gap-4">
        {/* Claire avatar */}
        <div className="w-12 h-12 rounded-full bg-[var(--claire-teal)] flex items-center justify-center flex-shrink-0">
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1">
          <p className="text-xs font-semibold text-[var(--claire-teal)] uppercase tracking-wide mb-2">
            Claire says
          </p>
          <p className="text-lg text-[var(--claire-navy)] leading-relaxed mb-4">
            "You don't need to choose what to study. I'll guide the next step."
          </p>

          {nextTopicName && (
            <p className="text-sm text-[var(--claire-gray-500)] mb-4">
              Next: <span className="font-medium text-[var(--claire-navy)]">{nextTopicName}</span>
            </p>
          )}

          <button
            onClick={onContinue}
            className="btn-primary px-8 py-3 text-base"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  )
}
