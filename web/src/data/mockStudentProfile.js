/**
 * Mock Student Profile & Checkpoint Data
 *
 * Data structures designed for real backend integration:
 * - StudentProfile generates weakSpots, todayPlan, recommendedCheckpoints
 * - Checkpoint references real problem IDs from problems/*.json
 */

// Checkpoint types
export const CHECKPOINT_TYPES = {
  PREREQUISITE: 'prerequisite',
  CORE_SKILL: 'core_skill',
  EXAM_PATTERN: 'exam_pattern',
  MIXED_SET: 'mixed_set',
  BOSS: 'boss',
}

// Checkpoint statuses
export const CHECKPOINT_STATUS = {
  RECOMMENDED: 'recommended',   // Claire recommends starting here
  IN_PROGRESS: 'in_progress',   // Student has started
  COMPLETED: 'completed',       // Mastered
  AVAILABLE: 'available',       // Unlocked, ready to start
  LOCKED: 'locked',             // Prerequisites not met (deprecated - all unlocked now)
}

// Topic display names
export const TOPIC_DISPLAY = {
  limits: 'Limits',
  derivative_rules: 'Derivative Rules',
  curve_analysis: 'Curve Analysis',
  implicit_differentiation: 'Implicit Differentiation',
  linear_approximation: 'Linear Approximation',
  related_rates: 'Related Rates',
  optimization: 'Optimization',
  integration: 'Integration',
  double_integral: 'Double Integrals',
  polar_coordinates: 'Polar Coordinates',
  series: 'Series',
}

/**
 * Mock student profile - would come from backend based on diagnostic + history
 */
export const mockStudentProfile = {
  id: 'student_001',
  name: 'Demo Student',
  course: 'math124',
  examTarget: 'au24_final',
  goal: 'mastery',        // 'pass' | 'good' | 'mastery'
  daysUntilExam: 14,

  // From diagnostic analysis
  diagnosticResults: {
    tier1Passed: true,    // Foundation
    tier2Passed: true,    // Concept
    tier3Passed: false,   // UW Exam level
    tier4Passed: false,   // Elite
    skillLevel: '📈 Exam Ready',
    completedAt: new Date().toISOString(),
  },

  // Weak spots identified
  weakSpots: [
    {
      category: 'concept',
      skill: 'Linear approximation setup',
      description: 'You know derivatives but miss building L(x)',
      relatedTopics: ['linear_approximation'],
    },
    {
      category: 'algebra',
      skill: 'Chain rule with nested functions',
      description: 'Errors when functions are 3+ layers deep',
      relatedTopics: ['derivative_rules'],
    },
    {
      category: 'setup',
      skill: 'Related rates diagram',
      description: 'Drawing the relationship before differentiating',
      relatedTopics: ['related_rates'],
    },
  ],

  // Problem attempt history (would track real attempts)
  attemptHistory: {
    'uw_math_124_au24_p1': { status: 'completed', score: 1.0 },
    'uw_math_124_au24_p2': { status: 'attempted', score: 0.6 },
    'uw_math_124_au24_p5': { status: 'attempted', score: 0.3 },
  },
}

/**
 * Today's plan - generated from profile + time budget
 */
export const mockTodayPlan = [
  {
    id: 'plan_1',
    title: 'Fix linear approximation',
    duration: 20,
    checkpointId: 'cp_linear_approx',
    completed: false,
  },
  {
    id: 'plan_2',
    title: 'Do 2 related rates problems',
    duration: 15,
    checkpointId: 'cp_related_rates',
    completed: false,
  },
  {
    id: 'plan_3',
    title: 'Review yesterday\'s mistakes',
    duration: 10,
    checkpointId: null,
    completed: false,
  },
]

/**
 * Recommended checkpoints - personalized learning path
 * Each checkpoint references real problem IDs
 */
