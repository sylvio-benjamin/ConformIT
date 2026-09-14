'use client'

/**
 * Container principal pour toutes les pages
 * Assure un layout uniforme avec Navbar et Footer
 */
export default function PageContainer({ children, className = '' }) {
  return (
    <div className={`bg-gray-50 ${className}`}>
      {children}
    </div>
  )
}

