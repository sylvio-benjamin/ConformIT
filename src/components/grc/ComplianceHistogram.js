'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, CartesianGrid } from 'recharts'

/**
 * Histogramme pour afficher la répartition des scores de conformité par norme
 */
export default function ComplianceHistogram({ data = [] }) {
  // Grouper les scores par plages
  const scoreRanges = [
    { range: '0-20', min: 0, max: 20, color: '#EF4444' },
    { range: '21-40', min: 21, max: 40, color: '#F97316' },
    { range: '41-60', min: 41, max: 60, color: '#F59E0B' },
    { range: '61-80', min: 61, max: 80, color: '#10B981' },
    { range: '81-100', min: 81, max: 100, color: '#059669' }
  ]

  // Compter les scores par plage
  const distribution = scoreRanges.map(range => {
    const count = data.filter(item => {
      const score = item.score || 0
      return score >= range.min && score <= range.max
    }).length
    return {
      range: range.range,
      count: count,
      color: range.color
    }
  })

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={distribution} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="range" 
          label={{ value: 'Plage de scores (%)', position: 'insideBottom', offset: -5 }}
        />
        <YAxis 
          label={{ value: 'Nombre de normes', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          formatter={(value) => [`${value} norme(s)`, 'Nombre']}
          labelStyle={{ fontWeight: 'bold' }}
        />
        <Legend />
        <Bar dataKey="count" name="Nombre de normes" radius={[8, 8, 0, 0]}>
          {distribution.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
