import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getQuotaStatus, createCheckout } from '../../api/quotaApi'

/**
 * UpgradeCard - Subtle upgrade prompt
 *
 * Design principles (v3):
 * - No large gradient cards
 * - No attention-grabbing colors
 * - Positioned as secondary information
 * - Only becomes prominent when quota is exhausted
 */
export default function UpgradeCard({ className = '' }) {
  const { user, session } = useAuth()
  const [quota, setQuota] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchQuota() {
      try {
        const accessToken = session?.access_token || null
        const data = await getQuotaStatus(accessToken)
        setQuota(data)
      } catch (e) {
        console.error('Quota fetch failed:', e)
        // Don't show error to user - just hide the card
        setQuota(null)
      } finally {
        setLoading(false)
      }
    }
    fetchQuota()
  }, [session])

  const handleUpgrade = async () => {
    if (!user) {
      window.location.href = '/login'
      return
    }

    setCheckoutLoading(true)
    try {
      const data = await createCheckout(user.id, user.email)
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        setError(data.error || 'Could not create checkout')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setCheckoutLoading(false)
    }
  }

  // Don't show anything while loading
  if (loading) return null

  // Don't show for Pro users
  if (quota?.is_pro) {
    return (
      <div className={`card-subtle flex items-center gap-2 ${className}`}>
        <div className="w-5 h-5 rounded-full bg-[var(--claire-success-bg)] flex items-center justify-center">
          <svg className="w-3 h-3 text-[var(--claire-success)]" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <span className="text-sm text-[var(--claire-text-secondary)]">Pro</span>
      </div>
    )
  }

  // Don't show if quota fetch failed (no "Load failed" message)
  if (!quota) return null

  const remaining = quota?.remaining ?? 0
  const limit = quota?.limit ?? 20
  const limitReached = quota?.limit_reached ?? false

  // Exhausted state - slightly more prominent
  if (limitReached) {
    return (
      <div className={`card-standard ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-[var(--claire-weak-bg)] flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--claire-weak)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p className="font-medium text-[var(--claire-text-primary)]">
              Free reviews used
            </p>
            <p className="text-sm text-[var(--claire-text-secondary)]">
              Upgrade for unlimited access
            </p>
          </div>
        </div>

        <button
          onClick={handleUpgrade}
          disabled={checkoutLoading}
          className="w-full btn-hero text-sm py-3"
        >
          {checkoutLoading ? 'Processing...' : 'Upgrade — $9.99/mo'}
        </button>

        {error && (
          <p className="text-xs text-[var(--claire-weak)] mt-2">{error}</p>
        )}
      </div>
    )
  }

  // Normal state - very subtle
  return (
    <div className={`card-subtle ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-[var(--claire-text-secondary)]">
            {remaining}/{limit} reviews left
          </span>
        </div>
        <button
          onClick={handleUpgrade}
          disabled={checkoutLoading}
          className="btn-link text-xs"
        >
          {checkoutLoading ? '...' : 'Upgrade'}
        </button>
      </div>
    </div>
  )
}

/**
 * UpgradeBanner - Compact inline banner
 */
export function UpgradeBanner({ className = '' }) {
  const { user, session } = useAuth()
  const [quota, setQuota] = useState(null)
  const [checkoutLoading, setCheckoutLoading] = useState(false)

  useEffect(() => {
    async function fetchQuota() {
      try {
        const accessToken = session?.access_token || null
        const data = await getQuotaStatus(accessToken)
        setQuota(data)
      } catch (e) {
        console.error('Quota fetch failed:', e)
      }
    }
    fetchQuota()
  }, [session])

  const handleUpgrade = async () => {
    if (!user) return
    setCheckoutLoading(true)
    try {
      const data = await createCheckout(user.id, user.email)
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    } catch (e) {
      console.error('Checkout failed:', e)
    } finally {
      setCheckoutLoading(false)
    }
  }

  if (quota?.is_pro) return null
  if (!quota) return null

  const remaining = quota?.remaining ?? 0
  const limit = quota?.limit ?? 20
  const limitReached = quota?.limit_reached ?? false

  return (
    <div className={`flex items-center justify-between py-2 px-3 rounded-lg bg-[var(--claire-bg)] border border-[var(--claire-border)] ${className}`}>
      <span className="text-sm text-[var(--claire-text-secondary)]">
        {limitReached ? 'Reviews used' : `${remaining}/${limit} left`}
      </span>
      {user && (
        <button
          onClick={handleUpgrade}
          disabled={checkoutLoading}
          className="btn-link text-xs"
        >
          {checkoutLoading ? '...' : 'Upgrade'}
        </button>
      )}
    </div>
  )
}
