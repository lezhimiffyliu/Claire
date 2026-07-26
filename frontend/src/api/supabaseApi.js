/**
 * Supabase API - 写入数据库
 * 表结构参考 learning_context.py 和 attempt_tracker.py
 */

import { supabase } from '../lib/supabase'

/**
 * 创建 workspace 和 student_profile
 * @param {string} userId - User ID (required)
 * @param {object} data - Profile data
 * @returns {object|null} - Returns null if userId is missing
 */
export async function saveStudentProfile(userId, data) {
  if (!userId) {
    console.warn('[supabaseApi] saveStudentProfile called without userId, skipping')
    return null
  }

  const { course, goal, daysUntilExam, examTimeline } = data.selections || {}
  const { analysis } = data.testState || {}

  // 1. 先停用旧的 workspace
  await supabase
    .from('workspaces')
    .update({ is_active: false })
    .eq('user_id', userId)

  // 2. 创建新 workspace
  const { data: workspace, error: wsError } = await supabase
    .from('workspaces')
    .insert({
      user_id: userId,
      course: course || 'math124',
      is_active: true,
    })
    .select()
    .single()

  if (wsError) {
    console.error('[supabaseApi] workspace insert error:', wsError)
    throw wsError
  }

  // 3. 创建 student_profile
  const profileData = {
    workspace_id: workspace.id,
    user_id: userId,
    profile_data: {
      goal: goal,
      daysUntilExam: daysUntilExam,
      examTimeline: examTimeline,
      analysis: analysis,
      selections: data.selections,
    },
    checkpoint: { type: 'practice' },
    diagnostic_completed: true,
  }

  const { data: profile, error: profileError } = await supabase
    .from('student_profiles')
    .insert(profileData)
    .select()
    .single()

  if (profileError) {
    console.error('[supabaseApi] profile insert error:', profileError)
    throw profileError
  }

  console.log('[supabaseApi] Created workspace and profile:', { workspace, profile })
  return { workspace, profile }
}

/**
 * 获取 student_profile
 * @param {string} userId - User ID (required)
 * @returns {object|null} - Returns null if userId is missing or profile not found
 */
export async function getStudentProfile(userId) {
  if (!userId) {
    console.warn('[supabaseApi] getStudentProfile called without userId, skipping')
    return null
  }

  // 获取 active workspace 和关联的 profile
  const { data, error } = await supabase
    .from('workspaces')
    .select('*, student_profiles(*)')
    .eq('user_id', userId)
    .eq('is_active', true)
    .single()

  if (error && error.code !== 'PGRST116') {
    console.error('[supabaseApi] getStudentProfile error:', error)
  }

  return data
}

/**
 * 记录 attempt（用作 solve session）
 * 使用已有的 attempt_history 表
 * @param {string} userId - User ID (required)
 * @param {string} problemId - Problem ID
 * @param {object} problemData - Problem metadata
 * @returns {object|null} - Returns null if userId is missing
 */
export async function createSolveSession(userId, problemId, problemData) {
  if (!userId) {
    console.warn('[supabaseApi] createSolveSession called without userId, skipping')
    return null
  }

  // 先获取 workspace_id
  const { data: workspace } = await supabase
    .from('workspaces')
    .select('id')
    .eq('user_id', userId)
    .eq('is_active', true)
    .single()

  const attemptData = {
    user_id: userId,
    workspace_id: workspace?.id || null,
    question_id: problemId,
    source: 'practice',
    topic: problemData?.topic,
    // 其他字段待填
  }

  const { data, error } = await supabase
    .from('attempt_history')
    .insert(attemptData)
    .select()
    .single()

  if (error) {
    console.error('[supabaseApi] createSolveSession error:', error)
    throw error
  }

  console.log('[supabaseApi] Created attempt/session:', data)
  return data
}

/**
 * 更新 attempt
 * @param {string} sessionId - Session ID (required)
 * @param {object} updates - Fields to update
 * @returns {object|null} - Returns null if sessionId is missing
 */
export async function updateSolveSession(sessionId, updates) {
  if (!sessionId) {
    console.warn('[supabaseApi] updateSolveSession called without sessionId, skipping')
    return null
  }

  const { data, error } = await supabase
    .from('attempt_history')
    .update({
      is_correct: updates.status === 'completed' ? true : null,
      ...updates,
    })
    .eq('id', sessionId)
    .select()
    .single()

  if (error) {
    console.error('[supabaseApi] updateSolveSession error:', error)
    throw error
  }

  return data
}

export default {
  saveStudentProfile,
  getStudentProfile,
  createSolveSession,
  updateSolveSession,
}
