'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function SuccessPage() {
  const router = useRouter()

  useEffect(() => {
    // Ici tu peux récupérer l'ID de session si besoin depuis l'URL
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session_id')

    console.log("✅ Paiement réussi - session :", sessionId)
    // Tu peux faire un fetch vers ton backend ici si besoin

    // Redirige vers la page d'abonnement
    router.push('/employe')
  }, [router], 3000)

  return (

    <div className="min-h-screen flex flex-col items-center justify-center text-center p-6">
      <h1 className="text-4xl font-bold text-green-600 mb-4">✅ Paiement réussi</h1>
      <p className="text-gray-700 text-lg mb-2">Merci pour votre abonnement !</p>
      <p className="text-gray-500 text-sm">Votre compte sera mis à jour automatiquement.</p>
    </div>
  )
}
