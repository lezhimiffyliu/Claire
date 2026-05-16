/**
 * Extract user display info from Supabase user object
 *
 * Checks multiple possible locations for Google OAuth data:
 * - user.user_metadata (Supabase standard)
 * - user.identities[0].identity_data (identity provider data)
 *
 * @param {Object} user - Supabase user object
 * @returns {Object} { avatarUrl, displayName, initials, email }
 */
export function getUserDisplayInfo(user) {
  const avatarUrl =
    user?.user_metadata?.avatar_url ||
    user?.user_metadata?.picture ||
    user?.identities?.[0]?.identity_data?.avatar_url ||
    user?.identities?.[0]?.identity_data?.picture ||
    null

  const displayName =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.identities?.[0]?.identity_data?.full_name ||
    user?.identities?.[0]?.identity_data?.name ||
    user?.email?.split('@')[0] ||
    'Student'

  const initials = displayName
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'U'

  const email = user?.email || ''

  // Validate avatar URL
  const validAvatarUrl = avatarUrl && avatarUrl.startsWith('http') ? avatarUrl : null

  return { avatarUrl: validAvatarUrl, displayName, initials, email }
}

export default getUserDisplayInfo
