/**
 * MathText - Render text with LaTeX math using KaTeX
 *
 * Supports:
 * - Inline math: $...$
 * - Display math: $$...$$ or \[...\]
 */
import katex from 'katex'
import 'katex/dist/katex.min.css'

export default function MathText({ text, className = '' }) {
  if (!text) return null

  const renderMath = (str) => {
    const parts = str.split(/(\$\$[^$]+\$\$|\$[^$]+\$|\\[[^\]]+\\]|\\\\[[^\]]+\\\\])/g)

    return parts.map((part, i) => {
      // Display math: $$...$$ or \[...\]
      if ((part.startsWith('$$') && part.endsWith('$$')) ||
          (part.startsWith('\\[') && part.endsWith('\\]'))) {
        const math = part.startsWith('$$') ? part.slice(2, -2) : part.slice(2, -2)
        try {
          const html = katex.renderToString(math, {
            throwOnError: false,
            displayMode: true,
            strict: false,
          })
          return (
            <span
              key={i}
              className="block my-3"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          )
        } catch (e) {
          return <span key={i} className="font-mono">{math}</span>
        }
      }
      // Inline math: $...$
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
          return <span key={i} className="font-mono">{math}</span>
        }
      }
      // Plain text
      return <span key={i} dangerouslySetInnerHTML={{ __html: part }} />
    })
  }

  return <span className={`math-text ${className}`}>{renderMath(text)}</span>
}
