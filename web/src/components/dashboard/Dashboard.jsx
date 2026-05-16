import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import TodayTaskCard from './TodayTaskCard'
import ProgressOverview from './ProgressOverview'
import MockExamsPage from './MockExamsPage'
import MockExamView from './MockExamView'
import ProblemPractice from './ProblemPractice'
import { useAuth } from '../../context/AuthContext'
import { loadProblems } from '../../api/problemLoader'
import { getRecommendations, getExamCountdown } from '../../api/problemApi'
import { getStudentProfile } from '../../api/supabaseApi'
import { TOPIC_DISTRIBUTION, getTopicDisplayName } from '../../data/topicDistribution'

// Map course codes
const COURSE_MAP = {
  math124: '124',
  math125: '125',
  math126: '126',
}

const COURSE_NAMES = {
  math124: 'Math 124',
  math125: 'Math 125',
  math126: 'Math 126',
}

/**
 * Map diagnostic skillGap to taxonomy topic
 */
const SKILL_TO_TOPIC_MAP = {
  'derivative_rules': 'derivative_rules',
  'curve_analysis': 'curve_analysis',
  'implicit_differentiation': 'implicit_differentiation',
  'Basic power rule': 'derivative_rules',
  'Constant rule (most basic derivative)': 'derivative_rules',
  'Reading f from a graph of f\'': 'curve_analysis',
  'Sign of f\' tells direction of f': 'curve_analysis',
  'Identifying composite function structure': 'derivative_rules',
  'Chain rule mechanics': 'derivative_rules',
  'Critical points include non-differentiable points': 'curve_analysis',
  'Evaluating implicit derivatives at specific points': 'implicit_differentiation',
  'antiderivatives_and_riemann_sums': 'antiderivatives_and_riemann_sums',
  'fundamental_theorem_of_calculus': 'fundamental_theorem_of_calculus',
  'partial_fractions': 'partial_fractions',
  'substitution': 'substitution',
  'improper_integrals': 'improper_integrals',
  'Basic antiderivative': 'antiderivatives_and_riemann_sums',
  'Antiderivative of a constant': 'antiderivatives_and_riemann_sums',
  'Integral = accumulation of a rate': 'fundamental_theorem_of_calculus',
  'Integral = area (basic geometric meaning)': 'antiderivatives_and_riemann_sums',
  'Recognizing partial fractions setup': 'partial_fractions',
  'U-substitution: computing du correctly': 'substitution',
  'Divergence test goes only one way': 'improper_integrals',
  'Spotting hidden improper integrals': 'improper_integrals',
  'vectors_and_geometry': 'vectors_and_geometry',
  'multivariable_optimization': 'multivariable_optimization',
  'partial_derivatives': 'partial_derivatives',
  'polar_coordinates': 'polar_coordinates',
  'double_integrals': 'double_integrals',
  'taylor_polynomials_and_series': 'taylor_polynomials_and_series',
  'Recognizing perpendicular vectors': 'vectors_and_geometry',
  'Component-wise vector arithmetic': 'vectors_and_geometry',
  'Second Derivative Test: must compute D, not just check signs of f_xx and f_yy': 'multivariable_optimization',
  'Definition of partial derivative': 'partial_derivatives',
  'Recognizing when to switch to polar': 'polar_coordinates',
  'Polar Jacobian (the famous extra r)': 'double_integrals',
  'Lagrange gives candidates, not final answers': 'multivariable_optimization',
  'Taylor\'s Inequality: M must be an upper bound, not a point value': 'taylor_polynomials_and_series',
}

function resolveToTopic(skillGap, taxonomyTopic) {
  if (taxonomyTopic) return taxonomyTopic
  if (SKILL_TO_TOPIC_MAP[skillGap]) return SKILL_TO_TOPIC_MAP[skillGap]
  const snakeCase = skillGap?.toLowerCase().replace(/ /g, '_')
  if (snakeCase && TOPIC_DISTRIBUTION.math124?.find(t => t.topic === snakeCase)) return snakeCase
  if (snakeCase && TOPIC_DISTRIBUTION.math125?.find(t => t.topic === snakeCase)) return snakeCase
  if (snakeCase && TOPIC_DISTRIBUTION.math126?.find(t => t.topic === snakeCase)) return snakeCase
  return null
}

