'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { API_URL, getAuthHeaders } from '@/lib/apiConfig'

export default function PageAttente() {
  const router = useRouter()
  const [annulee, setAnnulee] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const slug = localStorage.getItem('slug')

    if (!slug) {
      console.warn("Aucun slug trouvé dans localStorage")
      setError("Aucun slug trouvé. Veuillez recommencer l'analyse.")
      return
    }

    let interval = null
    let isMounted = true

    const verifierResultat = async () => {
      try {
        // Utiliser getAuthHeaders() pour inclure la clé API
        const res = await fetch(`${API_URL}/resultat/${slug}`, {
          method: 'GET',
          credentials: 'include',
        })

        // Gestion détaillée des erreurs HTTP
        if (!res.ok) {
          if (res.status === 401) {
            const errorText = await res.text()
            console.error('❌ Erreur 401 (Non autorisé):', errorText)
            setError("Erreur d'authentification. Vérifiez votre clé API.")
            clearInterval(interval)
            return
          } else if (res.status === 404) {
            // 404 est normal si l'analyse n'est pas encore terminée
            console.log(`⏳ Analyse en cours (${res.status})...`)
            return
          } else if (res.status >= 500) {
            console.error(`❌ Erreur serveur ${res.status}`)
            setError(`Erreur serveur (${res.status}). Réessayez plus tard.`)
            return
          } else {
            console.warn(`⚠️ Réponse HTTP ${res.status} — en attente...`)
            return
          }
        }

        // Parser la réponse JSON
        let data
        try {
          data = await res.json()
        } catch (parseError) {
          console.error('❌ Erreur parsing JSON:', parseError)
          setError("Réponse invalide du serveur.")
          return
        }

        if (!isMounted) return

        if (data.annulee === true) {
          clearInterval(interval)
          setAnnulee(true)
          return
        }

        if (data.analyseTerminee === true) {
          clearInterval(interval)
          router.replace('/employe/resultat-analyse')
        }
      } catch (err) {
        // Gestion détaillée des erreurs réseau
        if (err instanceof TypeError && err.message === 'Failed to fetch') {
          console.error('❌ Erreur réseau: Impossible de contacter le serveur')
          console.error('   Vérifiez que le backend est démarré sur', API_URL)
          setError(`Impossible de contacter le serveur (${API_URL}). Vérifiez que le backend est démarré.`)
        } else if (err.name === 'NetworkError' || err.message.includes('network')) {
          console.error('❌ Erreur réseau:', err.message)
          setError('Erreur de connexion réseau. Vérifiez votre connexion internet.')
        } else {
          console.error('❌ Erreur inattendue:', err)
          setError(`Erreur: ${err.message || 'Erreur inconnue'}`)
        }
      }
    }

    // Vérification immédiate
    verifierResultat()
    interval = setInterval(verifierResultat, 3000)

    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [router])

  const handleCancel = async () => {
    const slug = localStorage.getItem('slug')

    if (slug) {
      try {
        const res = await fetch(`${API_URL}/annuler-analyse/${slug}`, {
          method: 'POST',
          headers: getAuthHeaders(),
          mode: 'cors',
        })
        
        if (res.ok) {
          console.log("✅ Analyse annulée côté serveur.")
          setAnnulee(true)
        } else {
          console.error(`❌ Erreur lors de l'annulation: ${res.status}`)
        }
      } catch (err) {
        console.error("❌ Erreur réseau lors de l'annulation:", err)
      }
    }
  }

  if (annulee) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-center px-4">
        <h1 className="text-3xl font-bold text-red-600 mb-4">Analyse annulée</h1>
        <p className="text-gray-600 mb-6">L&apos;analyse a été interrompue par l&apos;utilisateur.</p>
        <button
          onClick={() => router.push('/analyses')}
          className="text-blue-600 underline"
        >
          Retour aux analyses
        </button>
      </div>
    )
  }

  // Afficher l'erreur si elle existe
  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-center px-4">
        <h1 className="text-3xl font-bold text-red-600 mb-4">Erreur de connexion</h1>
        <p className="text-gray-600 mb-6">{error}</p>
        <div className="space-y-4">
          <button
            onClick={() => {
              setError(null)
              window.location.reload()
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Réessayer
          </button>
          <button
            onClick={() => router.push('/analyses')}
            className="block text-blue-600 underline mt-4"
          >
            Retour à l&apos;accueil
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-center px-4">
      <h1 className="text-3xl font-bold text-gray-800 mb-4">Chargement de l&apos;analyse en cours...</h1>
      <p className="text-gray-600 mb-6">
        Votre document est en cours d&apos;analyse. Veuillez patienter quelques instants.
      </p>

      <div className="w-12 h-12 border-4 border-blue-500 border-dashed rounded-full animate-spin"></div>

      <p className="mt-8 text-sm text-gray-500">
        Si rien ne se passe,&nbsp;
        <button
          onClick={handleCancel}
          className="text-blue-600 hover:underline"
        >
          annulez et retournez à l&apos;accueil
        </button>.
      </p>
    </div>
  )
}
