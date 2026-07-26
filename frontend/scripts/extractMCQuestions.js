/**
 * Extract Multiple Choice Questions from UW Problem Bank
 *
 * This script processes the JSON problem files and extracts questions
 * that are in multiple choice format, converting them to the diagnostic format.
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const problemsDir = path.join(__dirname, '../../problems')
const outputFile = path.join(__dirname, '../src/data/uwQuestionBank.js')

// Patterns to detect multiple choice options
const MC_PATTERNS = [
  /\(i\)\s*(.+?)\s*\(ii\)\s*(.+?)\s*\(iii\)\s*(.+?)\s*\(iv\)\s*(.+?)(?:\(v\)|$)/s,
  /\(A\)\s*(.+?)\s*\(B\)\s*(.+?)\s*\(C\)\s*(.+?)\s*\(D\)\s*(.+?)(?:\(E\)|$)/s,
  /\(a\)\s*(.+?)\s*\(b\)\s*(.+?)\s*\(c\)\s*(.+?)\s*\(d\)\s*(.+?)(?:\(e\)|$)/s,
]

// Topic to tier mapping based on difficulty
const TOPIC_TIER_MAP = {
  // Tier 1: Foundation / Pre-calc / Basic
  'algebraic_manipulation': 1,
  'basic_limits': 1,
  'vectors_basic': 1,
  'vector_operations': 1,
  'dot_product': 1,
  'spheres': 1,
  'basic_derivatives': 1,

  // Tier 2: Conceptual Understanding
  'limits': 2,
  'derivative_interpretation': 2,
  'partial_derivatives': 2,
  'projections': 2,
  'unit_vectors': 2,
  'lines': 2,
  'planes': 2,

  // Tier 3: UW Exam Level
  'vectors_and_geometry': 3,
  'derivative_rules': 3,
  'chain_rule': 3,
  'integration_techniques': 3,
  'double_integrals': 3,
  'vector_valued_functions': 3,
  'taylor_polynomials_and_series': 3,
  'fundamental_theorem_of_calculus': 3,
  'applications_of_integration': 3,

  // Tier 4: Elite / 4.0 Separator
  'optimization': 4,
  'multivariable_optimization': 4,
  'lagrange_multipliers': 4,
  'implicit_differentiation': 4,
  'curve_analysis': 4,
  'constrained_optimization': 4,
}

// Get tier from topic
function getTierFromTopic(topic, concepts = []) {
  const normalizedTopic = topic.toLowerCase().replace(/\s+/g, '_')

  if (TOPIC_TIER_MAP[normalizedTopic]) {
    return TOPIC_TIER_MAP[normalizedTopic]
  }

  // Check concepts
  for (const concept of concepts) {
    const normalizedConcept = concept.toLowerCase().replace(/\s+/g, '_')
    if (TOPIC_TIER_MAP[normalizedConcept]) {
      return TOPIC_TIER_MAP[normalizedConcept]
    }
  }

  // Default to Tier 3 (UW Exam level)
  return 3
}

// Extract course name from filename
function getCourseFromFilename(filename) {
  if (filename.includes('math124')) return 'math124'
  if (filename.includes('math125')) return 'math125'
  if (filename.includes('math126')) return 'math126'
  return 'math126'
}

// Parse multiple choice options from question text
function parseMCOptions(questionText) {
  for (const pattern of MC_PATTERNS) {
    const match = questionText.match(pattern)
    if (match) {
      // Extract options and the question stem
      const options = [match[1], match[2], match[3], match[4]].map(opt => opt.trim())
      const stem = questionText.replace(pattern, '').trim()
      return { stem, options }
    }
  }
  return null
}

// Find correct answer index from final_answer
function findCorrectIndex(options, finalAnswer) {
  if (!finalAnswer) return 0

  const normalizedAnswer = finalAnswer.replace(/\$/g, '').trim().toLowerCase()

  for (let i = 0; i < options.length; i++) {
    const normalizedOption = options[i].replace(/\$/g, '').trim().toLowerCase()
    if (normalizedOption === normalizedAnswer ||
        normalizedOption.includes(normalizedAnswer) ||
        normalizedAnswer.includes(normalizedOption)) {
      return i
    }
  }

  // Default to first option if not found
  return 0
}

// Process a single problem
function processProblem(problem, course, filename) {
  const mcQuestions = []

  const parts = problem.parts || []

  for (const part of parts) {
    const questionText = part.question_text
    if (!questionText) continue

    const parsed = parseMCOptions(questionText)
    if (!parsed) continue

    const tier = getTierFromTopic(problem.topic, problem.concepts || [])
    const correctIndex = findCorrectIndex(parsed.options, part.final_answer)

    // Generate unique ID
    const examInfo = problem.exam || filename.replace('.json', '')
    const partLabel = part.label ? `_${part.label}` : ''
    const id = `uw_${course}_${examInfo}_p${problem.problem_number}${partLabel}`

    mcQuestions.push({
      id,
      tier,
      topic: problem.topic.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      skill: (problem.concepts && problem.concepts[0])
        ? problem.concepts[0].replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
        : problem.topic.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      question: parsed.stem,
      options: parsed.options,
      correct: correctIndex,
      explanation: `The correct answer is ${parsed.options[correctIndex]}`,
      skillGap: problem.topic.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      source: `UW ${course.toUpperCase()} ${examInfo.replace(/_/g, ' ')}`,
    })
  }

  return mcQuestions
}

// Main extraction function
function extractAllMCQuestions() {
  const allQuestions = {
    math124: [],
    math125: [],
    math126: [],
  }

  const files = fs.readdirSync(problemsDir).filter(f => f.endsWith('.json'))

  for (const filename of files) {
    const filepath = path.join(problemsDir, filename)
    const content = fs.readFileSync(filepath, 'utf-8')

    try {
      const problems = JSON.parse(content)
      const course = getCourseFromFilename(filename)

      for (const problem of problems) {
        const mcQuestions = processProblem(problem, course, filename)
        allQuestions[course].push(...mcQuestions)
      }
    } catch (e) {
      console.error(`Error processing ${filename}:`, e.message)
    }
  }

  return allQuestions
}

// Generate output file
function generateOutputFile(questions) {
  const output = `/**
 * UW Problem Bank - Multiple Choice Questions
 * Auto-generated from /problems/*.json
 * Generated: ${new Date().toISOString()}
 *
 * These are real UW Math exam questions extracted and converted for the diagnostic system.
 */

