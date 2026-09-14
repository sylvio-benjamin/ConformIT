'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useAuth } from '@/hooks/useAuth'
import { analysesAPI } from '@/services/api'

const couleurs = {
  'low': '#00C49F',
  'medium-low': '#FFBB28',
  'high': '#FF8042',
  'critical': '#FF0000'
}

const niveaux = ['low', 'medium-low', 'high', 'critical']

export default function GraphiqueNiveauxRisque() {
  const { user } = useAuth()
  const [dataParNiveau, setDataParNiveau] = useState([])

  useEffect(() => {
    if (!user) return

    analysesAPI.listCompanies(user)
      .then((payload) => {
        const companies = payload.companies || []
        const counts = { 'low': 0, 'medium-low': 0, 'high': 0, 'critical': 0 }

        companies.forEach((ent) => {
          const niveau = (ent.risque || '').toLowerCase()
          if (counts[niveau] !== undefined) counts[niveau] += 1
        })

        setDataParNiveau(niveaux.map((niveau) => ({
          niveau,
          entreprises: counts[niveau],
        })))
      })
      .catch(() => setDataParNiveau(niveaux.map((niveau) => ({ niveau, entreprises: 0 }))))
  }, [user])

  return (
    <div className="bg-white p-4 rounded-xl shadow">
      <h2 className="text-lg font-semibold mb-2 text-center">Nombre d&apos;entreprises par niveau de risque</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={dataParNiveau}>
          <XAxis dataKey="niveau" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="entreprises">
            {dataParNiveau.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={couleurs[entry.niveau]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
