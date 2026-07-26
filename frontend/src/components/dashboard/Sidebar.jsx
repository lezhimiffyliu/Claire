import { motion } from 'framer-motion'

const NAV_ITEMS = [
  { id: 'learn', label: 'Home', icon: TodayIcon },
  { id: 'exams', label: 'Mock Exams', icon: PracticeIcon },
  { id: 'profile', label: 'Profile', icon: ProfileIcon },
]

// Today/Home icon
function TodayIcon({ active }) {
  return (
    <svg
      className={`nav-icon ${active ? 'text-[var(--claire-green)]' : ''}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  )
}

// Practice icon
function PracticeIcon({ active }) {
  return (
    <svg
      className={`nav-icon ${active ? 'text-[var(--claire-green)]' : ''}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  )
}

// Profile icon
function ProfileIcon({ active }) {
  return (
    <svg
      className={`nav-icon ${active ? 'text-[var(--claire-green)]' : ''}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  )
}

// Flame icon with pulse animation
function FlameIcon({ animate = false }) {
  return (
    <svg
      className={`w-[18px] h-[18px] text-[var(--claire-fire)] ${animate ? 'animate-fire-pulse' : ''}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"
      />
    </svg>
  )
}

// Brand mark with green accent
function LogoMark() {
  return (
    <svg
      className="w-8 h-8"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <line x1="6" y1="16" x2="26" y2="16" stroke="#E5E7EB" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="6" cy="16" r="3" fill="#047857" />
      <circle cx="16" cy="16" r="4" fill="#047857" />
      <circle cx="26" cy="16" r="3" stroke="#9CA3AF" strokeWidth="1.5" fill="none" />
    </svg>
  )
}

export default function Sidebar({ activeTab, onTabChange, streak = 0 }) {
  return (
    <aside className="fixed left-0 top-0 h-full w-[72px] bg-white border-r border-[var(--claire-border)] flex flex-col items-center py-5 z-40">
      {/* Logo */}
      <div className="mb-5 flex flex-col items-center gap-1">
        <LogoMark />
        <span className="text-xs font-semibold text-[var(--claire-charcoal)]">Claire</span>
      </div>

      {/* Streak badge - only show if streak > 0 */}
      {streak > 0 && (
        <div className="mb-5 flex flex-col items-center gap-0.5 px-3 py-2 bg-gradient-to-b from-[rgba(245,158,11,0.08)] to-[rgba(251,191,36,0.08)] rounded-xl border border-[rgba(245,158,11,0.15)]">
          <FlameIcon animate />
          <span className="text-xs font-semibold text-[var(--claire-charcoal)]">{streak}</span>
        </div>
      )}

      {/* Nav Items */}
      <nav className="flex-1 flex flex-col gap-1 w-full px-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id

          return (
            <motion.button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              whileTap={{ scale: 0.95 }}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 bg-[var(--claire-green)] rounded-r-full"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}

              <Icon active={isActive} />
              <span className="nav-label">{item.label}</span>
            </motion.button>
          )
        })}
      </nav>

      {/* Help button */}
      <button className="p-2.5 text-[var(--claire-text-muted)] hover:text-[var(--claire-text-secondary)] transition-colors duration-200 rounded-lg hover:bg-[var(--claire-hover)]">
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.75}
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </button>
    </aside>
  )
}
