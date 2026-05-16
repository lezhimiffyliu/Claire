/**
 * Problem Loader - 从 FastAPI 后端加载题库
 */

const API_BASE = 'http://localhost:8000'

// 缓存
const cache = new Map()

/**
 * 加载课程所有题目
 */
export async function loadProblems(course) {
  const cacheKey = `problems_${course}`
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey)
  }

  const response = await fetch(`${API_BASE}/problems?course=${course}`)
  if (!response.ok) {
    throw new Error(`Failed to load problems: ${response.status}`)
  }

  const data = await response.json()
  const problems = data.problems || []
  cache.set(cacheKey, problems)
  return problems
}

/**
 * 获取单个题目
 */
export async function getProblemById(problemId) {
  const response = await fetch(`${API_BASE}/problems/${problemId}`)
  if (!response.ok) {
    throw new Error(`Problem not found: ${problemId}`)
  }
  return response.json()
}

/**
 * 获取考试列表
 */
export async function getExamList(course) {
  const problems = await loadProblems(course)
  const examMap = new Map()

  for (const p of problems) {
    const exam = p.exam
    if (!exam) continue
    if (!examMap.has(exam)) {
      examMap.set(exam, { id: exam, problemCount: 0, partCount: 0 })
    }
    const entry = examMap.get(exam)
    entry.problemCount++
    entry.partCount += p.parts?.length || 0
  }

  const exams = Array.from(examMap.values())
  // Sort by date (newest first): wi25 > au24 > sp24 > wi24 > ...
  exams.sort((a, b) => {
    const parseExam = (id) => {
      const season = id.slice(0, 2)
      const year = parseInt('20' + id.slice(2, 4))
      // Season order: wi=1 (Jan), sp=4 (Apr), au=10 (Oct)
      const seasonMonth = { wi: 1, sp: 4, au: 10 }
      return year * 12 + (seasonMonth[season] || 0)
    }
    return parseExam(b.id) - parseExam(a.id)
  })

  return exams.map(exam => ({
    ...exam,
    displayName: formatExamName(exam.id),
  }))
}

/**
 * 获取 topic 列表
 */
export async function getTopicList(course) {
  const problems = await loadProblems(course)
  const topicMap = new Map()

  for (const p of problems) {
    const topic = p.topic
    if (!topic) continue
    if (!topicMap.has(topic)) {
      topicMap.set(topic, { id: topic, count: 0 })
    }
    topicMap.get(topic).count++
  }

  const topics = Array.from(topicMap.values())
  topics.sort((a, b) => b.count - a.count)

  return topics.map(t => ({
    ...t,
    displayName: t.id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
  }))
}

function formatExamName(examId) {
  if (!examId) return ''
  const seasonMap = { au: 'Autumn', wi: 'Winter', sp: 'Spring' }
  const season = seasonMap[examId.slice(0, 2)] || ''
  const year = '20' + examId.slice(2, 4)
  return `${season} ${year}`
}

// Topic display name mapping
const TOPIC_DISPLAY_NAMES = {
  vectors_and_geometry: 'Vectors',
  lines_and_planes: 'Lines & Planes',
  quadric_surfaces: 'Quadric Surfaces',
  vector_valued_functions: 'Vector Functions',
  motion_in_space: 'Motion in Space',
  multivariable_functions: 'Multivariable Functions',
  partial_derivatives: 'Partial Derivatives',
  tangent_planes_and_differentials: 'Tangent Planes',
  multivariable_optimization: 'Optimization',
  double_integrals: 'Double Integrals',
  polar_coordinates: 'Polar Coordinates',
  applications_of_double_integrals: 'Applications',
  taylor_polynomials_and_series: 'Taylor Series',
}

/**
 * Parse exam ID to get sortable date value
 */
function parseExamDate(examId) {
  if (!examId) return 0
  // Handle formats like "au23_final" or "au23"
  const base = examId.split('_')[0]
  const season = base.slice(0, 2)
  const yearStr = base.slice(2, 4)
  const year = parseInt('20' + yearStr)
  // Season order: wi=1 (Jan), sp=4 (Apr), au=10 (Oct)
  const seasonMonth = { wi: 1, sp: 4, au: 10 }
  return year * 12 + (seasonMonth[season] || 0)
}

/**
 * Get detailed exam list with stats for ANY course
 * Returns: { id, displayName, questionCount, totalPoints, estimatedMinutes, topics }
 */
export async function getCourseFinals(course) {
  console.log('[problemLoader] getCourseFinals:', course)
  const problems = await loadProblems(course)
  const examMap = new Map()

  for (const p of problems) {
    const exam = p.exam
    if (!exam) continue
    // Only include finals
    if (!exam.includes('final')) continue

    if (!examMap.has(exam)) {
      examMap.set(exam, {
        id: exam,
        problems: [],
        totalPoints: 0,
        questionCount: 0,
        topicSet: new Set(),
      })
    }
    const entry = examMap.get(exam)
    entry.problems.push(p)
    entry.totalPoints += p.points || 0
    entry.questionCount += p.parts?.length || 1
    if (p.topic) {
      entry.topicSet.add(p.topic)
    }
  }

  const courseDisplayMap = { '124': 'Math 124', '125': 'Math 125', '126': 'Math 126' }
  const courseDisplay = courseDisplayMap[course] || `Math ${course}`

  const exams = Array.from(examMap.values()).map(exam => {
    // Extract base exam ID (e.g., "au23" from "au23_final")
    const baseId = exam.id.split('_')[0]
    return {
      id: exam.id,
      displayName: formatExamName(baseId) + ' Final',
      courseDisplay,
      questionCount: exam.questionCount,
      problemCount: exam.problems.length,
      totalPoints: exam.totalPoints,
      estimatedMinutes: Math.round(exam.totalPoints * 1.5),
      topics: Array.from(exam.topicSet).map(t => TOPIC_DISPLAY_NAMES[t] || t),
      problems: exam.problems,
    }
  })

  // Sort by date (newest first)
  exams.sort((a, b) => parseExamDate(b.id) - parseExamDate(a.id))

  console.log('[problemLoader] getCourseFinals found', exams.length, 'finals for course', course)
  return exams
}

/**
 * Get detailed exam list with stats (Math 126 finals only) - DEPRECATED, use getCourseFinals
 */
export async function getMath126Finals() {
  console.warn('[problemLoader] getMath126Finals is deprecated, use getCourseFinals(course) instead')
  return getCourseFinals('126')
}

/**
 * Get problems for a specific exam
 */
export async function getExamProblems(course, examId) {
  const problems = await loadProblems(course)
  return problems.filter(p => p.exam === examId)
}

export default {
  loadProblems,
  getProblemById,
  getExamList,
  getTopicList,
  getCourseFinals,
  getMath126Finals,
  getExamProblems,
}
