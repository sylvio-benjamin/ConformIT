'use client'

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer, Tooltip } from 'recharts'

/**
 * Graphique radar pour visualiser les performances multiformes (conformité, risque, actions)
 */
export default function ComplianceRadarChart({ data = {} }) {
  // Transformer les données pour le format attendu par Recharts
  const chartData = [
    { subject: 'Conformité', value: data.compliance || 0, fullMark: 100 },
    { subject: 'Risque', value: data.risk || 0, fullMark: 100 },
    { subject: 'Actions', value: data.actions || 0, fullMark: 100 },
    { subject: 'Contrôles', value: data.controls || 0, fullMark: 100 },
    { subject: 'Gaps', value: data.gaps || 0, fullMark: 100 },
    { subject: 'Performance', value: data.performance || 0, fullMark: 100 }
  ]

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis 
          angle={90} 
          domain={[0, 100]} 
          tick={{ fontSize: 10 }}
        />
        <Radar
          name="Performance GRC"
          dataKey="value"
          stroke="#003366"
          fill="#003366"
          fillOpacity={0.6}
        />
        <Tooltip
          formatter={(value) => [`${value}%`, 'Score']}
        />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  )
}
