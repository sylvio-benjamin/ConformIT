export const RISK_FILTERS = ['Tous', 'Faible', 'Modéré', 'Élevé', 'Critique']

const RISK_ALIASES = {
  low: 'Faible',
  faible: 'Faible',
  medium: 'Modéré',
  moyen: 'Modéré',
  modere: 'Modéré',
  modéré: 'Modéré',
  high: 'Élevé',
  eleve: 'Élevé',
  élevé: 'Élevé',
  critical: 'Critique',
  critique: 'Critique',
}

export function labelRisque(value) {
  if (!value) return '—'
  const key = String(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  return RISK_ALIASES[key] || RISK_ALIASES[String(value).toLowerCase()] || value
}

export function matchesRiskFilter(value, filtre) {
  if (!filtre || filtre === 'Tous') return true
  return labelRisque(value) === filtre
}
