'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function CancelledPage() {
  const router = useRouter()

  useEffect(() => {
    router.push('/employe/profile') // Redirection immédiate
  }, [router], 3000)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center p-6">
      <h1 className="text-4xl font-bold text-red-600 mb-4">❌ Paiement annulé</h1>
      <p className="text-gray-700 text-lg mb-2">Redirection en cours vers votre profil...</p>
    </div>
  )
}
