import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// Brand mark: path with highlighted node
function LogoMark({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Path line */}
      <path
        d="M6 16 H26"
        stroke="#CBD5E0"
        strokeWidth="2"
        strokeDasharray="3 3"
      />
      {/* Past node */}
      <circle cx="6" cy="16" r="3" fill="#2FBF9F" />
      {/* Current node with ring */}
      <circle cx="16" cy="16" r="5" fill="#2FBF9F" />
      <circle
        cx="16"
        cy="16"
        r="7"
        fill="none"
        stroke="#2FBF9F"
        strokeWidth="1.5"
        opacity="0.3"
      />
      {/* Pen trace */}
      <path
        d="M19 13 L22 10"
        stroke="#0B1F3A"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      {/* Future node */}
      <circle
        cx="26"
        cy="16"
        r="3"
        fill="none"
        stroke="#CBD5E0"
        strokeWidth="1.5"
      />
    </svg>
  )
}

function StickyHeader({ onGetStarted, heroRef }) {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      if (heroRef?.current) {
        const heroBottom = heroRef.current.getBoundingClientRect().bottom
        setIsScrolled(heroBottom < 100)
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [heroRef])

  return (
    <motion.header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-200 ${
        isScrolled
          ? 'bg-white/95 backdrop-blur-md border-b border-[var(--claire-gray-200)]'
          : 'bg-transparent'
      }`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="max-w-6xl mx-auto px-6 md:px-12 lg:px-20 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <LogoMark className="w-8 h-8" />
          <span className="font-semibold text-lg text-[var(--claire-navy)]">
            claire
          </span>
        </div>

        {/* CTA Button - appears when scrolled */}
        <AnimatePresence>
          {isScrolled && (
            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.15 }}
              onClick={onGetStarted}
              className="btn-primary text-sm px-5 py-2"
            >
              GET STARTED
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </motion.header>
  )
}

export default StickyHeader
