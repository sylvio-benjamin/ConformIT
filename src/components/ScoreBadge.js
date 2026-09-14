'use client'

export default function ScoreBadge({ score, riskColor }) {
  const getScoreClass = (scoreValue, riskColorValue) => {
    if (riskColorValue) {
      const colorMap = {
        green: 'bg-green-100 text-green-700',
        orange: 'bg-yellow-100 text-yellow-700',
        'orange-dark': 'bg-orange-200 text-orange-800',
        red: 'bg-red-100 text-red-700',
      }
      if (colorMap[riskColorValue]) {
        return colorMap[riskColorValue]
      }
    }

    const value = Number(scoreValue) || 0
    if (value <= 30) return 'bg-green-100 text-green-700'
    if (value <= 60) return 'bg-yellow-100 text-yellow-700'
    if (value <= 80) return 'bg-orange-200 text-orange-800'
    return 'bg-red-100 text-red-700'
  }

  const scoreValue = Number(score) || 0

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getScoreClass(score, riskColor)}`}>
      {scoreValue}/100
    </span>
  )
}

