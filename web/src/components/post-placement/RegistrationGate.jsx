import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 },
  },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
}

const BENEFITS = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    title: 'Upload handwritten work from your phone',
    description: 'Snap a photo of your scratch paper, AI reads your steps',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    title: 'AI analysis + step-by-step guidance',
    description: 'Finds your exact mistake, guides you to fix it yourself',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: 'Track your exam prep progress',
    description: "See what you've mastered and where you're stuck",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    title: '760+ real UW past exam problems',
    description: '86 exams from Math 124/125/126, all free',
  },
]

function ConfirmSkipModal({ onConfirm, onCancel }) {
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
      />

      {/* Modal */}
      <motion.div
        className="relative bg-white rounded-2xl p-6 w-full max-w-md shadow-xl"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Warning icon */}
        <div className="w-12 h-12 bg-[var(--claire-weak-bg)] rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-[var(--claire-weak)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h2 className="text-xl font-semibold text-[var(--claire-navy)] text-center mb-2">
          Your diagnostic results will be lost
        </h2>

        <p className="text-[var(--claire-gray-500)] text-center text-sm mb-6">
          You may need to retake it next time. Sign in takes 3 seconds.
        </p>

        {/* Benefits list */}
        <div className="bg-[var(--claire-bg)] rounded-xl p-4 mb-6">
          <p className="text-xs font-semibold text-[var(--claire-gray-500)] uppercase tracking-wider mb-3">
            Unlock with sign in
          </p>
          <ul className="space-y-3">
            {BENEFITS.map((benefit, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center text-[var(--claire-teal)] flex-shrink-0">
                  {benefit.icon}
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--claire-navy)]">
                    {benefit.title}
                  </p>
                  <p className="text-xs text-[var(--claire-gray-500)]">
                    {benefit.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Buttons */}
        <div className="space-y-3">
          <button
            onClick={onCancel}
            className="btn-secondary w-full"
          >
            OK, sign me in
          </button>
          <button
            onClick={onConfirm}
            className="w-full text-sm text-[var(--claire-gray-400)] hover:text-[var(--claire-gray-600)] transition-colors py-2"
          >
            No thanks, skip anyway
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

function RegistrationGate({ onLogin, onSkip }) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showConfirmSkip, setShowConfirmSkip] = useState(false)
  const { signInWithGoogle } = useAuth()

  const handleGoogleLogin = async () => {
    setIsLoading(true)
    setError(null)

    try {
      await signInWithGoogle()
    } catch (err) {
      console.error('Login error:', err)
      setError('Failed to sign in. Please try again.')
      setIsLoading(false)
    }
  }

  const handleMaybeLater = () => {
    setShowConfirmSkip(true)
  }

  const handleConfirmSkip = () => {
    setShowConfirmSkip(false)
    onSkip()
  }

  return (
    <>
      <motion.div
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        className="flex-1 flex items-center justify-center px-4"
      >
        <div className="w-full max-w-md mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-[var(--claire-navy)] rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
            </div>

            <h1 className="text-2xl font-semibold text-[var(--claire-navy)] mb-2">
              Sign in to save your progress
            </h1>

            <p className="text-[var(--claire-gray-500)]">
              Without signing in, your diagnostic results won't be saved
            </p>
          </div>

          {/* Benefits */}
          <div className="bg-white rounded-xl border border-[var(--claire-gray-200)] p-4 mb-6">
            <ul className="space-y-4">
              {BENEFITS.map((benefit, i) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-[var(--claire-teal-muted)] rounded-lg flex items-center justify-center text-[var(--claire-teal)] flex-shrink-0">
                    {benefit.icon}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[var(--claire-navy)]">
                      {benefit.title}
                    </p>
                    <p className="text-xs text-[var(--claire-gray-500)]">
                      {benefit.description}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 bg-[var(--claire-weak-bg)] border border-[var(--claire-weak)] rounded-xl text-[var(--claire-weak)] text-sm text-center"
            >
              {error}
            </motion.div>
          )}

          {/* Google sign in button */}
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full btn-secondary flex items-center justify-center gap-3 text-lg mb-4"
          >
            {isLoading ? (
              <motion.div
                className="w-6 h-6 border-3 border-white border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            ) : (
              <>
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </>
            )}
          </button>

          {/* Skip link */}
          <button
            onClick={handleMaybeLater}
            className="w-full text-[var(--claire-gray-400)] text-sm hover:text-[var(--claire-gray-600)] transition-colors py-2"
            disabled={isLoading}
          >
            Maybe later
          </button>

          {/* Trust badges */}
          <div className="mt-6 flex items-center justify-center gap-4 text-xs text-[var(--claire-gray-400)]">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                  clipRule="evenodd"
                />
              </svg>
              Secure
            </span>
            <span>·</span>
            <span>No spam</span>
            <span>·</span>
            <span>Free</span>
          </div>
        </div>
      </motion.div>

      {/* Confirm skip modal */}
      <AnimatePresence>
        {showConfirmSkip && (
          <ConfirmSkipModal
            onConfirm={handleConfirmSkip}
            onCancel={() => setShowConfirmSkip(false)}
          />
        )}
      </AnimatePresence>
    </>
  )
}

export default RegistrationGate
