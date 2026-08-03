import { motion } from 'framer-motion'

// Path icon with nodes representing progress
function PathIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 120 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Connecting line */}
      <line
        x1="12"
        y1="12"
        x2="108"
        y2="12"
        stroke="#CBD5E0"
        strokeWidth="2"
        strokeDasharray="4 4"
      />
      {/* Done node */}
      <circle cx="12" cy="12" r="6" fill="#2FBF9F" />
      {/* Current node with ring */}
      <circle cx="48" cy="12" r="8" fill="#2FBF9F" />
      <circle
        cx="48"
        cy="12"
        r="11"
        fill="none"
        stroke="#2FBF9F"
        strokeWidth="2"
        opacity="0.3"
      />
      {/* Pen trace hint */}
      <path
        d="M52 8 L56 4"
        stroke="#0B1F3A"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.4"
      />
      {/* Future nodes */}
      <circle
        cx="84"
        cy="12"
        r="6"
        fill="none"
        stroke="#CBD5E0"
        strokeWidth="2"
      />
      <circle
        cx="108"
        cy="12"
        r="6"
        fill="none"
        stroke="#CBD5E0"
        strokeWidth="2"
      />
    </svg>
  )
}

function HeroSection({ onGetStarted }) {
  return (
    <section className="min-h-screen flex items-center justify-center px-6 md:px-12 lg:px-20 pt-20 pb-16 bg-[var(--claire-bg)]">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 md:gap-16 items-center">
        {/* Left: Text content */}
        <motion.div
          className="text-left"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          {/* Brand + Context */}
          <div className="flex items-center gap-3 mb-6">
            <PathIcon className="w-24 h-6 opacity-80" />
            <span className="text-sm font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
              UW Calculus
            </span>
          </div>

          {/* Headline - Claire + Cram prominent */}
          <h1 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-[var(--claire-navy)] mb-4 leading-[1.1] tracking-tight">
            <span className="text-[var(--claire-teal)]">Claire</span> helps you{' '}
            <span className="italic">cram</span> smarter.
          </h1>

          {/* Subheadline */}
          <p className="text-xl md:text-2xl text-[var(--claire-gray-700)] mb-3 font-medium">
            Last-minute clarity for calculus.
          </p>
          <p className="text-base md:text-lg text-[var(--claire-gray-500)] mb-8 leading-relaxed max-w-lg">
            Start with a 5-minute diagnostic to see exactly what you need to fix, using real UW exam problems.
          </p>

          {/* CTA Button */}
          <button
            onClick={onGetStarted}
            className="btn-primary text-lg px-10 py-4"
          >
            GET STARTED
          </button>

          {/* Trust line */}
          <p className="mt-6 text-sm text-[var(--claire-gray-400)]">
            Math 124 · 125 · 126 — No signup required
          </p>
        </motion.div>

        {/* Right: Diagnostic Preview Panel */}
        <motion.div
          className="relative"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          {/* Diagnostic Result Card */}
          <div className="bg-white rounded-xl border border-[var(--claire-gray-200)] shadow-sm p-6">
            <div className="flex items-center justify-between mb-5">
              <span className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider">
                Your Diagnosis
              </span>
              <span className="text-xs text-[var(--claire-gray-400)]">
                Math 125
              </span>
            </div>

            <div className="space-y-3">
              {/* Weak */}
              <div className="status-card weak">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="label-weak">Weak</span>
                    <p className="text-sm font-medium text-[var(--claire-gray-900)] mt-2">
                      Implicit Differentiation
                    </p>
                    <p className="text-xs text-[var(--claire-gray-500)] mt-1">
                      Chain rule step on y terms
                    </p>
                  </div>
                  <button className="text-xs font-medium text-[var(--claire-weak)] hover:underline">
                    Fix this
                  </button>
                </div>
              </div>

              {/* Next */}
              <div className="status-card next">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="label-next">Next</span>
                    <p className="text-sm font-medium text-[var(--claire-gray-900)] mt-2">
                      Related Rates
                    </p>
                  </div>
                </div>
              </div>

              {/* Strong */}
              <div className="status-card strong">
                <div className="flex items-center gap-2">
                  <span className="label-strong">Strong</span>
                  <span className="text-sm text-[var(--claire-gray-600)]">
                    Chain Rule · Power Rule · Limits
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default HeroSection
