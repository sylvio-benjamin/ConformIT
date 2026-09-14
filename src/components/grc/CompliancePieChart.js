'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

/**
 * Graphique en secteurs (camembert) pour la répartition des normes évaluées vs non évaluées
 */
export default function CompliancePieChart({ data = [] }) {
  // Compter les évaluées vs non évaluées
  const assessed = data.filter(item => item.status === 'assessed').length
  const notAssessed = data.filter(item => item.status === 'not_assessed').length

  const chartData = [
    { name: 'Évaluées', value: assessed, color: '#10B981' },
    { name: 'Non évaluées', value: notAssessed, color: '#E5E7EB' }
  ]

  const COLORS = ['#10B981', '#E5E7EB']

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

