'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, CreditCard, ReceiptText, Calendar, UserPlus, Users, Trash2, Copy, KeyRound, XOctagon } from 'lucide-react'
import NavUtilisateur from '@/components/NavUtilisateur'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'react-hot-toast'
import { usePlan } from '@/hooks/useQuota'
import { usersAPI } from '@/services/api'
import { SUBSCRIPTION_PLANS, BILLING_CYCLES } from '@/data/subscriptions'
import { cancelCurrentSubscription, startCheckoutSession } from '@/services/planClient'


export default function AbonnementsPage() {
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [isAnnual, setIsAnnual] = useState(false)
  const { user } = useAuth()
  const { plan: planInfo, loading: planLoading } = usePlan()

  const currentPlanId = planInfo?.plan || 'basic'
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const [collaborators, setCollaborators] = useState([])
  const [collaboratorEmail, setCollaboratorEmail] = useState('')
  const [collaboratorsLoading, setCollaboratorsLoading] = useState(false)

  const [apiKeyStatus, setApiKeyStatus] = useState({ hasKey: false, created_at: null })
  const [apiKeyLoading, setApiKeyLoading] = useState(false)
  const [newApiKey, setNewApiKey] = useState(null)

  useEffect(() => {
    if (!planLoading && currentPlanId) {
      setSelectedPlan(currentPlanId)
    }
  }, [planLoading, currentPlanId])

  useEffect(() => {
    if (!user?.uid || currentPlanId !== 'enterprise') {
      setCollaborators([])
      setCollaboratorsLoading(false)
      return
    }

    setCollaboratorsLoading(true)
    usersAPI.getCollaborators(user, user.uid)
      .then((data) => setCollaborators(data.collaborators || []))
      .catch(() => setCollaborators([]))
      .finally(() => setCollaboratorsLoading(false))
  }, [user, currentPlanId])

  const fetchApiKeyStatus = async () => {
    if (!user?.uid || currentPlanId !== 'enterprise') {
      setApiKeyStatus({ hasKey: false, created_at: null })
      return
    }

    setApiKeyLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api-keys/${user.uid}`, {
        credentials: 'include',
      })
      if (!res.ok) {
        throw new Error('Erreur lors de la récupération de la clé API')
      }
      const data = await res.json()
      setApiKeyStatus({ hasKey: data.has_key, created_at: data.created_at || null })
    } catch (error) {
      console.error('Erreur API key:', error)
      toast.error("Impossible de récupérer l'état de la clé API.")
    } finally {
      setApiKeyLoading(false)
    }
  }

  useEffect(() => {
    if (!user?.uid || currentPlanId !== 'enterprise') {
      setNewApiKey(null)
      setApiKeyStatus({ hasKey: false, created_at: null })
      return
    }

    fetchApiKeyStatus()
  }, [user, currentPlanId])

  const handleAddCollaborator = async () => {
    if (!user?.uid) return

    const email = collaboratorEmail.trim().toLowerCase()
    if (!email) {
      toast.error('Veuillez saisir une adresse e-mail.')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error('Adresse e-mail invalide.')
      return
    }

    if (collaborators.some((c) => c.email === email)) {
      toast.error('Ce collaborateur est déjà ajouté.')
      return
    }

    if (collaborators.length >= 2) {
      toast.error('Vous avez atteint la limite de collaborateurs (2).')
      return
    }

    try {
      const created = await usersAPI.addCollaborator(user, user.uid, email)
      setCollaborators((prev) => [...prev, created])
      toast.success('Collaborateur ajouté')
      setCollaboratorEmail('')
    } catch (error) {
      console.error('Erreur ajout collaborateur:', error)
      toast.error("Impossible d'ajouter le collaborateur.")
    }
  }

  const handleRemoveCollaborator = async (collaboratorId) => {
    if (!user?.uid) return
    try {
      await usersAPI.removeCollaborator(user, user.uid, collaboratorId)
      setCollaborators((prev) => prev.filter((c) => c.id !== collaboratorId))
      toast.success('Collaborateur supprimé')
    } catch (error) {
      console.error('Erreur suppression collaborateur:', error)
      toast.error('Impossible de supprimer ce collaborateur.')
    }
  }

  const handleGenerateApiKey = async () => {
    if (!user?.uid) return
    setApiKeyLoading(true)
    setNewApiKey(null)
    try {
      const res = await fetch(`${API_BASE}/api-keys/generate/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })

      if (!res.ok) {
        throw new Error('Erreur lors de la génération de la clé')
      }

      const data = await res.json()
      setNewApiKey(data.api_key)
      setApiKeyStatus({ hasKey: true, created_at: data.created_at })
      toast.success('Nouvelle clé API générée')
    } catch (error) {
      console.error('Erreur génération clé API:', error)
      toast.error('Impossible de générer la clé API.')
    } finally {
      setApiKeyLoading(false)
    }
  }

  const handleRevokeApiKey = async () => {
    if (!user?.uid) return
    setApiKeyLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api-keys/${user.uid}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      if (!res.ok) {
        throw new Error('Erreur lors de la révocation')
      }
      setNewApiKey(null)
      setApiKeyStatus({ hasKey: false, created_at: null })
      toast.success('Clé API révoquée')
    } catch (error) {
      console.error('Erreur révocation clé API:', error)
      toast.error('Impossible de révoquer la clé API.')
    } finally {
      setApiKeyLoading(false)
    }
  }

  const handleCopyApiKey = async () => {
    if (!newApiKey) {
      toast.error('Aucune clé à copier. Générez-en une nouvelle.')
      return
    }
    try {
      await navigator.clipboard.writeText(newApiKey)
      toast.success('Clé copiée dans le presse-papiers')
    } catch (error) {
      toast.error('Impossible de copier la clé.')
    }
  }


  const [cancelling, setCancelling] = useState(false)

  const handleStartCheckout = async (priceId, planId) => {
    if (!user?.uid) {
      toast.error('Utilisateur non connecté.')
      return
    }
    try {
      await startCheckoutSession({ priceId, planId, userId: user.uid })
    } catch (error) {
      console.error(error)
      toast.error(error.message || "Impossible de lancer le paiement.")
    }
  }

  const handleCancelSubscription = async () => {
    if (!user?.uid) return
    if (!confirm('Confirmez-vous la résiliation de votre abonnement ?')) return
    setCancelling(true)
    try {
      await cancelCurrentSubscription(user.uid)
      toast.success('Abonnement résilié. Vous êtes repassé sur le plan Basique.')
      setSelectedPlan('basic')
    } catch (error) {
      console.error(error)
      toast.error(error.message || 'Impossible de résilier votre abonnement.')
    } finally {
      setCancelling(false)
    }
  }


  return (
    <>
    < NavUtilisateur />
    <div className="min-h-screen bg-gray-50 py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-4">Choisissez votre formule</h1>
        <p className="text-center text-gray-500 mb-8">Trouvez le plan qui correspond à vos besoins</p>

        <div className="flex justify-center mb-8">
          <button
            onClick={() => setIsAnnual(false)}
            className={`px-4 py-2 rounded-l-lg border ${!isAnnual ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            Mensuel
          </button>
          <button
            onClick={() => setIsAnnual(true)}
            className={`px-4 py-2 rounded-r-lg border ${isAnnual ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            Annuel <span className="ml-1 text-xs bg-green-200 text-green-700 px-2 py-0.5 rounded">2 mois offerts</span>
          </button>
        </div>

        <div className="grid gap-8 grid-cols-1 md:grid-cols-3">
          {SUBSCRIPTION_PLANS.map(plan => {
            const isCurrent = plan.id === currentPlanId
            const isSelected = selectedPlan === plan.id
            const priceId = plan.pricing[isAnnual ? BILLING_CYCLES.ANNUALLY : BILLING_CYCLES.MONTHLY]?.stripePriceId
            const priceLabel = plan.pricing[isAnnual ? BILLING_CYCLES.ANNUALLY : BILLING_CYCLES.MONTHLY]?.label || '—'

            return (
            <div
              key={plan.id}
              className={`rounded-xl shadow-md p-6 border-2 transition-all duration-300 hover:shadow-xl ${
                isCurrent ? 'border-blue-600' : 'border-transparent'
              } ${isCurrent ? 'bg-blue-50/40' : 'cursor-pointer'}`}
              onClick={() => {
                if (!isCurrent) {
                  setSelectedPlan(plan.id)
                }
              }}
            >
              <div className="flex items-center gap-3 mb-2">
                <CreditCard className="text-blue-500" />
                <h2 className="text-2xl font-semibold text-gray-800">{plan.name}</h2>
              </div>
              {isCurrent && (
                <div className="inline-flex items-center gap-1 px-2 py-1 mb-3 text-xs font-semibold text-blue-700 bg-blue-100 rounded-full">
                  <CheckCircle size={14} className="text-blue-600" /> Plan actuel
                </div>
              )}
              <p className="text-sm text-gray-500 mb-4">{plan.description}</p>
              <p className="text-3xl font-bold text-blue-700 mb-6">
                {priceLabel}
              </p>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-gray-700">
                    <CheckCircle className="text-green-500" size={18} /> {feature}
                  </li>
                ))}
              </ul>

              {isSelected && (
              <div className="text-center">
                <button
                  onClick={() => {
                    if (!priceId) {
                      toast.error("Ce plan n'est pas encore disponible.")
                      return
                    }
                    handleStartCheckout(priceId, plan.id)
                  }}
                  disabled={isCurrent || !priceId}
                  className={`font-medium px-6 py-2 rounded-xl shadow transition ${
                    isCurrent || !priceId
                      ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >   
                {isCurrent ? 'Plan actuel' : "S'abonner"}
              </button>
                </div>
              )}
            </div>
          )})}
        </div>

        <div className="mt-10 text-center text-sm text-gray-500">
          <ReceiptText className="inline-block mr-1" />
          Tous les abonnements sont <strong>sans engagement</strong>. Résiliables à tout moment.
        </div>

        <div className="mt-6 max-w-2xl mx-auto text-center text-sm text-gray-600">
          {SUBSCRIPTION_PLANS.map(p =>
            selectedPlan === p.id ? (
              <p key={p.id}>
                <Calendar className="inline-block mr-1 mb-1" size={14} />
                <strong>Plan {p.id === currentPlanId ? 'actuel' : 'sélectionné'} :</strong>{' '}
                <span className="text-blue-700">{p.name}</span> – {p.pricing[isAnnual ? BILLING_CYCLES.ANNUALLY : BILLING_CYCLES.MONTHLY]?.label || '—'}
              </p>
            ) : null
          )}
        </div>

        {currentPlanId !== 'basic' && (
          <div className="mt-12 text-center">
            <button
              onClick={handleCancelSubscription}
              disabled={cancelling}
              className="inline-flex items-center gap-2 rounded-full border border-red-200 px-5 py-2 text-sm font-semibold text-red-600 transition hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <XOctagon size={16} />
              {cancelling ? 'Résiliation en cours…' : 'Résilier mon abonnement'}
            </button>
          </div>
        )}
      </div>
    </div>
    </>
  )
}