export const UW_QUESTION_BANK = ${JSON.stringify(questions, null, 2)}

// Get questions by course, optionally filtered by tier
export function getQuestionsByCourse(course, tier = null) {
  const questions = UW_QUESTION_BANK[course] || UW_QUESTION_BANK.math126
  if (tier === null) return questions
  return questions.filter(q => q.tier === tier)
}

// Get a balanced set of questions (one per tier)
export function getBalancedQuestionSet(course) {
  const questions = UW_QUESTION_BANK[course] || UW_QUESTION_BANK.math126
  const result = []

  for (let tier = 1; tier <= 4; tier++) {
    const tierQuestions = questions.filter(q => q.tier === tier)
    if (tierQuestions.length > 0) {
      // Random selection from available questions
      const randomIndex = Math.floor(Math.random() * tierQuestions.length)
      result.push(tierQuestions[randomIndex])
    }
  }

  return result
}

export default UW_QUESTION_BANK
`

  fs.writeFileSync(outputFile, output)
  console.log(`Generated ${outputFile}`)

  // Print stats
  console.log('\nQuestion counts:')
  for (const [course, qs] of Object.entries(questions)) {
    console.log(`  ${course}: ${qs.length} MC questions`)
    const byTier = {}
    for (const q of qs) {
      byTier[q.tier] = (byTier[q.tier] || 0) + 1
    }
    for (const [tier, count] of Object.entries(byTier).sort()) {
      console.log(`    Tier ${tier}: ${count}`)
    }
  }
}

// Run extraction
const questions = extractAllMCQuestions()
generateOutputFile(questions)
