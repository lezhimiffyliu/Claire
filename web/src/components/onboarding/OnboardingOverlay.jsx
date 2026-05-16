import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import PathSelection from './PathSelection'
import GoalSelection from './GoalSelection'
import TimelineSelection from './TimelineSelection'
import DiagnosticQuestion from './DiagnosticQuestion'
import ReportGenerating from './ReportGenerating'
import DiagnosticProgress from './DiagnosticProgress'
import BackButton from '../ui/BackButton'
import { getNextQuestion, analyzeResults } from '../../data/questionBanks'
import { useAuth } from '../../context/AuthContext'
import {
  PlacementComplete,
  UnlockResult,
  KnowledgeMap,
  RewardPreview,
  RegistrationGate,
  PostLoginCelebration,
  MainHome,
} from '../post-placement'

const PHASES = {
  COURSE_SELECT: 'course',
  GOAL_SELECT: 'goal',
  TIMELINE_SELECT: 'timeline',
  DIAGNOSTIC: 'diagnostic',
  GENERATING: 'generating',
  // Post-placement flow
  PLACEMENT_COMPLETE: 'placement_complete',
  UNLOCK_RESULT: 'unlock_result',
  KNOWLEDGE_MAP: 'knowledge_map',
  REWARD_PREVIEW: 'reward_preview',
  REGISTRATION_GATE: 'registration_gate',
  POST_LOGIN_CELEBRATION: 'post_login_celebration',
  MAIN_HOME: 'main_home',
}

