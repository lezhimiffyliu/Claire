import { useRef } from 'react'
import StickyHeader from './StickyHeader'
import HeroSection from './HeroSection'
import FeatureSection, {
  DiagnosticVisual,
  ProblemCardsVisual,
  FeedbackVisual,
  RoadmapVisual,
} from './FeatureSection'
import CTAFooter from './CTAFooter'

const features = [
  {
    id: 'diagnostic',
    title: '5-Minute Diagnostic',
    description:
      'Find your weak spots fast—tailored for UW Math 124/125/126. No guessing what to study.',
    visual: DiagnosticVisual,
  },
  {
    id: 'roadmap',
    title: 'Your Cram Roadmap',
    description:
      'See what to study next. Topics ordered by prerequisite so you build knowledge efficiently.',
    visual: RoadmapVisual,
  },
  {
    id: 'past-papers',
    title: '760+ Real UW Exam Problems',
    description:
      '86 past exams from Math 124/125/126. Practice what actually shows up on your test.',
    visual: ProblemCardsVisual,
  },
  {
    id: 'feedback',
    title: 'AI Reads Your Handwriting',
    description:
      'Upload your handwritten solution. Claire finds the exact mistake and guides you forward.',
    visual: FeedbackVisual,
  },
]

function LandingPage({ onGetStarted }) {
  const heroRef = useRef(null)

  return (
    <div className="relative bg-[var(--claire-bg)]">
      <StickyHeader onGetStarted={onGetStarted} heroRef={heroRef} />

      <div ref={heroRef}>
        <HeroSection onGetStarted={onGetStarted} />
      </div>

      {/* Subtle divider */}
      <div className="h-px bg-[var(--claire-gray-200)]" />

      {features.map((feature, index) => (
        <FeatureSection
          key={feature.id}
          {...feature}
          reversed={index % 2 === 1}
        />
      ))}

      <CTAFooter onGetStarted={onGetStarted} />
    </div>
  )
}

export default LandingPage
