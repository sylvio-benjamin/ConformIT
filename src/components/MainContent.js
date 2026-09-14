'use client'

/**
 * Container pour le contenu principal d'une page
 * Assure un espacement et une largeur maximale uniformes
 */
export default function MainContent({ children, className = '' }) {
  return (
    <main className={`mx-auto w-full max-w-7xl px-6 py-8 lg:px-8 ${className}`}>
      {children}
    </main>
  )
}

