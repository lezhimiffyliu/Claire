import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'

const departments = ['CSE', 'MATH', 'ENGR', 'PHYS', 'AMATH', 'CHEM']

function SocialProofBar() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section
      ref={ref}
      className="bg-gray-50 border-y border-gray-100 py-8 overflow-hidden"
    >
      <motion.div
        className="max-w-6xl mx-auto px-4"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
      >
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8">
          <p className="text-gray-500 font-medium text-center">
            Trusted by UW students in
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            {departments.map((dept, index) => (
              <motion.div
                key={dept}
                className="px-4 py-2 bg-white rounded-full border border-gray-200 shadow-sm"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={isInView ? { opacity: 1, scale: 1 } : {}}
                transition={{ delay: index * 0.1, duration: 0.3 }}
              >
                <span className="font-bold text-gray-700">{dept}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Stats row */}
        <motion.div
          className="mt-8 grid grid-cols-3 gap-4 max-w-md mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="text-center">
            <div className="text-2xl md:text-3xl font-extrabold text-[#58cc02]">1,000+</div>
            <div className="text-xs md:text-sm text-gray-500">Students</div>
          </div>
          <div className="text-center">
            <div className="text-2xl md:text-3xl font-extrabold text-[#1cb0f6]">4.8★</div>
            <div className="text-xs md:text-sm text-gray-500">Rating</div>
          </div>
          <div className="text-center">
            <div className="text-2xl md:text-3xl font-extrabold text-[#ff9600]">89%</div>
            <div className="text-xs md:text-sm text-gray-500">Pass Rate↑</div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  )
}

export default SocialProofBar
