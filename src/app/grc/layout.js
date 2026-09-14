'use client'

import NavUtilisateur from '@/components/NavUtilisateur'

export default function GRCLayout({ children }) {
  return (
    <div className="bg-gray-50">
      <NavUtilisateur />
      <div className="mx-auto w-full max-w-7xl">
        {children}
      </div>
    </div>
  )
}
