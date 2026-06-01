import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  getExamCountdown,
  getRoadmapState,
  getQuotaStatus,
  createCheckout,
  getRoadmap,
} from '../../api/problemApi'
import { loadProblems } from '../../api/problemLoader'
import { problemMatchesSection, normalizeConcepts } from '../../utils/conceptAliases'
import { getUserDisplayInfo } from '../../utils/userDisplayInfo'
import MockExamView from './MockExamView'
import MockExamsPage from './MockExamsPage'
import ProblemPractice from './ProblemPractice'
import ExamDatePopup from './ExamDatePopup'
import PrepLevelPopup from './PrepLevelPopup'

// =============================================================================
// Course Resolution - Single source of truth for selected course
// Priority: localStorage (onboarding) > API/Supabase > fallback
// =============================================================================
function resolveSelectedCourse(apiCourse) {
  // 1. Check localStorage first (just completed onboarding)
  let localCourse = null
  try {
    const savedSelections = JSON.parse(localStorage.getItem('claire_selections') || '{}')
    localCourse = savedSelections.course || null
  } catch (e) {
    // Ignore parse errors
  }

  // 2. API/Supabase course
  const apiCourseValue = apiCourse || null

  // 3. Determine resolved course with priority
  let resolvedCourse = 'math126' // fallback
  let source = 'fallback'

  if (localCourse) {
    resolvedCourse = localCourse
    source = 'localStorage'
  } else if (apiCourseValue && apiCourseValue !== 'math126') {
    // Only use API if it's not the default fallback
    resolvedCourse = apiCourseValue
    source = 'api'
  } else if (apiCourseValue === 'math126' && !localCourse) {
    // API returned math126 and no localStorage - could be real selection or default
    resolvedCourse = apiCourseValue
    source = 'api-default'
  }

  const courseCode = resolvedCourse.replace('math', '')
  const courseDisplay = { math124: 'Math 124', math125: 'Math 125', math126: 'Math 126' }[resolvedCourse] || 'Math 126'

  // Debug logging
  console.log('[resolveSelectedCourse]', {
    localCourse,
    apiCourse: apiCourseValue,
    resolvedCourse,
    courseCode,
    source,
  })

  return { resolvedCourse, courseCode, courseDisplay, source }
}

