/**
 * UW Problem Bank - Multiple Choice Questions
 * Auto-generated from /problems/*.json
 * Generated: 2026-04-25T01:14:06.167Z
 *
 * These are real UW Math exam questions extracted and converted for the diagnostic system.
 */

export const UW_QUESTION_BANK = {
  "math124": [
    {
      "id": "uw_math124_sp23_final_p1_c",
      "tier": 2,
      "topic": "Limits",
      "skill": "One Sided Limits",
      "question": "Determine if the following are True or False. Circle the correct answer.\n\n If $f'(x) = \\frac{3x^2 + e^x}{\\cos x}$, then $f(x) = \\frac{x^3 + e^x}{\\sin x}$.\n\nTrue    False",
      "options": [
        "If $\\lim_{x \\to 3} f(x) = 5$ and $\\lim_{x \\to 3} g(x) = 0$, then $\\lim_{x \\to 3} \\frac{f(x)}{g(x)} = \\infty$.\n\nTrue    False",
        "If $\\lim_{x \\to a} f(x) = \\lim_{x \\to a} g(x)$, then $\\lim_{x \\to a} f'(x) = \\lim_{x \\to a} g'(x)$.\n\nTrue    False",
        "If $f'(x) = g'(x)$ for all $x$, then $f(x) = g(x)$ for all $x$.\n\nTrue    False",
        "If $\\lim_{x \\to 4^+} f(x) = \\infty$, then $x = 4$ is a vertical asymptote for the graph $y = f(x)$.\n\nTrue    False"
      ],
      "correct": 0,
      "explanation": "The correct answer is If $\\lim_{x \\to 3} f(x) = 5$ and $\\lim_{x \\to 3} g(x) = 0$, then $\\lim_{x \\to 3} \\frac{f(x)}{g(x)} = \\infty$.\n\nTrue    False",
      "skillGap": "Limits",
      "source": "UW MATH124 sp23 final"
    }
  ],
  "math125": [
    {
      "id": "uw_math125_sp20_final_p7",
      "tier": 3,
      "topic": "Fundamental Theorem Of Calculus",
      "skill": "Derivative Of Integral Function",
      "question": "Circle the correct ones, and cross out the incorrect ones. For the ones that you crossed out, show which of the conditions it fails to satisfy: $\\frac{dy}{dx} = e^{x^2}$, $f(1) = 2$, or both.\n\n $y = \\frac{1}{2x} e^{x^2} - \\frac{1}{2}e + 2$",
      "options": [
        "$y = \\int_1^x e^t dt$",
        "$y = \\int_1^x e^t dt + 2$",
        "$y = \\int_1^{x^2} e^t dt$",
        "$y = \\int_1^x (e^{t^2} + 2) dt$"
      ],
      "correct": 0,
      "explanation": "The correct answer is $y = \\int_1^x e^t dt$",
      "skillGap": "Fundamental Theorem Of Calculus",
      "source": "UW MATH125 sp20 final"
    },
    {
      "id": "uw_math125_wi24_final_p6_c",
      "tier": 3,
      "topic": "Applications Of Integration",
      "skill": "Average Value Of A Function",
      "question": "$(2 \\text{ points}) \\text{The Trapezoidal Rule approximation } T_3 \\text{ of } \\int_{-2}^{0} f(x) dx \\text{ is (circle one)}: \\\\ \\text{(i) an underestimate} \\quad \\text{or} \\quad \\text{(ii) an overestimate} \\\\ \\text{because the function is (circle one)}: \\\\ \\text{ concave up} \\quad \\text{(f) concave down}$",
      "options": [
        "positive} \\quad \\text{",
        "negative} \\quad \\text{",
        "increasing} \\quad \\text{",
        "decreasing} \\quad \\text{"
      ],
      "correct": 0,
      "explanation": "The correct answer is positive} \\quad \\text{",
      "skillGap": "Applications Of Integration",
      "source": "UW MATH125 wi24 final"
    }
  ],
  "math126": [
    {
      "id": "uw_math126_math126_Sp18_p1_a",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Suppose $\\mathbf{a} \\neq \\mathbf{0}$ and $\\text{proj}_{\\mathbf{a}}\\mathbf{b} = \\mathbf{a} \\times \\mathbf{b}$. Then...",
      "options": [
        "$\\mathbf{b} = \\mathbf{a}$.",
        "$\\mathbf{b} = -\\mathbf{a}$.",
        "$\\mathbf{b} = \\mathbf{0}$.",
        "$\\mathbf{b}$ is orthogonal to $\\mathbf{a}$, but $\\mathbf{b} \\neq \\mathbf{0}$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $\\mathbf{b} = \\mathbf{a}$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Sp18"
    },
    {
      "id": "uw_math126_math126_Sp18_p1_b",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Let $\\mathcal{P}$ be the plane through $(0,0,0)$, $(1,1,2)$, and $(2,0,0)$. Then $\\mathcal{P}$ also contains...",
      "options": [
        "$(1,2,4)$.",
        "$(1,4,2)$.",
        "$(2,1,4)$.",
        "$(2,4,1)$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $(1,2,4)$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Sp18"
    },
    {
      "id": "uw_math126_math126_Sp18_p1_c",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Let $\\ell$ be the line $\\mathbf{r}(t) = \\langle 4t, 2t, 2+t \\rangle$ and let $\\mathcal{P}$ be the plane $x - 3y + 2z = 4$. Then $\\ell$ is...",
      "options": [
        "parallel to $\\mathcal{P}$.",
        "orthogonal to $\\mathcal{P}$.",
        "contained in $\\mathcal{P}$.",
        "none of these."
      ],
      "correct": 0,
      "explanation": "The correct answer is parallel to $\\mathcal{P}$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Sp18"
    },
    {
      "id": "uw_math126_math126_Sp18_p1_d",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Suppose $S$ is the set of points $P$ such that the distance from $P$ to the $z$-axis is 1. Then $S$ is...",
      "options": [
        "two planes.",
        "a cone.",
        "a circular paraboloid.",
        "a cylinder."
      ],
      "correct": 0,
      "explanation": "The correct answer is two planes.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Sp18"
    },
    {
      "id": "uw_math126_math126_Sp18_p1_e",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Let $\\mathbf{T}(t)$ be the unit tangent vector for $\\mathbf{r}(t)$, and suppose $|\\mathbf{r}'(0)| = \\frac{1}{2}$. Then...",
      "options": [
        "$\\mathbf{T}(0) = 2\\mathbf{r}'(0)$.",
        "$\\mathbf{T}(0) = \\frac{1}{2}\\mathbf{r}'(0)$.",
        "$\\mathbf{T}(0) = \\mathbf{r}'(0)$.",
        "$\\mathbf{T}(0) = \\mathbf{0}$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $\\mathbf{T}(0) = 2\\mathbf{r}'(0)$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Sp18"
    },
    {
      "id": "uw_math126_spr2025_final_p1_a",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Spheres",
      "question": "What is the radius of the sphere through $(-1, 2, 0)$ with center $(0, 0, 2)$?",
      "options": [
        "$\\sqrt{2}$",
        "$3$",
        "$4$",
        "$\\sqrt{5}$"
      ],
      "correct": 1,
      "explanation": "The correct answer is $3$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 spr2025 final"
    },
    {
      "id": "uw_math126_spr2025_final_p1_b",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Spheres",
      "question": "If $\\text{proj}_{\\mathbf{a}} \\mathbf{b} = \\langle 1, 2, 3 \\rangle$, what's $\\text{proj}_{(2,4,6)} \\mathbf{b}$?",
      "options": [
        "$\\langle 1, 2, 3 \\rangle$",
        "$\\langle 2, 4, 6 \\rangle$",
        "$\\langle 3, 6, 9 \\rangle$",
        "$(\\sqrt{2}, 2\\sqrt{2}, 3\\sqrt{2})$"
      ],
      "correct": 0,
      "explanation": "The correct answer is $\\langle 1, 2, 3 \\rangle$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 spr2025 final"
    },
    {
      "id": "uw_math126_spr2025_final_p1_c",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Spheres",
      "question": "If $\\mathbf{a}$ and $\\mathbf{b}$ are unit vectors, which of the following cannot equal $\\mathbf{a} \\times \\mathbf{b}$?",
      "options": [
        "$\\langle 0, 0, 0 \\rangle$",
        "$\\langle 0, 1, 0 \\rangle$",
        "$\\langle 1, 0, 1 \\rangle$",
        "$(\\frac{1}{2}, \\frac{1}{2}, \\frac{1}{2})$"
      ],
      "correct": 0,
      "explanation": "The correct answer is $\\langle 0, 0, 0 \\rangle$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 spr2025 final"
    },
    {
      "id": "uw_math126_spr2025_final_p1_d",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Spheres",
      "question": "Which point lies on the line through $(1, 2, 3)$ and $(2, 0, 1)$?",
      "options": [
        "$(-1, 5, 7)$",
        "$(0, 4, 5)$",
        "$(2, 1, 2)$",
        "$(3, -2, 5)$"
      ],
      "correct": 1,
      "explanation": "The correct answer is $(0, 4, 5)$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 spr2025 final"
    },
    {
      "id": "uw_math126_spr2025_final_p1_e",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Spheres",
      "question": "Which of the following planes is parallel to the line $\\mathbf{r}(t) = \\langle t, 2t, 3t \\rangle$?",
      "options": [
        "$x + y + z = 6$",
        "$x + 2y + 3z = 1$",
        "$2x - y + z = 4$",
        "$x + y - z = 7$"
      ],
      "correct": 3,
      "explanation": "The correct answer is $x + y - z = 7$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 spr2025 final"
    },
    {
      "id": "uw_math126_math126_Wi22_p1_a",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Suppose $|\\mathbf{a} \\times \\mathbf{b}| > -\\mathbf{a} \\cdot \\mathbf{b} > 0$. Then the angle between $\\mathbf{a}$ and $\\mathbf{b}$ is between...",
      "options": [
        "$0°$ and $45°$.",
        "$45°$ and $90°$.",
        "$90°$ and $135°$.",
        "$135°$ and $180°$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $0°$ and $45°$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi22"
    },
    {
      "id": "uw_math126_math126_Wi22_p1_b",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Suppose $\\text{proj}_{\\mathbf{a}}\\mathbf{b} = \\langle 1, -1, 1 \\rangle$. Then $\\mathbf{b}$ could be...",
      "options": [
        "$\\langle 2, -2, 2 \\rangle$.",
        "$\\langle -1, 1, -1 \\rangle$.",
        "$\\langle 2, 2, 2 \\rangle$.",
        "$\\langle 2, 3, 4 \\rangle$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $\\langle 2, -2, 2 \\rangle$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi22"
    },
    {
      "id": "uw_math126_math126_Wi22_p1_c",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "The intersection of the hyperboloid $x^2 + y^2 - z^2 = 1$ and the $xy$-plane is...",
      "options": [
        "a line.",
        "a circle.",
        "a hyperbola.",
        "the empty set."
      ],
      "correct": 0,
      "explanation": "The correct answer is a line.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi22"
    },
    {
      "id": "uw_math126_math126_Wi22_p1_d",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "The surface $z = f(x, y) = x^3 + y^3 - 3x - 3y$ has a local maximum of...",
      "options": [
        "$f(1, 1)$.",
        "$f(1, -1)$.",
        "$f(-1, 1)$.",
        "$f(-1, -1)$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $f(1, 1)$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi22"
    },
    {
      "id": "uw_math126_math126_Wi22_p1_e",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "A lamina occupies the disc $x^2 + y^2 \\le 1$, and the density at $(x, y)$ is $\\rho(x, y) = x^3 + y^2 + 2$. The center of mass of the lamina is...",
      "options": [
        "at the origin.",
        "on the $x$-axis.",
        "on the $y$-axis.",
        "none of these."
      ],
      "correct": 0,
      "explanation": "The correct answer is at the origin.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi22"
    },
    {
      "id": "uw_math126_math126_Wi25_p1_a",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "If $|\\mathbf{b}| = -2 \\text{comp}_{\\mathbf{a}}\\mathbf{b}$, then what's the angle between $\\mathbf{a}$ and $\\mathbf{b}$?",
      "options": [
        "$30°$",
        "$60°$",
        "$120°$",
        "$150°$"
      ],
      "correct": 2,
      "explanation": "The correct answer is $120°$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi25"
    },
    {
      "id": "uw_math126_math126_Wi25_p1_b",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Suppose $\\overrightarrow{AB} \\times \\overrightarrow{AC} = \\langle 2, -1, 2 \\rangle$. What's the area of $\\triangle ABC$?",
      "options": [
        "$1$",
        "$1.5$",
        "$2$",
        "$3$"
      ],
      "correct": 0,
      "explanation": "The correct answer is $1$",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi25"
    },
    {
      "id": "uw_math126_math126_Wi25_p1_c",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "Which of the following points is on the line $\\mathbf{r}(t) = \\langle 2 - t, t, -1 + 2t \\rangle$?",
      "options": [
        "$(1, 1, 1)$.",
        "$(1, 1, 0)$.",
        "$(-1, 1, 2)$.",
        "$(2, 1, 1)$."
      ],
      "correct": 0,
      "explanation": "The correct answer is $(1, 1, 1)$.",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi25"
    },
    {
      "id": "uw_math126_math126_Wi25_p1_d",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "What's the intersection between the planes $2x - y + 3z = 3$ and $4x - 2y + 6z = 5$?",
      "options": [
        "a point",
        "a line",
        "a plane",
        "nothing"
      ],
      "correct": 3,
      "explanation": "The correct answer is nothing",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi25"
    },
    {
      "id": "uw_math126_math126_Wi25_p1_e",
      "tier": 2,
      "topic": "Vectors And Geometry",
      "skill": "Dot Product",
      "question": "What is the trace (cross section) of the surface $x^2 - 2x - y^2 + z^2 = 0$ in the plane $z = 1$?",
      "options": [
        "a parabola",
        "a circle",
        "a hyperbola",
        "two lines"
      ],
      "correct": 3,
      "explanation": "The correct answer is two lines",
      "skillGap": "Vectors And Geometry",
      "source": "UW MATH126 math126 Wi25"
    }
  ]
}

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
