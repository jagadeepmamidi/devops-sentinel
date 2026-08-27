import { motion, useReducedMotion } from 'motion/react'

const MotionDiv = motion.div

export default function Reveal({ children, className = '', delay = 0 }) {
  const reduce = useReducedMotion()
  if (reduce) {
    return <div className={className}>{children}</div>
  }
  return (
    <MotionDiv
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-12% 0px' }}
      transition={{ type: 'spring', stiffness: 100, damping: 20, delay }}
    >
      {children}
    </MotionDiv>
  )
}