function OnboardingOverlay({ onExit, onComplete, initialSelections = {} }) {
  const [phase, setPhase] = useState(PHASES.COURSE_SELECT)
  const [direction, setDirection] = useState(1)
  const [selections, setSelections] = useState({
    course: null,
    goal: null,
    timeline: null,
    daysUntilExam: null,
    urgency: null,
    examTimeline: null,
    ...initialSelections,
  })
  const [testState, setTestState] = useState({
    answers: [],
    startTime: null,
    analysis: null,
  })
  // Current question data from adaptive engine
  const [currentQuestionData, setCurrentQuestionData] = useState(null)
  const [authState, setAuthState] = useState({
    isLoggedIn: false,
    skippedLogin: false,
  })

  const { user } = useAuth()

  // Helper to update selections
  const updateSelection = (key, value) => {
    setSelections(prev => ({ ...prev, [key]: value }))
  }

  // Watch for user login (from OAuth callback)
  useEffect(() => {
    if (user && phase === PHASES.REGISTRATION_GATE) {
      // User just logged in via OAuth
      setAuthState({ isLoggedIn: true, skippedLogin: false })
      setPhase(PHASES.POST_LOGIN_CELEBRATION)
    }
  }, [user, phase])

  // Save state before OAuth redirect
  const saveStateBeforeOAuth = useCallback(() => {
    const stateToSave = {
      phase,
      selections,
      testState,
    }
    localStorage.setItem('claire_onboarding_state', JSON.stringify(stateToSave))
  }, [phase, selections, testState])

  // Restore state on mount (after OAuth redirect)
  useEffect(() => {
    const saved = localStorage.getItem('claire_onboarding_state')
    if (saved && user) {
      try {
        const state = JSON.parse(saved)
        // Only restore if we were at registration gate
        if (state.phase === PHASES.REGISTRATION_GATE) {
          setTestState(state.testState)
          setAuthState({ isLoggedIn: true, skippedLogin: false })
          setPhase(PHASES.POST_LOGIN_CELEBRATION)
          localStorage.removeItem('claire_onboarding_state')
        }
      } catch (e) {
        console.error('Failed to restore state:', e)
      }
    }
  }, [user])

  const handleCourseSelected = () => {
    setDirection(1)
    setPhase(PHASES.GOAL_SELECT)
  }

  const handleGoalSelected = () => {
    setDirection(1)
    setPhase(PHASES.TIMELINE_SELECT)
  }

  const handleTimelineSelected = () => {
    setDirection(1)
    // Fetch first question from adaptive engine
    const course = selections.course || 'math126'
    const firstQ = getNextQuestion([], course)
    setCurrentQuestionData(firstQ)
    setTestState((prev) => ({ ...prev, startTime: Date.now(), answers: [] }))
    setPhase(PHASES.DIAGNOSTIC)
  }

  const handleSkipDiagnostic = () => {
    // Skip diagnostic entirely - go straight to generating with "unknown" results
    setDirection(1)
    const skippedAnalysis = {
      skillLevel: 'Let\'s Find Out',
      skillEmoji: '🎯',
      skillColor: '#1cb0f6',
      levelDescription: 'Start practicing to discover your strengths and gaps!',
      gaps: [],
      strengths: [],
      blockerMessage: 'Complete some practice problems and we\'ll map your skills.',
      predictedGrade: 'TBD',
      highestTier: 0,
      totalAnswered: 0,
      correctCount: 0,
      diagnosticSkipped: true,
    }
    setTestState((prev) => ({ ...prev, analysis: skippedAnalysis }))
    setPhase(PHASES.GENERATING)
  }

  const handleAnswerSubmit = useCallback((questionId, isCorrect, skipped = false) => {
    setTestState((prev) => ({
      ...prev,
      answers: [...prev.answers, { questionId, isCorrect, skipped }],
    }))
  }, [])

  const handleNextQuestion = useCallback(() => {
    const course = selections.course || 'math126'
    // Build updated answers array with the just-submitted answer
    const updatedAnswers = testState.answers
    const nextQ = getNextQuestion(updatedAnswers, course)

    if (nextQ) {
      // More questions to go
      setDirection(1)
      setCurrentQuestionData(nextQ)
    } else {
      // Test complete - analyze results
      const analysis = analyzeResults(updatedAnswers, course)
      setTestState((prev) => ({ ...prev, analysis }))
      setPhase(PHASES.GENERATING)
    }
  }, [testState.answers, selections.course])

  const handleGeneratingComplete = () => {
    if (!testState.analysis) {
      const analysis = analyzeResults(testState.answers, selections.course)
      setTestState((prev) => ({ ...prev, analysis }))
    }
    setPhase(PHASES.PLACEMENT_COMPLETE)
  }

  // Post-placement navigation handlers
  const handlePlacementComplete = () => {
    console.log('[Onboarding] PLACEMENT_COMPLETE → UNLOCK_RESULT')
    setPhase(PHASES.UNLOCK_RESULT)
  }
  const handleUnlockResult = () => {
    console.log('[Onboarding] UNLOCK_RESULT → KNOWLEDGE_MAP')
    setPhase(PHASES.KNOWLEDGE_MAP)
  }
  const handleKnowledgeMap = () => {
    // Skip STUDY_PLAN_SELECT since exam timeline was already asked in TimelineSelection
    console.log('[Onboarding] KNOWLEDGE_MAP → REWARD_PREVIEW')
    setPhase(PHASES.REWARD_PREVIEW)
  }
  const handleRewardPreview = () => {
    console.log('[Onboarding] REWARD_PREVIEW → REGISTRATION_GATE')
    // Save state before going to registration (in case of OAuth redirect)
    saveStateBeforeOAuth()
    setPhase(PHASES.REGISTRATION_GATE)
  }

  const handleLogin = () => {
    console.log('[Onboarding] Login → POST_LOGIN_CELEBRATION')
    // This is now handled by useEffect watching user
    setAuthState({ isLoggedIn: true, skippedLogin: false })
    setPhase(PHASES.POST_LOGIN_CELEBRATION)
  }

  const handleSkipLogin = () => {
    // Skip login and go directly to dashboard (anonymous mode)
    console.log('[Onboarding] Skip login → complete onboarding (anonymous)')
    setAuthState({ isLoggedIn: false, skippedLogin: true })
    // Call onComplete to save to localStorage and navigate to /dashboard
    onComplete(selections, testState)
  }

  const handlePostLoginCelebration = () => {
    // After login celebration, complete onboarding
    console.log('[Onboarding] POST_LOGIN_CELEBRATION → complete onboarding')
    onComplete(selections, testState)
  }

  const handleBack = () => {
    if (phase === PHASES.DIAGNOSTIC) {
      // In adaptive mode, going back exits diagnostic entirely (no question history navigation)
      setDirection(-1)
      setPhase(PHASES.TIMELINE_SELECT)
      setCurrentQuestionData(null)
      setTestState((prev) => ({ ...prev, answers: [] }))
    } else if (phase === PHASES.TIMELINE_SELECT) {
      setDirection(-1)
      setPhase(PHASES.GOAL_SELECT)
    } else if (phase === PHASES.GOAL_SELECT) {
      setDirection(-1)
      setPhase(PHASES.COURSE_SELECT)
    } else if (phase === PHASES.KNOWLEDGE_MAP) {
      setPhase(PHASES.UNLOCK_RESULT)
    } else if (phase === PHASES.REWARD_PREVIEW) {
      setPhase(PHASES.KNOWLEDGE_MAP)
    } else if (phase === PHASES.UNLOCK_RESULT) {
      setPhase(PHASES.PLACEMENT_COMPLETE)
    } else if (phase === PHASES.COURSE_SELECT) {
      onExit()
    }
    // For other phases (GENERATING, PLACEMENT_COMPLETE, REGISTRATION_GATE, POST_LOGIN_CELEBRATION, MAIN_HOME),
    // back button is not shown, so this shouldn't be called
  }

  // Determine which phases show back button
  const phasesWithBackButton = [
    PHASES.COURSE_SELECT,
    PHASES.GOAL_SELECT,
    PHASES.TIMELINE_SELECT,
    PHASES.DIAGNOSTIC,
    PHASES.KNOWLEDGE_MAP,
    PHASES.REWARD_PREVIEW,
  ]
  const showBackButton = phasesWithBackButton.includes(phase)
  const showProgress = phase === PHASES.DIAGNOSTIC

  return (
    <motion.div
      className="fixed inset-0 z-[100] bg-white flex flex-col"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <header className="h-16 px-4 flex items-center shrink-0 relative z-10">
        <div className="w-12">
          {showBackButton && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <BackButton onClick={handleBack} />
            </motion.div>
          )}
        </div>
        <div className="flex-1 px-4">
          {showProgress && currentQuestionData && (
            <DiagnosticProgress
              questionNumber={currentQuestionData.questionNumber}
              totalQuestions={currentQuestionData.totalQuestions}
              progressPercent={currentQuestionData.progressPercent}
              answers={testState.answers}
            />
          )}
        </div>
        <div className="w-12">
          {phase === PHASES.COURSE_SELECT && (
            <motion.button
              onClick={onExit}
              className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <svg
                className="w-6 h-6 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </motion.button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-h-0">
        <AnimatePresence mode="wait" initial={false} custom={direction}>
          {phase === PHASES.COURSE_SELECT && (
            <PathSelection
              key="course"
              direction={direction}
              onNext={handleCourseSelected}
              selections={selections}
              updateSelection={updateSelection}
            />
          )}

          {phase === PHASES.GOAL_SELECT && (
            <GoalSelection
              key="goal"
              direction={direction}
              onNext={handleGoalSelected}
              selections={selections}
              updateSelection={updateSelection}
            />
          )}

          {phase === PHASES.TIMELINE_SELECT && (
            <TimelineSelection
              key="timeline"
              direction={direction}
              onNext={handleTimelineSelected}
              onSkipDiagnostic={handleSkipDiagnostic}
              selections={selections}
              updateSelection={updateSelection}
            />
          )}

          {phase === PHASES.DIAGNOSTIC && currentQuestionData && (
            <DiagnosticQuestion
              key={`q-${currentQuestionData.questionNumber}`}
              direction={direction}
              question={currentQuestionData.question}
              questionNumber={currentQuestionData.questionNumber}
              totalQuestions={currentQuestionData.totalQuestions}
              onAnswerSubmit={handleAnswerSubmit}
              onNext={handleNextQuestion}
              course={selections.course}
            />
          )}

          {phase === PHASES.GENERATING && (
            <ReportGenerating
              key="generating"
              testState={testState}
              course={selections.course}
              onComplete={handleGeneratingComplete}
            />
          )}

          {/* Post-placement screens */}
          {phase === PHASES.PLACEMENT_COMPLETE && (
            <PlacementComplete
              key="placement-complete"
              testState={testState}
              onNext={handlePlacementComplete}
            />
          )}

          {phase === PHASES.UNLOCK_RESULT && (
            <UnlockResult
              key="unlock-result"
              testState={testState}
              onNext={handleUnlockResult}
            />
          )}

          {phase === PHASES.KNOWLEDGE_MAP && (
            <KnowledgeMap
              key="knowledge-map"
              testState={testState}
              selections={selections}
              onNext={handleKnowledgeMap}
            />
          )}

          {phase === PHASES.REWARD_PREVIEW && (
            <RewardPreview
              key="reward-preview"
              testState={testState}
              selections={selections}
              onNext={handleRewardPreview}
            />
          )}

          {phase === PHASES.REGISTRATION_GATE && (
            <RegistrationGate
              key="registration"
              onLogin={handleLogin}
              onSkip={handleSkipLogin}
            />
          )}

          {phase === PHASES.POST_LOGIN_CELEBRATION && (
            <PostLoginCelebration
              key="celebration"
              onNext={handlePostLoginCelebration}
            />
          )}

          {phase === PHASES.MAIN_HOME && (
            <MainHome
              key="main-home"
              testState={testState}
              selections={selections}
              onComplete={() => onComplete(selections, testState)}
            />
          )}
        </AnimatePresence>
      </main>
    </motion.div>
  )
}

export default OnboardingOverlay
