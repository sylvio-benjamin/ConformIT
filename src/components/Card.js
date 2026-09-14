'use client'

export default function Card({ children, className = '', hover = false, ...props }) {
  return (
    <div
      className={`bg-white rounded-xl shadow-md p-6 ${hover ? 'hover:shadow-lg transition' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

