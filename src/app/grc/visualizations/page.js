'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { API_URL, getAuthHeaders } from '@/lib/apiConfig'
import { toast } from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Card from '@/components/Card'
import Button from '@/components/Button'
import { Download, Filter, RefreshCw, Calendar, FileCheck, TrendingUp } from 'lucide-react'

// Imports des composants de graphiques
import ComplianceSpeedometer from '@/components/grc/ComplianceSpeedometer'
import ComplianceBarChart from '@/components/grc/ComplianceBarChart'
import ComplianceLineChart from '@/components/grc/ComplianceLineChart'
import CompliancePieChart from '@/components/grc/CompliancePieChart'
import ComplianceHistogram from '@/components/grc/ComplianceHistogram'
import ComplianceRadarChart from '@/components/grc/ComplianceRadarChart'
import ComplianceRiskMatrix from '@/components/grc/ComplianceRiskMatrix'
import ComplianceHeatmap from '@/components/grc/ComplianceHeatmap'
import ComplianceGanttChart from '@/components/grc/ComplianceGanttChart'

export default function GRCVisualizationsPage() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('monthly')
  const [frameworkFilter, setFrameworkFilter] = useState('all')
  
  // États des données
  const [scores, setScores] = useState({ overall_score: 0, scores_by_framework: [] })
  const [evolution, setEvolution] = useState({})
  const [matrix, setMatrix] = useState({})
  const [heatmap, setHeatmap] = useState({ heatmap_data: [] })
  const [actions, setActions] = useState({ remediations: [], status_counts: {} })
  const [gaps, setGaps] = useState({ gaps: [], severity_counts: {} })
  const [frameworks, setFrameworks] = useState([])

  useEffect(() => {
    if (user?.uid) {
      fetchAllData()
    }
  }, [user?.uid, period, frameworkFilter])

  const fetchAllData = async () => {
    if (!user?.uid) return

    setLoading(true)
    try {
      const baseUrl = `${API_URL}/api/compliance`
      const authFetch = { credentials: 'include', headers: getAuthHeaders() }

      const [
        scoresRes,
        evolutionRes,
        matrixRes,
        heatmapRes,
        actionsRes,
        gapsRes,
        frameworksRes
      ] = await Promise.all([
        fetch(`${baseUrl}/dashboard/scores`, authFetch),
        fetch(`${baseUrl}/dashboard/evolution?period=${period}${frameworkFilter !== 'all' ? `&framework_id=${frameworkFilter}` : ''}`, authFetch),
        fetch(`${baseUrl}/dashboard/matrix`, authFetch),
        fetch(`${baseUrl}/dashboard/heatmap`, authFetch),
        fetch(`${baseUrl}/dashboard/actions`, authFetch),
        fetch(`${baseUrl}/dashboard/gaps${frameworkFilter !== 'all' ? `?framework_id=${frameworkFilter}` : ''}`, authFetch),
        fetch(`${baseUrl}/frameworks`, authFetch)
      ])

      if (scoresRes.ok) {
        const scoresData = await scoresRes.json()
        setScores(scoresData)
      }

      if (evolutionRes.ok) {
        const evolutionData = await evolutionRes.json()
        setEvolution(evolutionData.evolution || {})
      }

      if (matrixRes.ok) {
        const matrixData = await matrixRes.json()
        setMatrix(matrixData)
      }

      if (heatmapRes.ok) {
        const heatmapData = await heatmapRes.json()
        setHeatmap(heatmapData)
      }

      if (actionsRes.ok) {
        const actionsData = await actionsRes.json()
        setActions(actionsData)
      }

      if (gapsRes.ok) {
        const gapsData = await gapsRes.json()
        setGaps(gapsData)
      }

      if (frameworksRes.ok) {
        const frameworksData = await frameworksRes.json()
        setFrameworks(frameworksData)
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
      toast.error('Erreur lors du chargement des données')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = (format) => {
    // Fonction d'export (à implémenter avec des bibliothèques comme jsPDF, html2canvas, etc.)
    toast(`Export ${format} en cours de développement`, {
      icon: 'ℹ️',
    })
  }

  const handleRefresh = () => {
    fetchAllData()
    toast.success('Données actualisées')
  }

  // Préparer les données pour le graphique radar
  const radarData = {
    compliance: scores.overall_score,
    risk: matrix.risk_level || 0,
    actions: (actions.status_counts?.completed || 0) + (actions.status_counts?.in_progress || 0),
    controls: 0, // À récupérer depuis l'API controls si disponible
    gaps: gaps.total || 0,
    performance: scores.overall_score * 0.8 + (100 - (matrix.risk_level || 0)) * 0.2
  }

  if (loading) {
    return <LoadingSpinner message="Chargement des visualisations GRC..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Visualisations GRC"
        description="Graphiques et matrices pour analyser la conformité et les risques"
      />

      {/* Filtres et Actions */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-gray-500" />
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
          >
            <option value="daily">Quotidien</option>
            <option value="weekly">Hebdomadaire</option>
            <option value="monthly">Mensuel</option>
            <option value="quarterly">Trimestriel</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <FileCheck className="h-5 w-5 text-gray-500" />
          <select
            value={frameworkFilter}
            onChange={(e) => setFrameworkFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
          >
            <option value="all">Toutes les normes</option>
            {frameworks.map((fw) => (
              <option key={fw.id} value={fw.id}>
                {fw.name}
              </option>
            ))}
          </select>
        </div>

        <div className="ml-auto flex gap-2">
          <Button
            onClick={handleRefresh}
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="h-4 w-4" />}
          >
            Actualiser
          </Button>
          <div className="flex gap-2">
            <Button
              onClick={() => handleExport('pdf')}
              variant="secondary"
              size="sm"
              icon={<Download className="h-4 w-4" />}
            >
              PDF
            </Button>
            <Button
              onClick={() => handleExport('png')}
              variant="secondary"
              size="sm"
              icon={<Download className="h-4 w-4" />}
            >
              PNG
            </Button>
          </div>
        </div>
      </div>

      {/* Section 1: Score global de conformité */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Score global</h3>
          <ComplianceSpeedometer score={scores.overall_score} size={250} />
        </Card>
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Évolution du score</h3>
          <ComplianceLineChart data={evolution} period={period} />
        </Card>
      </div>

      {/* Section 2: Scores par norme */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scores par norme</h3>
          <ComplianceBarChart data={scores.scores_by_framework || []} />
        </Card>
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Répartition des normes</h3>
          <CompliancePieChart data={scores.scores_by_framework || []} />
        </Card>
      </div>

      {/* Section 3: Histogramme et Matrice */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Répartition des scores</h3>
          <ComplianceHistogram data={scores.scores_by_framework || []} />
        </Card>
        <Card>
          <ComplianceRiskMatrix data={matrix} />
        </Card>
      </div>

      {/* Section 4: Carte thermique */}
      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Carte thermique des normes</h3>
        <ComplianceHeatmap data={heatmap.heatmap_data || []} />
      </Card>

      {/* Section 5: Actions correctives */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions correctives (Gantt)</h3>
          <ComplianceGanttChart data={actions.remediations || []} />
        </Card>
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Statuts des actions</h3>
          <ComplianceBarChart
            data={Object.entries(actions.status_counts || {}).map(([status, count]) => ({
              framework_name: status,
              score: count,
              status: status
            }))}
          />
        </Card>
      </div>

      {/* Section 6: Graphique radar */}
      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance GRC (Radar)</h3>
        <ComplianceRadarChart data={radarData} />
      </Card>

      {/* Section 7: Écarts de conformité */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Écarts de conformité</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">Par sévérité</h4>
            <ComplianceBarChart
              data={Object.entries(gaps.severity_counts || {}).map(([severity, count]) => ({
                framework_name: severity,
                score: count,
                status: severity
              }))}
            />
          </div>
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">Par framework</h4>
            <ComplianceBarChart
              data={Object.entries(gaps.framework_gaps || {}).map(([framework, count]) => ({
                framework_name: framework,
                score: count,
                status: 'gap'
              }))}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}
