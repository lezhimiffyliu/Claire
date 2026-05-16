import { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase'

/**
 * Handles OAuth callback from Supabase.
 * This component should be rendered at /auth/callback route.
 */
function AuthCallback({ onSuccess, onError }) {
  const [status, setStatus] = useState('processing')

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Supabase will automatically handle the OAuth callback
        // when detectSessionInUrl is true
        const { data, error } = await supabase.auth.getSession()

        if (error) {
          console.error('Auth callback error:', error)
          setStatus('error')
          onError?.(error)
          return
        }

        if (data.session) {
          setStatus('success')
          onSuccess?.(data.session)
        } else {
          setStatus('no-session')
        }
      } catch (err) {
        console.error('Auth callback exception:', err)
        setStatus('error')
        onError?.(err)
      }
    }

    handleCallback()
  }, [onSuccess, onError])

  if (status === 'processing') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#58cc02] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Signing you in...</p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="text-5xl mb-4">😕</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Sign in failed</h2>
          <p className="text-gray-500 mb-4">Something went wrong. Please try again.</p>
          <button
            onClick={() => window.location.href = '/'}
            className="btn-squishy btn-green"
          >
            Back to home
          </button>
        </div>
      </div>
    )
  }

  return null
}

export default AuthCallback
