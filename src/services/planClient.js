'use client'

import { loadStripe } from '@stripe/stripe-js'
import { API_URL } from '@/lib/apiConfig'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '')

export async function startCheckoutSession({ priceId, planId, userId }) {
  if (!priceId) {
    throw new Error("Ce plan n'est pas disponible pour le paiement en ligne.")
  }
  if (!userId) {
    throw new Error('Utilisateur non connecté.')
  }

  await stripePromise

  const res = await fetch(`${API_URL}/create-checkout-session/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      plan_id: priceId,
      user_id: userId,
      plan: planId,
    }),
  })

  const data = await res.json()
  if (!res.ok || !data?.url) {
    throw new Error(data?.detail || data?.error || 'Impossible de lancer la session de paiement.')
  }

  window.location.href = data.url
}

export async function cancelCurrentSubscription(userId) {
  if (!userId) {
    throw new Error('Utilisateur non connecté.')
  }

  const res = await fetch(`${API_URL}/api/users/me/cancel-subscription`, {
    method: 'POST',
    credentials: 'include',
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || 'Impossible de résilier l’abonnement.')
  }
  return {
    abonnement: data.abonnement || 'basic',
    subscription_status: data.subscription_status || 'cancelled',
    cancelled_at: new Date().toISOString(),
  }
}
