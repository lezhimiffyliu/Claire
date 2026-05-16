/**
 * ClaireHint - An inline hint component for problem pages
 *
 * Appears at the top of the problem, providing a subtle
 * guidance message without being intrusive.
 */
export default function ClaireHint({ message }) {
  if (!message) return null

  return (
    <div className="mb-4 flex items-start gap-2 px-3 py-2 bg-[var(--claire-ai-bg)] rounded-lg border-l-3 border-[var(--claire-ai)]">
      <span className="text-xs font-semibold text-[var(--claire-ai)] uppercase tracking-wide flex-shrink-0">
        Claire:
      </span>
      <span className="text-sm text-[var(--claire-gray-700)] italic">
        "{message}"
      </span>
    </div>
  )
}
