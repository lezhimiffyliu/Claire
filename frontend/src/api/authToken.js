/**
 * authToken — single source of the Bearer token sent to the backend.
 *
 * Supabase is the auth provider. When a user has a Supabase session we send its
 * access token; otherwise there is no token and the request is treated as
 * anonymous by the backend.
 */
import { supabase } from '../lib/supabase'

export async function getAuthToken() {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession()
    return session?.access_token || null
  } catch {
    return null
  }
}