export const mockCheckpoints = [
  {
    id: 'cp_chain_rule_fix',
    type: CHECKPOINT_TYPES.PREREQUISITE,
    title: 'Chain Rule Foundations',
    subtitle: 'Fix nested function errors before harder problems',
    status: CHECKPOINT_STATUS.RECOMMENDED,
    tags: ['Fix first', 'Foundation gap'],

    // Why Claire recommends this
    reason: 'Your diagnostic showed errors on 3+ layer chain rule. This blocks linear approximation and related rates.',

    // Problems in this checkpoint (references to real IDs)
    problemIds: [
      'uw_math_124_au24_p2',  // derivative rules
      'uw_math_124_wi24_p2',
    ],

    estimatedMinutes: 15,
    problemCount: 2,

    // Past exam problems included
    pastExamSources: ['Autumn 2024 Final P2', 'Winter 2024 Final P2'],
  },
  {
    id: 'cp_linear_approx',
    type: CHECKPOINT_TYPES.CORE_SKILL,
    title: 'Linear Approximation',
    subtitle: 'Build L(x) and use it to estimate values',
    status: CHECKPOINT_STATUS.LOCKED,
    tags: ['High impact', 'Often tested'],

    reason: 'You got the derivative right on P5, but missed how to construct L(x) = f(a) + f\'(a)(x-a).',

    problemIds: [
      'uw_math_124_au24_p5',
      'uw_math_124_sp24_p4',
      'uw_math_124_wi23_p5',
    ],

    estimatedMinutes: 20,
    problemCount: 3,

    pastExamSources: ['Autumn 2024 P5', 'Spring 2024 P4', 'Winter 2023 P5'],
  },
  {
    id: 'cp_related_rates',
    type: CHECKPOINT_TYPES.EXAM_PATTERN,
    title: 'Related Rates',
    subtitle: 'Geometric setups + implicit differentiation',
    status: CHECKPOINT_STATUS.LOCKED,
    tags: ['Exam favorite', '12-13 pts'],

    reason: 'Related rates appears on 90% of finals. Your weak spot: drawing the diagram before solving.',

    problemIds: [
      'uw_math_124_au24_p6',
      'uw_math_124_sp24_p6',
      'uw_math_124_au23_p6',
    ],

    estimatedMinutes: 25,
    problemCount: 3,

    pastExamSources: ['Autumn 2024 P6', 'Spring 2024 P6', 'Autumn 2023 P6'],
  },
  {
    id: 'cp_mixed_practice',
    type: CHECKPOINT_TYPES.MIXED_SET,
    title: 'Mixed Past Paper Set',
    subtitle: '3 problems from recent finals',
    status: CHECKPOINT_STATUS.LOCKED,
    tags: ['Timed practice'],

    reason: 'After fixing core skills, practice under time pressure with mixed topics.',

    problemIds: [
      'uw_math_124_au24_p3',
      'uw_math_124_au24_p4',
      'uw_math_124_wi24_p7',
    ],

    estimatedMinutes: 30,
    problemCount: 3,

    pastExamSources: ['Autumn 2024 P3', 'Autumn 2024 P4', 'Winter 2024 P7'],
  },
  {
    id: 'cp_boss',
    type: CHECKPOINT_TYPES.BOSS,
    title: 'Full Curve Analysis',
    subtitle: 'The 18-point monster problem',
    status: CHECKPOINT_STATUS.LOCKED,
    tags: ['Boss', '18 pts'],

    reason: 'This is the hardest problem type on finals. Combines derivatives, critical points, concavity, and sketching.',

    problemIds: [
      'uw_math_124_au24_p8',
    ],

    estimatedMinutes: 25,
    problemCount: 1,

    pastExamSources: ['Autumn 2024 P8'],
  },
]

/**
 * Generate course header info
 */
export function getCourseHeader(profile) {
  const courseNames = {
    math124: 'Math 124',
    math125: 'Math 125',
    math126: 'Math 126',
  }

  const examTypes = {
    final: 'Final',
    midterm1: 'Midterm 1',
    midterm2: 'Midterm 2',
  }

  // Extract focus topics from weak spots
  const focusTopics = profile.weakSpots
    .flatMap(ws => ws.relatedTopics)
    .map(t => TOPIC_DISPLAY[t] || t)
    .slice(0, 3)

  return {
    courseName: courseNames[profile.course] || profile.course.toUpperCase(),
    examType: 'Final Prep',
    focusTopics,
    daysUntilExam: profile.daysUntilExam,
  }
}

/**
 * Get checkpoint icon based on type
 */
export function getCheckpointIcon(type) {
  const icons = {
    [CHECKPOINT_TYPES.PREREQUISITE]: '🔧',
    [CHECKPOINT_TYPES.CORE_SKILL]: '📘',
    [CHECKPOINT_TYPES.EXAM_PATTERN]: '📝',
    [CHECKPOINT_TYPES.MIXED_SET]: '🎯',
    [CHECKPOINT_TYPES.BOSS]: '👑',
  }
  return icons[type] || '📌'
}

/**
 * Get status color classes
 */
export function getStatusColors(status) {
  const colors = {
    [CHECKPOINT_STATUS.RECOMMENDED]: {
      bg: 'bg-blue-50',
      border: 'border-blue-400',
      dot: 'bg-blue-500',
      text: 'text-blue-700',
    },
    [CHECKPOINT_STATUS.IN_PROGRESS]: {
      bg: 'bg-amber-50',
      border: 'border-amber-400',
      dot: 'bg-amber-500',
      text: 'text-amber-700',
    },
    [CHECKPOINT_STATUS.COMPLETED]: {
      bg: 'bg-green-50',
      border: 'border-green-400',
      dot: 'bg-green-500',
      text: 'text-green-700',
    },
    [CHECKPOINT_STATUS.LOCKED]: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      dot: 'bg-gray-300',
      text: 'text-gray-400',
    },
  }
  return colors[status] || colors[CHECKPOINT_STATUS.LOCKED]
}