export default function Dashboard({ onBack, selections = {}, testState = {} }) {
  const { problemId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [activeTab, setActiveTab] = useState('learn')
  const [problems, setProblems] = useState([])
  const [loading, setLoading] = useState(true)
  const [practiceProblem, setPracticeProblem] = useState(null)
  const [checkpoints, setCheckpoints] = useState([])
  const [examMode, setExamMode] = useState(null)
  const [workspace, setWorkspace] = useState(null)
  const [streak, setStreak] = useState(7) // Placeholder - would come from backend
  const [todayCompleted, setTodayCompleted] = useState(false)
  const [todayStats, setTodayStats] = useState({ problems: 0, correct: 0 })
  const [weeklyGain, setWeeklyGain] = useState(3) // Placeholder
  const [examCountdown, setExamCountdown] = useState({
    days_until: selections.daysUntilExam || 14,
    source: 'approximate',
    has_date: false,
  })

  const course = selections.course || 'math124'
  const courseCode = COURSE_MAP[course] || '124'
  const analysis = testState.analysis || {}

  // Use exam countdown from API
  const daysUntilExam = examCountdown.days_until

  // Calculate recommended daily time
  const getDailyMinutes = () => {
    if (daysUntilExam <= 3) return 30
    if (daysUntilExam <= 7) return 20
    if (daysUntilExam <= 14) return 15
    return 10
  }
  const dailyMinutes = getDailyMinutes()

  // Check if user has diagnostic data
  const hasDiagnostic = testState.answers?.length > 0

  // Load exam countdown from API
  useEffect(() => {
    async function fetchExamCountdown() {
      try {
        const countdown = await getExamCountdown()
        setExamCountdown(countdown)
      } catch (error) {
        console.warn('Failed to fetch exam countdown:', error)
        // Keep using the default/local values
      }
    }
    fetchExamCountdown()
  }, [user?.id])

  // Load workspace, problems and recommendations
  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        if (user?.id) {
          try {
            const wsData = await getStudentProfile(user.id)
            if (wsData) {
              setWorkspace(wsData)
              if (wsData.streak) setStreak(wsData.streak)
            }
          } catch (wsError) {
            console.warn('Failed to load workspace:', wsError)
          }
        }

        const data = await loadProblems(courseCode)
        setProblems(data)

        try {
          const recResponse = await getRecommendations(courseCode)
          const apiCheckpoints = mapRecommendationsToCheckpoints(
            recResponse.recommendations,
            data,
            analysis.gaps || []
          )
          setCheckpoints(apiCheckpoints)
        } catch (recError) {
          console.warn('Failed to get recommendations, using fallback:', recError)
          const gaps = analysis.gaps || []
          const generatedCheckpoints = generateCheckpointsFallback(data, gaps, course)
          setCheckpoints(generatedCheckpoints)
        }
      } catch (error) {
        console.error('Failed to load problems:', error)
      }
      setLoading(false)
    }
    fetchData()
  }, [courseCode, analysis, user?.id])

  // Handle URL problem ID
  useEffect(() => {
    if (problemId && problems.length > 0) {
      const problem = problems.find(p => p.id === problemId)
      if (problem) {
        setPracticeProblem(problem)
        setActiveTab('exams')
      }
    }
  }, [problemId, problems])

  // Map API recommendations to checkpoints
  function mapRecommendationsToCheckpoints(recommendations, allProblems, gaps) {
    if (!recommendations || recommendations.length === 0) {
      return generateCheckpointsFallback(allProblems, gaps, course)
    }

    const topicProblems = {}
    allProblems.forEach(p => {
      if (!p.topic) return
      if (!topicProblems[p.topic]) topicProblems[p.topic] = []
      topicProblems[p.topic].push(p)
    })

    return recommendations.map((rec, index) => {
      const probs = topicProblems[rec.topic] || []
      const selectedProblems = probs.filter(p => rec.problemIds?.includes(p.id))
      const displayProblems = selectedProblems.length > 0
        ? selectedProblems.slice(0, 5)
        : probs.slice(0, 5)

      return {
        id: rec.id || `cp_${rec.topic}`,
        type: rec.type || 'exam_pattern',
        title: rec.title,
        subtitle: rec.subtitle || `${rec.problemCount} problems`,
        status: index === 0 ? 'recommended' : (rec.status || 'available'),
        reason: rec.reason || 'Personalized recommendation',
        problemIds: displayProblems.map(p => p.id),
        estimatedMinutes: Math.min(30, displayProblems.length * 8),
        problemCount: rec.problemCount || displayProblems.length,
        problems: displayProblems,
        weight: rec.weight || 0,
        pastExamSources: getExamSources(displayProblems.slice(0, 3)),
        isWeak: rec.type === 'prerequisite',
      }
    })
  }

  // Fallback checkpoint generation
  function generateCheckpointsFallback(allProblems, gaps, courseName) {
    const checkpoints = []
    const usedTopics = new Set()
    const distribution = TOPIC_DISTRIBUTION[courseName] || []

    const topicProblems = {}
    allProblems.forEach(p => {
      if (!p.topic) return
      if (!topicProblems[p.topic]) topicProblems[p.topic] = []
      topicProblems[p.topic].push(p)
    })

    for (const gap of gaps) {
      const taxonomyTopic = resolveToTopic(gap.skillGap, gap.taxonomyTopic)
      if (!taxonomyTopic || usedTopics.has(taxonomyTopic)) continue

      const probs = topicProblems[taxonomyTopic] || []
      if (probs.length === 0) continue

      checkpoints.push({
        id: `cp_gap_${taxonomyTopic}`,
        type: 'prerequisite',
        title: getTopicDisplayName(taxonomyTopic),
        subtitle: 'Needs practice',
        status: checkpoints.length === 0 ? 'recommended' : 'available',
        reason: 'Weakness identified in diagnostic',
        problemIds: probs.slice(0, 5).map(p => p.id),
        problemCount: probs.length,
        problems: probs.slice(0, 5),
        pastExamSources: getExamSources(probs.slice(0, 3)),
        isWeak: true,
      })
      usedTopics.add(taxonomyTopic)
    }

    const MAX_CHECKPOINTS = 5
    for (const distEntry of distribution) {
      if (checkpoints.length >= MAX_CHECKPOINTS) break
      if (usedTopics.has(distEntry.topic)) continue

      const probs = topicProblems[distEntry.topic] || []
      if (probs.length === 0) continue

      checkpoints.push({
        id: `cp_${distEntry.topic}`,
        type: 'exam_pattern',
        title: getTopicDisplayName(distEntry.topic),
        subtitle: `${probs.length} problems`,
        status: checkpoints.length === 0 ? 'recommended' : 'available',
        reason: 'High-frequency exam topic',
        problemIds: probs.slice(0, 5).map(p => p.id),
        problemCount: probs.length,
        problems: probs.slice(0, 5),
        pastExamSources: getExamSources(probs.slice(0, 3)),
        isWeak: false,
      })
      usedTopics.add(distEntry.topic)
    }

    return checkpoints
  }

  function getExamSources(probs) {
    const sources = []
    for (const p of probs) {
      if (p.exam) {
        const display = p.exam.replace(/_/g, ' ').replace(/(\d{2})$/, ' 20$1')
        sources.push(`${display} P${p.problem_number || '?'}`)
      }
    }
    return [...new Set(sources)].slice(0, 3)
  }

  // Get weak spots with practice predictions
  const weakSpots = (analysis.gaps || []).map((gap, i) => {
    const topic = resolveToTopic(gap.skillGap, gap.taxonomyTopic)
    return {
      skill: gap.skill || gap.name || 'Unknown',
      description: 'Still needs practice',
      relatedTopics: topic ? [topic] : [],
      practiceCount: 3 + (i % 3), // Placeholder: 3-5 problems prediction
    }
  })

  // First weak topic for motivation message
  const firstWeakTopic = weakSpots.length > 0 ? weakSpots[0].skill : null

  // Today's task
  const todayTask = checkpoints.length > 0 ? {
    topic: checkpoints[0].title,
    problemCount: Math.min(3, checkpoints[0].problemCount),
    problems: checkpoints[0].problems?.slice(0, 3) || [],
    isWeak: checkpoints[0].isWeak,
    hasReview: weakSpots.length > 0,
  } : null

  // Calculate mastery
  const distribution = TOPIC_DISTRIBUTION[course] || []
  const totalTopics = distribution.length || 30
  const masteredCount = Math.floor(totalTopics * 0.23) // Placeholder
  const masteryPercent = totalTopics > 0 ? Math.round((masteredCount / totalTopics) * 100) : 0

  const handleStartToday = () => {
    if (todayTask && todayTask.problems.length > 0) {
      setPracticeProblem(todayTask.problems[0])
      navigate(`/practice/${todayTask.problems[0].id}`)
    } else if (checkpoints.length > 0 && checkpoints[0].problems?.length > 0) {
      setPracticeProblem(checkpoints[0].problems[0])
      navigate(`/practice/${checkpoints[0].problems[0].id}`)
    }
  }

  const handleStartDiagnostic = () => {
    if (onBack) onBack()
  }

  const handlePracticeProblem = (problem) => {
    if (problem?.isNewExam || problem?.isResumeExam) {
      if (problems.length > 0) {
        const shuffled = [...problems].sort(() => Math.random() - 0.5)
        const examProblems = shuffled.slice(0, Math.min(8, shuffled.length))
        setExamMode({ name: 'Mock Exam', problems: examProblems })
      }
      return
    }
    setPracticeProblem(problem)
    navigate(`/practice/${problem.id}`)
  }

  // Handler for starting a real exam from MockExamsPage
  const handleStartExam = (exam) => {
    if (exam?.problems?.length > 0) {
      setExamMode({
        name: `Math 126 ${exam.displayName}`,
        problems: exam.problems,
        examId: exam.id,
      })
    }
  }

  const handleBackFromPractice = () => {
    setPracticeProblem(null)
    navigate('/dashboard')
  }

  const handlePracticeWeakSpot = (spot) => {
    const relatedProblems = problems.filter(p => spot.relatedTopics?.includes(p.topic))
    if (relatedProblems.length > 0) {
      handlePracticeProblem(relatedProblems[0])
    }
  }

  const handleViewLastSession = () => {
    console.log('View last session')
  }

  const handleViewWeekReview = () => {
    console.log('View week review')
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--claire-bg)]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--claire-green)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[var(--claire-text-secondary)] text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  // Exam mode
  if (examMode) {
    return (
      <MockExamView
        examName={examMode.name}
        problems={examMode.problems}
        onExit={() => setExamMode(null)}
        onSubmit={(result) => { console.log('Exam:', result); setExamMode(null) }}
      />
    )
  }

  return (
    <div className="min-h-screen bg-[var(--claire-bg)]">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} streak={streak} />

      <div className="pl-[72px]">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-[var(--claire-bg)]/90 backdrop-blur-sm border-b border-[var(--claire-border)]">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <button onClick={onBack} className="btn-link flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>

            <div className="flex items-center gap-4">
              <button className="btn-link text-xs">Upgrade</button>
              <div className="w-8 h-8 bg-[var(--claire-green)] rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {user?.email?.[0]?.toUpperCase() || 'G'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="max-w-5xl mx-auto px-6 py-8">
          {activeTab === 'learn' && (
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Left: Today's Task (Hero) */}
              <div className="flex-1 min-w-0">
                <TodayTaskCard
                  dailyMinutes={dailyMinutes}
                  task={todayTask}
                  hasDiagnostic={hasDiagnostic}
                  todayCompleted={todayCompleted}
                  todayStats={todayStats}
                  onStart={handleStartToday}
                  onStartDiagnostic={handleStartDiagnostic}
                  onExtraProblems={() => setActiveTab('exams')}
                  onViewLastSession={handleViewLastSession}
                  onViewWeekReview={handleViewWeekReview}
                  courseName={COURSE_NAMES[course]}
                  daysUntilExam={daysUntilExam}
                  streak={streak}
                  weakTopic={firstWeakTopic}
                />
              </div>

              {/* Right: Progress Overview */}
              <div className="w-full lg:w-72">
                <ProgressOverview
                  daysUntilExam={daysUntilExam}
                  examSource={examCountdown.source}
                  masteryPercent={masteryPercent}
                  masteredCount={masteredCount}
                  totalTopics={totalTopics}
                  weeklyGain={weeklyGain}
                  weakSpots={weakSpots}
                  streak={streak}
                  onViewWeakSpots={() => setActiveTab('weak')}
                  onPracticeWeakSpot={handlePracticeWeakSpot}
                />
              </div>
            </div>
          )}

          {activeTab === 'exams' && (
            practiceProblem ? (
              <ProblemPractice problem={practiceProblem} onBack={handleBackFromPractice} />
            ) : (
              <MockExamsPage onStartExam={handleStartExam} examCountdown={examCountdown} />
            )
          )}

          {activeTab === 'weak' && (
            <div className="max-w-2xl">
              <h2 className="text-2xl font-semibold text-[var(--claire-text-primary)] mb-2">
                Weak Spots
              </h2>
              <p className="text-[var(--claire-text-secondary)] mb-6">
                Master these to improve your score
              </p>
              {weakSpots.length === 0 ? (
                <div className="card-standard text-center py-10">
                  <p className="text-[var(--claire-text-secondary)]">
                    Complete the diagnostic to see weak spots
                  </p>
                  <button onClick={handleStartDiagnostic} className="btn-hero mt-6">
                    Start Diagnostic
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {weakSpots.map((spot, i) => (
                    <button
                      key={i}
                      onClick={() => handlePracticeWeakSpot(spot)}
                      className="weak-spot-item w-full text-left"
                    >
                      <div className="status-dot weak mt-1" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-[var(--claire-text-primary)]">
                          {spot.skill}
                        </h3>
                        <p className="prediction">
                          {spot.practiceCount} problems to master
                        </p>
                      </div>
                      <svg className="w-5 h-5 text-[var(--claire-text-muted)]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="max-w-md mx-auto text-center py-10">
              <div className="w-20 h-20 bg-[var(--claire-green)] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl font-semibold">
                  {user?.email?.[0]?.toUpperCase() || 'G'}
                </span>
              </div>
              <h2 className="text-xl font-semibold text-[var(--claire-text-primary)]">
                {user?.email || 'Guest'}
              </h2>
              <p className="text-[var(--claire-text-secondary)] mt-1">{COURSE_NAMES[course]}</p>

              <div className="mt-8 grid grid-cols-3 gap-3">
                <div className="card-subtle text-center py-4">
                  <div className="text-2xl font-semibold text-[var(--claire-text-primary)]">
                    {testState.answers?.length || 0}
                  </div>
                  <div className="text-xs text-[var(--claire-text-secondary)] mt-1">Diagnostic</div>
                </div>
                <div className="card-subtle text-center py-4">
                  <div className="text-2xl font-semibold text-[var(--claire-text-primary)]">
                    {problems.length}
                  </div>
                  <div className="text-xs text-[var(--claire-text-secondary)] mt-1">Problems</div>
                </div>
                <div className="card-subtle text-center py-4">
                  <div className="text-2xl font-semibold text-[var(--claire-fire)] flex items-center justify-center gap-1">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    </svg>
                    {streak}
                  </div>
                  <div className="text-xs text-[var(--claire-text-secondary)] mt-1">Streak</div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
