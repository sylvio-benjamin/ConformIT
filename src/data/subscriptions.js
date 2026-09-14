'use client'

export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  ANNUALLY: 'annually',
}

export const SUBSCRIPTION_PLANS = [
  {
    id: 'basic',
    name: 'Basique',
    description: 'Parfait pour commencer et tester les analyses.',
    pricing: {
      [BILLING_CYCLES.MONTHLY]: {
        label: 'Gratuit',
        stripePriceId: null,
      },
      [BILLING_CYCLES.ANNUALLY]: {
        label: 'Gratuit',
        stripePriceId: null,
      },
    },
    features: [
      '5 analyses / mois',
      'Support par mail',
      'Accès aux rapports PDF',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'Idéal pour les professionnels avec un volume régulier.',
    pricing: {
      [BILLING_CYCLES.MONTHLY]: {
        label: '29€/mois',
        stripePriceId: 'price_1Rc3SrRoX6cVFKbCgYeQOlRB',
      },
      [BILLING_CYCLES.ANNUALLY]: {
        label: '290€/an (2 mois offerts)',
        stripePriceId: 'price_1Rc3SrRoX6cVFKbCzoGZPRgj',
      },
    },
    features: [
      '50 analyses / mois',
      'Support prioritaire',
      'Export Excel + PDF',
      'Alertes en temps réel',
    ],
  },
  {
    id: 'enterprise',
    name: 'Business',
    description: 'Pensé pour les équipes et les gros volumes.',
    pricing: {
      [BILLING_CYCLES.MONTHLY]: {
        label: '59€/mois',
        stripePriceId: 'price_1Rc3TaRoX6cVFKbCsZnt4paC',
      },
      [BILLING_CYCLES.ANNUALLY]: {
        label: '590€/an (2 mois offerts)',
        stripePriceId: 'price_1Rc3U4RoX6cVFKbCYNYIDQ6s',
      },
    },
    features: [
      'Analyses illimitées',
      '1 compte principal + 2 collaborateurs',
      'Support client réactif',
      'Export Excel et PDF',
      'Accès API privée',
    ],
  },
]

export function getPlanById(planId) {
  return SUBSCRIPTION_PLANS.find(plan => plan.id === planId)
}

