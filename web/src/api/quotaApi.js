/**
 * Quota & Payment API
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Get current user's quota status
 */
export async function getQuotaStatus(accessToken = null) {
  const headers = {
    'Content-Type': 'application/json',
  }
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE}/api/quota`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    throw new Error(`Quota check failed: ${response.status}`)
  }

  return response.json()
}

/**
 * Create Stripe checkout session
 */
export async function createCheckout(userId, email) {
  const response = await fetch(`${API_BASE}/api/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, email }),
  })

  if (!response.ok) {
    throw new Error(`Checkout failed: ${response.status}`)
  }

  return response.json()
}

/**
 * Get Stripe customer portal URL
 */
export async function getPortalUrl(accessToken) {
  const response = await fetch(`${API_BASE}/api/portal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Portal failed: ${response.status}`)
  }

  return response.json()
}
