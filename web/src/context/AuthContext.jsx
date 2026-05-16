import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from '../lib/supabase'
import { saveStudentProfile, getStudentProfile } from '../api/supabaseApi'

const AuthContext = createContext({
  user: null,
  session: null,
  loading: true,
  signInWithGoogle: async () => {},
  signOut: async () => {},
  requireAuth: () => false,
  showLoginModal: false,
  closeLoginModal: () => {},
})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)
  const hasSyncedRef = useRef(false)

  // Sync localStorage to Supabase when user logs in
  const syncLocalToSupabase = useCallback(async (loggedInUser) => {
    if (!loggedInUser?.id || hasSyncedRef.current) return

    try {
      // Check if user has local onboarding data
      const localComplete = localStorage.getItem('claire_onboarding_complete')
      const localSelections = localStorage.getItem('claire_selections')
      const localTestState = localStorage.getItem('claire_test_state')

      if (!localComplete || !localSelections) {
        console.log('[AuthContext] No local onboarding data to sync')
        return
      }

      // Check if user already has a profile in Supabase
      const existingProfile = await getStudentProfile(loggedInUser.id)
      if (existingProfile) {
        console.log('[AuthContext] User already has Supabase profile, skipping sync')
        return
      }

      // Parse local data and sync to Supabase
      const selections = JSON.parse(localSelections)
      const testState = localTestState ? JSON.parse(localTestState) : {}

      await saveStudentProfile(loggedInUser.id, { selections, testState })
      console.log('[AuthContext] Successfully synced local data to Supabase')

      hasSyncedRef.current = true
    } catch (error) {
      console.error('[AuthContext] Failed to sync local data to Supabase:', error)
      // Don't throw - sync failure shouldn't break the app
    }
  }, [])

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)

      // Sync if user is already logged in
      if (session?.user) {
        syncLocalToSupabase(session.user)
      }
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)

      // Sync when user logs in
      if (_event === 'SIGNED_IN' && session?.user) {
        syncLocalToSupabase(session.user)
      }

      // Reset sync flag when user logs out
      if (_event === 'SIGNED_OUT') {
        hasSyncedRef.current = false
      }
    })

    return () => subscription.unsubscribe()
  }, [syncLocalToSupabase])

  const signInWithGoogle = async () => {
    const redirectUrl = window.location.origin + '/auth/callback'

    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: redirectUrl,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    })

    if (error) {
      console.error('Google sign in error:', error)
      throw error
    }

    return data
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) {
      console.error('Sign out error:', error)
      throw error
    }
  }

  // Check if user is authenticated, show login modal if not
  // Returns true if authenticated, false if login required
  const requireAuth = useCallback((onSuccess = null) => {
    if (user) {
      // Already logged in, execute callback immediately
      if (onSuccess) onSuccess(user)
      return true
    }
    // Not logged in, show modal and save pending action
    setPendingAction(() => onSuccess)
    setShowLoginModal(true)
    return false
  }, [user])

  const closeLoginModal = useCallback(() => {
    setShowLoginModal(false)
    setPendingAction(null)
  }, [])

  // Execute pending action when user logs in
  useEffect(() => {
    if (user && pendingAction) {
      pendingAction(user)
      setPendingAction(null)
      setShowLoginModal(false)
    }
  }, [user, pendingAction])

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        signInWithGoogle,
        signOut,
        requireAuth,
        showLoginModal,
        closeLoginModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
