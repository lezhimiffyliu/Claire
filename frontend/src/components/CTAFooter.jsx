import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

// Brand mark
function LogoMark({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M6 16 H26" stroke="#CBD5E0" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="6" cy="16" r="3" fill="#2FBF9F" />
      <circle cx="16" cy="16" r="5" fill="#2FBF9F" />
      <circle cx="16" cy="16" r="7" fill="none" stroke="#2FBF9F" strokeWidth="1.5" opacity="0.3" />
      <path d="M19 13 L22 10" stroke="#0B1F3A" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      <circle cx="26" cy="16" r="3" fill="none" stroke="#CBD5E0" strokeWidth="1.5" />
    </svg>
  )
}

function CTAFooter({ onGetStarted }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section ref={ref} className="py-20 md:py-24 px-6 md:px-12 lg:px-20 bg-white">
      <motion.div
        className="max-w-2xl mx-auto text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.3 }}
      >
        <h2 className="text-2xl md:text-3xl font-semibold text-[var(--claire-navy)] mb-4 leading-tight">
          Know what to study next.
        </h2>

        <p className="text-base text-[var(--claire-gray-500)] mb-8">
          5-minute diagnostic. Clear path to your target grade.
        </p>

        <button onClick={onGetStarted} className="btn-primary text-lg px-10 py-4">
          GET STARTED
        </button>

        <p className="mt-6 text-sm text-[var(--claire-gray-400)]">
          Math 124/125/126 · Real UW past exams
        </p>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-[var(--claire-gray-200)]">
          <div className="flex items-center justify-center gap-2 mb-4">
            <LogoMark className="w-6 h-6" />
            <span className="font-semibold text-[var(--claire-navy)]">claire</span>
          </div>

          <p className="text-sm text-[var(--claire-gray-400)] mb-4">
            Know what to study next.
          </p>

          <div className="flex justify-center gap-6 text-sm text-[var(--claire-gray-400)]">
            <a
              href="#"
              className="hover:text-[var(--claire-navy)] transition-colors"
            >
              About
            </a>
            <a
              href="#"
              className="hover:text-[var(--claire-navy)] transition-colors"
            >
              Privacy
            </a>
            <a
              href="#"
              className="hover:text-[var(--claire-navy)] transition-colors"
            >
              Terms
            </a>
          </div>

          <p className="mt-6 text-xs text-[var(--claire-gray-300)]">
            © 2025 Claire. Not affiliated with University of Washington.
          </p>
        </div>
      </motion.div>
    </section>
  )
}

export default CTAFooter
