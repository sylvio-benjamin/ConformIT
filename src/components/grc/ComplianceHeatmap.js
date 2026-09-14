'use client'

/**
 * Carte thermique (Heatmap) pour visualiser les normes par niveau de conformité
 */
export default function ComplianceHeatmap({ data = [] }) {
  // Couleurs selon le score
  const getColor = (score) => {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-green-300'
    if (score >= 40) return 'bg-yellow-300'
    if (score >= 20) return 'bg-orange-300'
    return 'bg-red-500'
  }

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Bon'
    if (score >= 40) return 'Moyen'
    if (score >= 20) return 'Faible'
    return 'Critique'
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.map((item) => (
        <div
          key={item.framework_id || item.framework_code}
          className={`${getColor(item.score || 0)} rounded-lg p-6 text-white shadow-lg transition-transform hover:scale-105`}
        >
          <h3 className="text-lg font-bold mb-2">{item.framework_name || item.framework_code}</h3>
          <div className="text-3xl font-bold mb-1">{Math.round(item.score || 0)}%</div>
          <div className="text-sm opacity-90">{getScoreLabel(item.score || 0)}</div>
          {item.status === 'not_assessed' && (
            <div className="mt-2 text-xs opacity-75 italic">Non évalué</div>
          )}
        </div>
      ))}
      
      {data.length === 0 && (
        <div className="col-span-full text-center text-gray-500 py-8">
          Aucune donnée de conformité disponible
        </div>
      )}
    </div>
  )
}

