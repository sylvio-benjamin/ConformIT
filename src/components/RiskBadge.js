'use client'

import { labelRisque } from '@/lib/riskLabels'

export default function RiskBadge({ risk, score }) {
  const getRiskClass = (riskValue, scoreValue) => {
    const hasScore = scoreValue !== undefined && scoreValue !== null && scoreValue !== ''
    const score = Number(scoreValue) || 0

    if (hasScore) {
      if (score < 25) return 'bg-green-100 text-green-700'
      if (score < 50) return 'bg-yellow-100 text-yellow-700'
      if (score < 75) return 'bg-orange-200 text-orange-800'
      return 'bg-red-100 text-red-700'
    }

    const risk = (riskValue || '').toLowerCase()
    if (risk === 'critical' || risk === 'critique') return 'bg-purple-100 text-purple-700'
    if (risk === 'high' || risk === 'élevé' || risk === 'eleve') return 'bg-red-100 text-red-700'
    if (risk === 'medium' || risk === 'moyen' || risk === 'modéré' || risk === 'modere') {
      return 'bg-orange-100 text-orange-700'
    }
    if (risk === 'low' || risk === 'faible') return 'bg-green-100 text-green-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskClass(risk, score)}`}>
      {labelRisque(risk)}
    </span>
  )
}
