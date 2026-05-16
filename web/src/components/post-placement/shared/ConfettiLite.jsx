import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const COLORS = ['#58cc02', '#1cb0f6', '#ff9600', '#ff4b4b', '#ce82ff', '#ffd900']

function ConfettiPiece({ delay, startX, color }) {
  const endX = startX + (Math.random() - 0.5) * 100
  const rotation = Math.random() * 720 - 360
  const size = 8 + Math.random() * 8

  return (
    <motion.div
      className="absolute rounded-sm"
      style={{
        width: size,
        height: size * 0.6,
        backgroundColor: color,
        left: startX,
        top: -20,
      }}
      initial={{ y: 0, x: 0, rotate: 0, opacity: 1 }}
      animate={{
        y: window.innerHeight + 50,
        x: endX - startX,
        rotate: rotation,
        opacity: [1, 1, 0],
      }}
      transition={{
        duration: 2 + Math.random() * 1,
        delay: delay,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
    />
  )
}

function ConfettiLite({ trigger = true, particleCount = 30 }) {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    if (trigger) {
      const newParticles = Array.from({ length: particleCount }, (_, i) => ({
        id: i,
        delay: Math.random() * 0.5,
        startX: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 400),
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      }))
      setParticles(newParticles)

      // Clean up after animation
      const timeout = setTimeout(() => {
        setParticles([])
      }, 4000)

      return () => clearTimeout(timeout)
    }
  }, [trigger, particleCount])

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      <AnimatePresence>
        {particles.map((p) => (
          <ConfettiPiece key={p.id} {...p} />
        ))}
      </AnimatePresence>
    </div>
  )
}

export default ConfettiLite
