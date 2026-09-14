'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useAuth } from '@/hooks/useAuth'
import { useAnalyses } from '@/hooks/useAnalyses'
import NavUtilisateur from '@/components/NavUtilisateur'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import PageContainer from '@/components/PageContainer'
import MainContent from '@/components/MainContent'

const couleurs = {
  'low': '#00C49F',
  'medium': '#FFBB28',
  'high': '#FF8042',
  'critical': '#FF0000'
}
const niveaux = ['low', 'medium', 'high', 'critical']

export default function DashboardEmploye() {
  const { user, loading } = useAuth()
  const { analyses, loading: analysesLoading } = useAnalyses()
  const [dataParNiveau, setDataParNiveau] = useState([])

  useEffect(() => {
    if (!analyses || analyses.length === 0) {
      setDataParNiveau(niveaux.map(niveau => ({ niveau, analyses: 0 })))
      return
    }

    const counts = { 'low': 0, 'medium': 0, 'high': 0, 'critical': 0 }
    analyses.forEach((a) => {
      const niveau = (a.niveau_risque || a.risque || '').toLowerCase()
      if (counts[niveau] !== undefined) {
        counts[niveau] += 1
      }
    })
    
    const finalData = niveaux.map(niveau => ({
      niveau,
      analyses: counts[niveau]
    }))
    setDataParNiveau(finalData)
  }, [analyses])

  if (loading || analysesLoading) {
    return (
      <PageContainer>
        <NavUtilisateur />
        <LoadingSpinner message="Chargement du tableau de bord..." />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <NavUtilisateur />
      <MainContent>
        <PageHeader
          title="Tableau de bord"
          description="Vue d'ensemble de vos analyses par niveau de risque"
        />

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900">
            Nombre d&apos;analyses par niveau de risque
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dataParNiveau}>
              <XAxis dataKey="niveau" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="analyses">
                {dataParNiveau.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={couleurs[entry.niveau]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </MainContent>
    </PageContainer>
  )
} 