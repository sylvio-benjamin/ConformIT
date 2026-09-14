'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { analysesAPI } from '@/services/api'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
)

import NavUtilisateur from '@/components/NavUtilisateur'

export default function EntrepriseEvolutionPage() {
  const { user } = useAuth()
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)
  const searchParams = useSearchParams()
  const slug = searchParams.get('slug') // slug = nom exact de l'entreprise

  useEffect(() => {
    if (!slug || !user) return

    analysesAPI.list(user)
      .then((data) => {
        const allData = data.analyses || []
        const filtered = allData
          .filter((item) => {
            const nom = (item.nom_entreprise || item.nom || '').toLowerCase()
            return nom === slug.toLowerCase()
          })
          .sort((a, b) => new Date(a.date) - new Date(b.date))

        const labels = filtered.map((item) =>
          new Date(item.date).toLocaleDateString('fr-FR')
        )
        const scores = filtered.map((item) => Number(item.score_total) || 0)

        setChartData({
          labels,
          datasets: [
            {
              label: 'Score total',
              data: scores,
              borderColor: '#4f46e5',
              tension: 0.4,
              fill: false,
            },
          ],
        })
      })
      .catch(() => setChartData(null))
      .finally(() => setLoading(false))
  }, [slug, user])

  return (
    <>
    <NavUtilisateur />
    <div className="p-6 flex justify-center">
      <Card className="w-full max-w-4xl shadow-xl">
        <CardHeader>
          <CardTitle className="text-xl text-center">
          Évolution du score de l&apos;entreprise : {slug?.toUpperCase()}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-gray-500 text-center">Chargement des données...</p>
          ) : !chartData || chartData.labels.length === 0 ? (
            <p className="text-center text-gray-500">Aucune donnée disponible.</p>
          ) : (
            <Line
              data={chartData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    display: true,
                    position: 'bottom',
                  },
                },
              }}
            />
          )}
        </CardContent>
      </Card>
    </div>
    </>
  )
}
