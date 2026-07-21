import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import LandingPage from './components/LandingPage'
import OnboardingOverlay from './components/onboarding/OnboardingOverlay'
import AuthCallback from './components/auth/AuthCallback'
import DashboardNew from './components/dashboard/DashboardNew'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ClaireProvider } from './context/ClaireContext'
// ClairePanel removed - no floating coach UI
import ErrorBoundary from './components/ErrorBoundary'
import LoginModal from './components/auth/LoginModal'
import { saveStudentProfile } from './api/supabaseApi'
import { saveAnonymousLearningState } from './utils/anonymousLearningState'

// Check if onboarding is complete
function isOnboardingComplete() {
  return localStorage.getItem('claire_onboarding_complete') === 'true'
}

// Save onboarding state to localStorage only
// Supabase write is handled in OnboardingPage after requireAuth
export function saveOnboardingToLocal(selections, testState) {
  localStorage.setItem('claire_onboarding_complete', 'true')
  localStorage.setItem('claire_selections', JSON.stringify(selections))
  localStorage.setItem('claire_test_state', JSON.stringify(testState))
}

// Get saved state
export function getSavedState() {
  try {
    const selections = JSON.parse(localStorage.getItem('claire_selections') || '{}')
    const testState = JSON.parse(localStorage.getItem('claire_test_state') || '{}')
    return { selections, testState }
  } catch {
    return { selections: {}, testState: {} }
  }
}

// Landing page with navigation
function LandingPageWithNav() {
  const navigate = useNavigate()
  const { user } = useAuth()

  // If onboarding complete (logged in or anonymous), redirect to dashboard
  useEffect(() => {
    if (isOnboardingComplete()) {
      navigate('/dashboard', { replace: true })
    }
  }, [navigate])

  const handleGetStarted = () => {
    navigate('/onboarding')
  }

  return <LandingPage onGetStarted={handleGetStarted} />
}

// Onboarding page
function OnboardingPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  // Track selections and test state locally
  const savedState = getSavedState()

  const handleExit = () => {
    navigate('/')
  }

  const handleComplete = async (selections, testState) => {
    console.log('[App] handleComplete called', { user: !!user, selections, testState })
    console.log('[App] Selected course:', selections.course)

    // Always save to localStorage (works for anonymous users)
    localStorage.setItem('claire_onboarding_complete', 'true')
    localStorage.setItem('claire_selections', JSON.stringify(selections))
    localStorage.setItem('claire_test_state', JSON.stringify(testState))
    console.log('[App] localStorage claire_selections saved:', selections.course)

    // Save complete anonymous learning state (for dashboard hydration)
    saveAnonymousLearningState({ selections, testState })
    console.log('[App] Saved to localStorage + anonymous learning state')

    // If logged in, also save to Supabase
    if (user) {
      try {
        await saveStudentProfile(user.id, { selections, testState })
        console.log('[App] Profile saved to Supabase')
      } catch (error) {
        console.error('[App] Failed to save profile to Supabase:', error)
        // Continue anyway - localStorage is the source of truth for now
      }
    }

    // Navigate to dashboard regardless of login status
    console.log('[App] Navigating to /dashboard')
    navigate('/dashboard', { replace: true })
  }

  return (
    <OnboardingOverlay
      onExit={handleExit}
      onComplete={handleComplete}
      initialSelections={savedState.selections}
    />
  )
}

// Protected dashboard route
function DashboardPage() {
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const savedState = getSavedState()

  // If not complete onboarding, redirect
  useEffect(() => {
    if (!loading && !isOnboardingComplete()) {
      navigate('/onboarding', { replace: true })
    }
  }, [loading, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--claire-bg)]">
        <div className="w-8 h-8 border-2 border-[var(--claire-charcoal)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isOnboardingComplete()) {
    return null // Will redirect
  }

  const handleBack = () => {
    navigate('/')
  }

  return (
    <DashboardNew
      onBack={handleBack}
    />
  )
}

// Auth callback handler
function AuthCallbackPage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    // Check if we have saved onboarding state
    const savedOnboarding = localStorage.getItem('claire_onboarding_state')
    if (savedOnboarding) {
      localStorage.removeItem('claire_onboarding_state')
      navigate('/onboarding', { replace: true })
    } else if (isOnboardingComplete()) {
      navigate('/dashboard', { replace: true })
    } else {
      navigate('/', { replace: true })
    }
  }

  const handleError = (error) => {
    console.error('Auth error:', error)
    navigate('/', { replace: true })
  }

  return <AuthCallback onSuccess={handleSuccess} onError={handleError} />
}

// Main app with router
function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPageWithNav />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/practice/:problemId" element={<DashboardPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  // LIFECYCLE DEBUG - logs on every App component mount (including StrictMode double-mount)
  useEffect(() => {
    console.log('[APP] MOUNT - component mounted', { timestamp: Date.now() })
    return () => {
      console.log('[APP] UNMOUNT - component unmounting', { timestamp: Date.now() })
    }
  }, [])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ClaireProvider>
            <AppRoutes />
            <LoginModal />
          </ClaireProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
