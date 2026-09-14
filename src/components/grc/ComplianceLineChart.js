'use client'

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts'

/**
 * Graphique en courbes pour afficher l'évolution des scores de conformité
 */
export default function ComplianceLineChart({ data = [], period = 'monthly' }) {
  // Transformer les données pour le format attendu par Recharts
  // data doit être un objet avec framework_id comme clés
  const frameworks = Object.keys(data)
  
  if (frameworks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Aucune donnée disponible
      </div>
    )
  }

  // Créer un ensemble de toutes les périodes uniques
  const allPeriods = new Set()
  frameworks.forEach(fwId => {
    if (data[fwId] && Array.isArray(data[fwId])) {
      data[fwId].forEach(item => allPeriods.add(item.period))
    }
  })

  const sortedPeriods = Array.from(allPeriods).sort()

  // Transformer en format pour Recharts
  const chartData = sortedPeriods.map(period => {
    const entry = { period }
    frameworks.forEach(fwId => {
      const frameworkData = data[fwId] || []
      const periodData = frameworkData.find(d => d.period === period)
      entry[fwId] = periodData ? periodData.score : null
    })
    return entry
  })

  // Couleurs pour les différentes lignes
  const colors = ['#003366', '#00A859', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          domain={[0, 100]}
          label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          formatter={(value) => value !== null ? `${value}%` : 'N/A'}
          labelStyle={{ fontWeight: 'bold' }}
        />
        <Legend />
        {frameworks.map((fwId, index) => (
          <Line
            key={fwId}
            type="monotone"
            dataKey={fwId}
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name={`Framework ${fwId.slice(0, 8)}`}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

