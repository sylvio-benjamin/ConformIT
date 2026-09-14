'use client'

/**
 * Matrice de conformité/risque : Croiser le niveau de conformité avec le niveau de risque
 */
export default function ComplianceRiskMatrix({ data }) {
  const { compliance_score = 0, risk_level = 0 } = data || {}

  // Déterminer la zone dans la matrice
  const getZone = (compliance, risk) => {
    if (compliance >= 80 && risk <= 30) return { zone: 'Optimal', color: 'bg-green-100 border-green-500' }
    if (compliance >= 60 && risk <= 50) return { zone: 'Acceptable', color: 'bg-blue-100 border-blue-500' }
    if (compliance >= 40 && risk <= 70) return { zone: 'Attention', color: 'bg-yellow-100 border-yellow-500' }
    return { zone: 'Critique', color: 'bg-red-100 border-red-500' }
  }

  const zone = getZone(compliance_score, risk_level)

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Matrice Conformité / Risque</h3>
      
      {/* Matrice visuelle */}
      <div className="relative h-64 mb-4 bg-gray-50 rounded-lg border-2 border-gray-300">
        {/* Axes */}
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gray-400"></div>
        <div className="absolute bottom-0 left-0 w-1 h-full bg-gray-400"></div>
        
        {/* Labels des axes */}
        <div className="absolute -bottom-6 left-0 text-xs text-gray-600">Conformité 0%</div>
        <div className="absolute -bottom-6 right-0 text-xs text-gray-600">Conformité 100%</div>
        <div className="absolute -left-12 top-0 text-xs text-gray-600 transform -rotate-90 origin-center">
          Risque 100%
        </div>
        <div className="absolute -left-12 bottom-0 text-xs text-gray-600 transform -rotate-90 origin-center">
          Risque 0%
        </div>
        
        {/* Point actuel */}
        <div
          className="absolute w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg transform -translate-x-1/2 -translate-y-1/2 z-10"
          style={{
            left: `${compliance_score}%`,
            bottom: `${risk_level}%`
          }}
        >
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-xs font-semibold text-blue-600 whitespace-nowrap">
            Position actuelle
          </div>
        </div>
        
        {/* Zones */}
        <div className="absolute top-0 left-0 w-1/2 h-1/2 bg-green-100 opacity-30 rounded-tl-lg"></div>
        <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-yellow-100 opacity-30 rounded-tr-lg"></div>
        <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-blue-100 opacity-30 rounded-bl-lg"></div>
        <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-red-100 opacity-30 rounded-br-lg"></div>
      </div>
      
      {/* Métriques */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">{Math.round(compliance_score)}%</div>
          <div className="text-sm text-gray-600">Score de conformité</div>
        </div>
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">{Math.round(risk_level)}%</div>
          <div className="text-sm text-gray-600">Niveau de risque</div>
        </div>
      </div>
      
      {/* Zone actuelle */}
      <div className={`mt-4 p-4 rounded-lg border-2 ${zone.color}`}>
        <div className="font-semibold text-gray-900">Zone: {zone.zone}</div>
        <div className="text-sm text-gray-600 mt-1">
          {zone.zone === 'Optimal' && 'Votre organisation est dans une zone optimale avec une conformité élevée et des risques faibles.'}
          {zone.zone === 'Acceptable' && 'Votre organisation présente une situation acceptable. Surveillez les tendances.'}
          {zone.zone === 'Attention' && 'Une attention particulière est requise. Des actions correctives sont recommandées.'}
          {zone.zone === 'Critique' && 'Situation critique. Des actions immédiates sont nécessaires pour améliorer la conformité et réduire les risques.'}
        </div>
      </div>
    </div>
  )
}