// =============================================================================
// Sidebar - 220px width with logo and navigation
// =============================================================================
function Sidebar({ activeTab, onTabChange }) {
  return (
    <div className="fixed left-0 top-0 h-full w-52 bg-white border-r border-gray-200 flex flex-col py-6 px-4 z-40">
      {/* Logo */}
      <div className="text-xl font-bold text-[var(--claire-navy)] mb-8 px-2">
        Claire
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1">
        <button
          onClick={() => onTabChange('home')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'home'
              ? 'bg-[var(--claire-navy)] text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Home
        </button>

        <button
          onClick={() => onTabChange('exams')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'exams'
              ? 'bg-[var(--claire-navy)] text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Mock Exams
        </button>

        <button
          onClick={() => onTabChange('roadmap')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'roadmap'
              ? 'bg-[var(--claire-navy)] text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          Roadmap
        </button>

        <button
          onClick={() => onTabChange('profile')}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'profile'
              ? 'bg-[var(--claire-navy)] text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Profile
        </button>
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Help link at bottom */}
      <button className="flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-gray-600 text-sm transition-colors">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Help
      </button>
    </div>
  )
}

// =============================================================================
// User Profile - Small component at top of right sidebar (clickable)
// =============================================================================
function UserProfile({ user, examCountdown, onProfileClick }) {
  const [imgError, setImgError] = useState(false)
  const { avatarUrl, displayName, initials } = getUserDisplayInfo(user)
  const courseDisplay = examCountdown?.course_display || 'Math 126'
  const showAvatar = avatarUrl && !imgError

  return (
    <button
      onClick={onProfileClick}
      className="flex items-center gap-3 mb-6 w-full text-left hover:bg-gray-50 rounded-lg p-2 -m-2 transition-colors"
    >
      {showAvatar ? (
        <img
          src={avatarUrl}
          alt=""
          className="w-10 h-10 rounded-full object-cover"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-10 h-10 rounded-full bg-[#0B1F3A] text-white flex items-center justify-center font-semibold text-sm">
          {initials}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-gray-800 truncate">{displayName}</div>
        <div className="text-xs text-gray-400">{courseDisplay}</div>
      </div>
    </button>
  )
}

// =============================================================================
// Profile Page - Full profile view with editable exam info
// =============================================================================
function ProfilePage({ user, examCountdown, onSignOut, onEditExam }) {
  const [imgError, setImgError] = useState(false)
  const { avatarUrl, displayName, initials, email } = getUserDisplayInfo(user)
  const courseDisplay = examCountdown?.course_display || ''
  const nextExamDisplay = examCountdown?.next_exam_display || ''
  const daysUntil = examCountdown?.days_until
  const showAvatar = avatarUrl && !imgError

  // Small edit pencil button
  const EditButton = ({ onClick }) => (
    <button
      onClick={onClick}
      className="p-1 rounded hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
    >
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    </button>
  )

  return (
    <div className="p-6 max-w-md mx-auto">
      {/* Profile Card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
        {/* Avatar - show Google photo or initials fallback */}
        <div className="mb-6 flex justify-center">
          {showAvatar ? (
            <img
              src={avatarUrl}
              alt={displayName}
              className="w-24 h-24 rounded-full object-cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-24 h-24 rounded-full bg-[#0B1F3A] text-white flex items-center justify-center font-bold text-2xl">
              {initials}
            </div>
          )}
        </div>

        {/* Name */}
        <h2 className="text-xl font-bold text-gray-800 mb-1">{displayName}</h2>

        {/* Email */}
        <p className="text-gray-500 mb-6">{email}</p>

        {/* Course & Exam Info - Editable rows */}
        <div className="border-t border-gray-100 pt-6 space-y-4 text-left">
          {courseDisplay && (
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Course</span>
              <span className="font-medium text-gray-800">{courseDisplay}</span>
            </div>
          )}

          {/* Next Exam - Editable */}
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Next Exam</span>
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-gray-800">{nextExamDisplay || 'Not set'}</span>
              <EditButton onClick={onEditExam} />
            </div>
          </div>

          {/* Days Until - Editable */}
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Days Left</span>
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-gray-800">
                {daysUntil !== undefined ? `${daysUntil} days` : 'Not set'}
              </span>
              <EditButton onClick={onEditExam} />
            </div>
          </div>
        </div>

        {/* Sign Out Button */}
        {user && (
          <button
            onClick={onSignOut}
            className="mt-8 w-full py-2.5 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
          >
            Sign Out
          </button>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Topic Entry Card - The main sticky CTA to start practicing
// =============================================================================
function TopicEntryCard({ currentSection, onStartPractice }) {
  if (!currentSection) {
    return (
      <div className="bg-gradient-to-r from-[var(--claire-navy)] to-[#1a3a5c] rounded-2xl p-6 text-white">
        <div className="text-lg font-semibold opacity-80">Loading your path...</div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-r from-[var(--claire-navy)] to-[#1a3a5c] rounded-2xl p-6 text-white shadow-lg">
      {/* Badge */}
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/20 rounded-full text-xs font-semibold mb-4">
        <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        NEXT UP
      </div>

      {/* Section info */}
      <div className="mb-4">
        <div className="text-2xl font-bold mb-1">
          {currentSection.section_id} {currentSection.display_name}
        </div>
        <div className="text-white/70 text-sm">
          Recommended because it appears often on exams and builds on previous topics.
        </div>
      </div>

      {/* CTA Button */}
      <button
        onClick={onStartPractice}
        className="w-full py-3.5 bg-white text-[var(--claire-navy)] font-bold rounded-xl hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 3l14 9-14 9V3z" />
        </svg>
        Continue Practice
      </button>
    </div>
  )
}

// =============================================================================
// Roadmap - Visual progress path (clickable nodes with labels)
// =============================================================================
function Roadmap({ sections, currentSectionId, studyMode, onSelectSection }) {
  if (!sections?.length) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-6 h-6 border-2 border-[var(--claire-navy)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Filter sections based on study mode (for future cram mode)
  const displaySections = studyMode === 'cram'
    ? sections.filter(s => s.is_weak || s.status === 'current')
    : sections

  // S-curve x offsets for winding path effect (repeating pattern)
  // indices 0-5: right side (x >= 0), indices 6-11: left side (x < 0)
  const xOffsets = [0, 40, 70, 80, 70, 40, 0, -40, -70, -80, -70, -40]

  // Node dimensions
  const nodeSpacingY = 70
  const nodeRadius = 18
  const currentNodeRadius = 26

  // Calculate node positions - S curve pattern
  const getNodePosition = (index) => {
    const x = xOffsets[index % xOffsets.length]
    const y = 60 + index * nodeSpacingY
    const labelOnRight = x >= 0  // Label on right when curve goes right
    return { x, y, labelOnRight }
  }

  // Find indices where exam dividers should appear
  const exam1End = displaySections.findIndex(s => s.covered_in_exam === 'exam_2')
  const exam2End = displaySections.findIndex(s => s.covered_in_exam === 'final')

  const totalHeight = 60 + displaySections.length * nodeSpacingY + 40

  return (
    <div className="relative flex justify-center overflow-visible" style={{ height: totalHeight }}>

      {/* Exam dividers */}
      {exam1End > 0 && (
        <div
          className="absolute left-0 right-0 flex items-center gap-3 px-4"
          style={{ top: getNodePosition(exam1End).y - nodeSpacingY / 2 - 10 }}
        >
          <div className="h-px flex-1 border-t-2 border-dashed border-gray-300" />
          <span className="px-3 py-1 bg-white text-xs font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">
            Midterm I
          </span>
          <div className="h-px flex-1 border-t-2 border-dashed border-gray-300" />
        </div>
      )}
      {exam2End > 0 && (
        <div
          className="absolute left-0 right-0 flex items-center gap-3 px-4"
          style={{ top: getNodePosition(exam2End).y - nodeSpacingY / 2 - 10 }}
        >
          <div className="h-px flex-1 border-t-2 border-dashed border-gray-300" />
          <span className="px-3 py-1 bg-white text-xs font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap">
            Midterm II
          </span>
          <div className="h-px flex-1 border-t-2 border-dashed border-gray-300" />
        </div>
      )}

      {/* Nodes */}
      {displaySections.map((section, index) => {
        const isCurrent = section.section_id === currentSectionId
        const isCompleted = section.status === 'completed'
        const isInProgress = section.status === 'in_progress'
        const pos = getNodePosition(index)
        const radius = isCurrent ? currentNodeRadius : nodeRadius

        return (
          <div
            key={section.section_id}
            className="absolute flex items-center"
            style={{
              left: '50%',
              top: pos.y,
              transform: `translate(calc(-50% + ${pos.x}px), -50%)`,
            }}
          >
            {/* START bubble for current node */}
            {isCurrent && (
              <div className="absolute -top-12 left-1/2 -translate-x-1/2 z-10">
                <div className="relative bg-[var(--claire-navy)] text-white text-xs font-bold px-3 py-1.5 rounded-lg whitespace-nowrap">
                  START
                  {/* Triangle pointer */}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-[var(--claire-navy)]" />
                </div>
              </div>
            )}

            {/* Node circle - clickable */}
            <button
              onClick={() => onSelectSection?.(section)}
              className={`
                flex items-center justify-center rounded-full font-semibold transition-all cursor-pointer
                ${isCurrent
                  ? 'bg-[var(--claire-navy)] text-white shadow-lg hover:shadow-xl hover:scale-105'
                  : isCompleted
                    ? 'bg-[var(--claire-navy)] text-white hover:opacity-80'
                    : isInProgress
                      ? 'bg-blue-100 text-[var(--claire-navy)] border-2 border-[var(--claire-navy)] hover:bg-blue-200'
                      : 'bg-gray-100 text-gray-400 border border-gray-200 hover:bg-gray-200 hover:text-gray-600'
                }
              `}
              style={{
                width: radius * 2,
                height: radius * 2,
                fontSize: isCurrent ? 14 : 11,
              }}
            >
              {isCompleted && !isCurrent ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                section.section_id
              )}
            </button>

            {/* Topic name label - position based on curve direction */}
            <div className={`absolute whitespace-nowrap ${pos.labelOnRight ? 'left-full ml-3' : 'right-full mr-3 text-right'}`}>
              <button
                onClick={() => onSelectSection?.(section)}
                className={`text-xs transition-colors cursor-pointer hover:text-[var(--claire-navy)] ${
                  isCurrent ? 'font-semibold text-[var(--claire-navy)]' : isCompleted ? 'text-gray-500' : 'text-gray-400'
                }`}
              >
                {section.display_name}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// =============================================================================
// Exam Countdown Card - Shows countdown and optional plan mode
// Never shows negative days - always clamp to 0
// =============================================================================
function ExamCountdownCard({ data }) {
  if (!data) return null

  // Never show negative days - clamp to 0
  const displayDays = Math.max(0, data.days_until ?? 0)
  const progress = Math.max(0, Math.min(100, ((30 - displayDays) / 30) * 100))

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Upcoming Exam
      </div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm text-gray-600">{data.course_display}</div>
          <div className="text-2xl font-bold text-[var(--claire-navy)]">{data.next_exam_display}</div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-[var(--claire-navy)]">{displayDays}</div>
          <div className="text-xs text-gray-400">days left</div>
        </div>
      </div>
      {/* Progress bar */}
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--claire-navy)] rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}

// =============================================================================
// High Value Topics Card (Must Know)
// =============================================================================
function HighValueCard({ data, onSelectTopic }) {
  if (!data?.sections?.length) return null

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        At Least Know These Before The Exam
      </div>
      <div className="space-y-2">
        {data.sections.slice(0, 3).map((s) => (
          <button
            key={s.section_id}
            onClick={() => onSelectTopic?.(s)}
            className="w-full flex items-center gap-3 p-2 -mx-2 rounded-lg hover:bg-gray-50 transition-colors text-left group"
          >
            <div className="w-2 h-2 rounded-full bg-[var(--claire-navy)] flex-shrink-0" />
            <span className="text-sm text-gray-700 group-hover:text-[var(--claire-navy)] transition-colors">
              {s.display_name}
            </span>
            <svg className="w-4 h-4 text-gray-300 group-hover:text-[var(--claire-navy)] ml-auto transition-colors" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Premium Card
// =============================================================================
function PremiumCard({ isPro, onUpgrade }) {
  if (isPro) {
    return (
      <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl border border-amber-200 p-5">
        <div className="flex items-center gap-2 text-amber-700 font-medium">
          <span>⭐</span>
          <span>Pro Member</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="font-semibold text-gray-800">Go Premium</div>
          <div className="text-xs text-gray-500">Unlimited practice & AI help</div>
        </div>
        <span className="text-xl">✨</span>
      </div>
      <button
        onClick={onUpgrade}
        className="w-full py-2.5 bg-[var(--claire-navy)] text-white text-sm font-semibold rounded-lg hover:opacity-90 transition-opacity"
      >
        Try 1 Week Free
      </button>
    </div>
  )
}

// =============================================================================
// Main Dashboard Component
// =============================================================================
export default function DashboardNew({ onBack }) {
  const navigate = useNavigate()
  const { user, signOut } = useAuth()

  const [activeTab, setActiveTab] = useState('home')
  // `loading` only gates the full-screen spinner on the FIRST load. Background
  // refetches (e.g. when `user` changes) must NOT flip this back on, otherwise
  // they unmount whatever view is showing (like an in-progress practice session).
  const [loading, setLoading] = useState(true)
  const hasLoadedRef = useRef(false)

  // Study mode: 'normal' | 'cram' (for future)
  const [studyMode, setStudyMode] = useState('normal')

  // Data states
  const [examCountdown, setExamCountdown] = useState(null)
  // mustKnowSections removed - now using roadmapData.high_value_sections
  const [roadmapState, setRoadmapState] = useState(null)
  const [quotaStatus, setQuotaStatus] = useState(null)
  const [problems, setProblems] = useState([])

  // Personalized roadmap data (from plan mode)
  const [roadmapData, setRoadmapData] = useState(null)

  // Onboarding popup states
  const [showExamDatePopup, setShowExamDatePopup] = useState(false)
  const [showPrepLevelPopup, setShowPrepLevelPopup] = useState(false)
  // Track if popup is required (exam expired - can't skip)
  const [examPopupRequired, setExamPopupRequired] = useState(false)

  // Practice states
  const [examMode, setExamMode] = useState(null)
  const [practiceSection, setPracticeSection] = useState(null)

  // Selected course code (resolved from localStorage/API)
  const [selectedCourseCode, setSelectedCourseCode] = useState('126')

  // Check for missing onboarding data on mount
  useEffect(() => {
    const examSetupDone = localStorage.getItem('claire_exam_date')
    const prepLevel = localStorage.getItem('claire_prep_level')

    if (!examSetupDone) {
      setShowExamDatePopup(true)
    } else if (!prepLevel) {
      setShowPrepLevelPopup(true)
    }
  }, [])

  // Load roadmap data after popups complete or if data exists
  const loadRoadmapData = async (code) => {
    try {
      const data = await getRoadmap(code)

      if (!data.fallback_to_legacy && data.sections?.length > 0) {
        setRoadmapData(data)

        // API返回正确格式的sections（如 "14.3: Partial Derivatives"）
        // 直接使用，按roadmap优先级排序
        setRoadmapState({
          sections: data.sections,
          current_section_id: data.current_section_id
        })
      }
    } catch (e) {
      console.error('Roadmap load error:', e)
    }
  }

  useEffect(() => {
    async function load() {
      // Only show the blocking spinner on the initial load. Subsequent refetches
      // run silently so they never tear down the current view.
      if (!hasLoadedRef.current) {
        setLoading(true)
      }
      try {
        // Fetch API data (works for logged-in users)
        const [countdown, roadmap, quota] = await Promise.all([
          getExamCountdown(),
          getRoadmapState(),
          getQuotaStatus(),
        ])

        console.log('[Dashboard] API returned countdown:', countdown)

        // Resolve course using unified logic (works for BOTH anonymous and logged-in users)
        // Priority: localStorage > API/Supabase > fallback
        const { resolvedCourse, courseCode, courseDisplay, source } = resolveSelectedCourse(countdown?.course)

        console.log('[Dashboard] Course resolution:', { resolvedCourse, courseCode, source, user: !!user })

        // Save resolved course code to state (for MockExamsPage, etc.)
        setSelectedCourseCode(courseCode)

        // Build effective countdown with resolved course
        const effectiveCountdown = {
          ...countdown,
          course: resolvedCourse,
          course_display: courseDisplay,
        }

        // Override with user's saved exam selection from localStorage
        const savedExamType = localStorage.getItem('claire_exam_type')
        const savedExamLabel = localStorage.getItem('claire_exam_label')
        const savedExamDate = localStorage.getItem('claire_exam_date')

        if (savedExamDate) {
          const examDateObj = new Date(savedExamDate)
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          const daysUntil = Math.ceil((examDateObj - today) / (1000 * 60 * 60 * 24))

          // Check if exam has passed (negative days)
          if (daysUntil < 0) {
            // Exam expired - show required popup to set new exam
            setExamPopupRequired(true)
            setShowExamDatePopup(true)
          }

          setExamCountdown({
            ...effectiveCountdown,
            next_exam: savedExamType || effectiveCountdown.next_exam,
            next_exam_display: savedExamLabel || effectiveCountdown.next_exam_display,
            days_until: daysUntil,
          })
        } else {
          setExamCountdown(effectiveCountdown)
        }
        setRoadmapState(roadmap)
        setQuotaStatus(quota)

        // Load problems for the resolved course
        console.log('[Dashboard] loadProblems:', courseCode)
        setProblems(await loadProblems(courseCode))

        // Load personalized roadmap if onboarding complete
        const examSetupDone = localStorage.getItem('claire_exam_date')
        const prepLevel = localStorage.getItem('claire_prep_level')
        if (examSetupDone && prepLevel) {
          console.log('[Dashboard] loadRoadmapData:', courseCode)
          await loadRoadmapData(courseCode)
        }
      } catch (e) {
        console.error('Load error:', e)
      }
      hasLoadedRef.current = true
      setLoading(false)
    }
    load()
  }, [user])

  // Handle exam date popup completion
  const handleExamDateSave = (data) => {
    // data = { examType, examLabel, examDate, daysUntil }
    // Update examCountdown with user's selection
    setExamCountdown(prev => ({
      ...prev,
      next_exam: data.examType,
      next_exam_display: data.examLabel,
      days_until: data.daysUntil,
    }))
    // Reset required flag if it was set (exam expired scenario)
    setExamPopupRequired(false)
    // Show prep level popup next
    setShowPrepLevelPopup(true)
  }

  // Handle prep level popup completion
  const handlePrepLevelSave = async (level) => {
    // Reload roadmap with new data using already resolved course
    console.log('[Dashboard] handlePrepLevelSave - using selectedCourseCode:', selectedCourseCode)
    await loadRoadmapData(selectedCourseCode)
  }

  // Get current section object
  const currentSection = roadmapState?.sections?.find(
    s => s.section_id === roadmapState?.current_section_id
  )

  const handleStartPractice = () => {
    if (!currentSection) return

    // Filter problems by concept overlap with normalization layer
    const sectionConcepts = currentSection.concepts || []
    const sectionProblems = problems.filter(p =>
      problemMatchesSection(p, sectionConcepts)
    )

    // DEBUG: Log matching details (remove in production)
    if (import.meta.env.DEV) {
      const matchedIds = sectionProblems.map(p => p.id)
      const matchedConceptsSet = new Set()
      sectionProblems.forEach(p => {
        const normalized = normalizeConcepts(p.concepts || [])
        normalized.forEach(c => {
          if (sectionConcepts.includes(c)) matchedConceptsSet.add(c)
        })
      })
      console.log('[DEBUG] Start practice:', {
        section_id: currentSection.section_id,
        section_concepts: sectionConcepts,
        matched_count: sectionProblems.length,
        matched_ids: matchedIds,
        matched_concepts: [...matchedConceptsSet],
      })
    }

    // Pass section context with filtered problems (no fallback)
    setPracticeSection({
      section_id: currentSection.section_id,
      display_name: currentSection.display_name,
      concepts: sectionConcepts,
      course: examCountdown?.course || 'math126',
      problems: sectionProblems,
    })
  }

  const handleStartMockExam = () => {
    if (problems.length) {
      const shuffled = [...problems].sort(() => Math.random() - 0.5)
      setExamMode({ name: 'Mock Exam', problems: shuffled.slice(0, 8) })
    }
  }

  // Handler for selecting a section from Roadmap (uses concepts)
  const handleSelectSection = (section) => {
    const sectionConcepts = section.concepts || []
    const sectionProblems = problems.filter(p =>
      problemMatchesSection(p, sectionConcepts)
    )

    setPracticeSection({
      section_id: section.section_id,
      display_name: section.display_name,
      concepts: sectionConcepts,
      course: examCountdown?.course || 'math126',
      problems: sectionProblems,
    })
  }

  // Handler for selecting a topic from HighValueCard (uses topic key)
  const handleSelectTopic = (topicData) => {
    const topicKey = topicData.section_id
    const topicProblems = problems.filter(p => p.topic === topicKey)

    setPracticeSection({
      section_id: topicKey,
      display_name: topicData.display_name,
      concepts: [],
      course: examCountdown?.course || 'math126',
      problems: topicProblems,
    })
  }

  // Handler for starting a real exam from MockExamsPage
  const handleStartExam = (exam) => {
    if (exam?.problems?.length > 0) {
      const courseDisplay = examCountdown?.course_display || 'Math 126'
      setExamMode({
        name: `${courseDisplay} ${exam.displayName}`,
        problems: exam.problems,
        examId: exam.id,
      })
    }
  }

  const handleUpgrade = async () => {
    if (!user) { navigate('/login'); return }
    try {
      const res = await createCheckout(user.id, user.email)
      if (res.checkout_url) window.location.href = res.checkout_url
    } catch (e) { console.error(e) }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-6 h-6 border-2 border-[var(--claire-navy)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Mock exam mode
  if (examMode) {
    return (
      <MockExamView
        examName={examMode.name}
        problems={examMode.problems}
        onExit={() => setExamMode(null)}
        onSubmit={() => setExamMode(null)}
      />
    )
  }

  // Practice mode
  if (practiceSection) {
    return (
      <ProblemPractice
        section={practiceSection}
        onBack={() => setPracticeSection(null)}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main content area */}
      <div className="ml-52 min-h-screen">
        {activeTab === 'home' && (
          <div className="flex">
            {/* Center: Topic Entry Card - fills available space */}
            <div className="flex-1 min-w-0">
              {/* Topic Entry Card */}
              <div className="pt-6 pb-4 px-6">
                <TopicEntryCard
                  currentSection={currentSection}
                  onStartPractice={handleStartPractice}
                />
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="w-80 border-l border-gray-200 bg-white min-h-screen">
              <div className="sticky top-0 p-6 space-y-5">
                {/* User Profile */}
                <UserProfile
                  user={user}
                  examCountdown={examCountdown}
                  onProfileClick={() => setActiveTab('profile')}
                />

                {/* Cards */}
                <ExamCountdownCard data={examCountdown} />
                {/* high_value_sections: 分数杠杆，点击进入topic练习 */}
                <HighValueCard
                  data={
                    roadmapData?.high_value_sections?.length > 0
                      ? {
                          sections: roadmapData.high_value_sections.map(topic => ({
                            section_id: topic.topic,
                            display_name: topic.display_name,
                            is_weak: topic.is_weak,
                            expected_loss: topic.expected_loss,
                          }))
                        }
                      // FALLBACK: roadmap前3个
                      : roadmapData?.sections?.length > 0
                        ? { sections: roadmapData.sections.slice(0, 3) }
                        : null
                  }
                  onSelectTopic={handleSelectTopic}
                />
                <PremiumCard isPro={quotaStatus?.is_pro} onUpgrade={handleUpgrade} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'exams' && (
          <div className="flex">
            {/* Main content */}
            <div className="flex-1 p-6">
              <MockExamsPage onStartExam={handleStartExam} examCountdown={examCountdown} courseCode={selectedCourseCode} hideSidebar />
            </div>

            {/* Right Sidebar - same as Home */}
            <div className="w-80 border-l border-gray-200 bg-white min-h-screen">
              <div className="sticky top-0 p-6 space-y-5">
                <UserProfile
                  user={user}
                  examCountdown={examCountdown}
                  onProfileClick={() => setActiveTab('profile')}
                />
                <ExamCountdownCard data={examCountdown} />
                <PremiumCard isPro={quotaStatus?.is_pro} onUpgrade={handleUpgrade} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'roadmap' && (
          <div className="flex">
            {/* Center: Roadmap - fills available space */}
            <div className="flex-1 min-w-0">
              {/* Scrollable Roadmap */}
              <div className="px-6 pt-6 pb-12 overflow-visible">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
                  Your Path
                </div>
                <Roadmap
                  sections={roadmapState?.sections || []}
                  currentSectionId={roadmapState?.current_section_id}
                  studyMode={studyMode}
                  onSelectSection={handleSelectSection}
                />
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="w-80 border-l border-gray-200 bg-white min-h-screen">
              <div className="sticky top-0 p-6 space-y-5">
                <UserProfile
                  user={user}
                  examCountdown={examCountdown}
                  onProfileClick={() => setActiveTab('profile')}
                />
                <ExamCountdownCard data={examCountdown} />
                <PremiumCard isPro={quotaStatus?.is_pro} onUpgrade={handleUpgrade} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <ProfilePage
            user={user}
            examCountdown={examCountdown}
            onSignOut={signOut}
            onEditExam={() => setShowExamDatePopup(true)}
          />
        )}
      </div>

      {/* Onboarding Popups */}
      <ExamDatePopup
        isOpen={showExamDatePopup}
        onClose={() => {
          // Only allow closing if not required
          if (!examPopupRequired) {
            setShowExamDatePopup(false)
          }
        }}
        onSave={handleExamDateSave}
        required={examPopupRequired}
      />
      <PrepLevelPopup
        isOpen={showPrepLevelPopup}
        onClose={() => setShowPrepLevelPopup(false)}
        onSave={handlePrepLevelSave}
      />
    </div>
  )
}
