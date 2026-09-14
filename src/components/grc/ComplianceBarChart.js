'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'

/**
 * Graphique en barres pour afficher les scores de conformité par norme
 */
export default function ComplianceBarChart({ data = [] }) {
  // Couleurs personnalisées selon le score
  const getColor = (score) => {
    if (score >= 80) return '#10B981' // Vert
    if (score >= 50) return '#F59E0B' // Orange
    return '#EF4444' // Rouge
  }

  const chartData = data.map(item => ({
    name: item.framework_name || item.framework_code || 'Unknown',
    score: item.score || 0,
    status: item.status || 'not_assessed'
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <XAxis
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          domain={[0, 100]}
          label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          formatter={(value) => [`${value}%`, 'Score']}
          labelStyle={{ fontWeight: 'bold' }}
        />
        <Legend />
        <Bar dataKey="score" name="Score de conformité" radius={[8, 8, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

