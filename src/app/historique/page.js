'use client'

import { useEffect, useState } from 'react'
import { Eye, Trash2, FileEdit, Building2 } from 'lucide-react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useAnalyses } from '@/hooks/useAnalyses'
import NavUtilisateur from '@/components/NavUtilisateur'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import RiskBadge from '@/components/RiskBadge'
import { toast } from 'react-hot-toast'
import PageContainer from '@/components/PageContainer'
import MainContent from '@/components/MainContent'
import Button from '@/components/Button'

export default function HistoriquePage() {
  const { user, loading } = useAuth()
  const { analyses: analysesData, loading: analysesLoading, deleteAnalysis } = useAnalyses()
  const [page, setPage] = useState(1)
  const pathname = usePathname()
  const router = useRouter()
  const analysesParPage = 10

  // Transformer et trier les données
  const analyses = analysesData
    .map(a => ({
      id: a.id || a.slug,
      slug: a.slug,
      nom: a.nom || a.nom_entreprise || '',
      nom_entreprise: a.nom_entreprise || a.nom || '',
      date: a.date || a.created_at || '',
      score: a.score || a.score_total || 0,
      risque: a.risque || a.niveau_risque || 'En attente',
      ...a
    }))
    .sort((a, b) => {
      const dateA = a.date || ''
      const dateB = b.date || ''
      return dateB.localeCompare(dateA)
    })

  const totalPages = Math.ceil(analyses.length / analysesParPage)
  const analysesPage = analyses.slice((page - 1) * analysesParPage, page * analysesParPage)

  const handleDelete = async (item) => {
    if (!window.confirm(`Supprimer l'analyse de ${item.nom_entreprise || item.nom || 'cette entreprise'} ?`)) {
      return
    }

    try {
      const slug = item.slug || item.id
      if (slug) {
        await deleteAnalysis(slug)
        toast.success('Analyse supprimée avec succès')
      } else {
        toast.error('Impossible de supprimer : slug manquant')
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  if (loading || analysesLoading) {
    return (
      <PageContainer>
        <NavUtilisateur />
        <LoadingSpinner message="Chargement de l'historique..." />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <NavUtilisateur />
      <MainContent>
        <PageHeader
          title="Historique des analyses"
          description="Consultation de l'historique complet de vos analyses"
        />

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entreprise
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  RCS
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risque
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysesPage.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    Aucune analyse trouvée
                  </td>
                </tr>
              ) : (
                analysesPage.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-900">
                          {a.nom_entreprise || a.nom || '—'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {a.rcs || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <RiskBadge risk={a.niveau_risque} score={a.score} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {a.date ? new Date(a.date).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                      <button
                        onClick={() => handleDelete(a)}
                        className="text-red-600 hover:text-red-800 transition"
                        title="Supprimer"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 px-6 py-4 border-t border-gray-200">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(p => p - 1)}
                disabled={page === 1}
              >
                Précédent
              </Button>
              <span className="text-sm text-gray-600">Page {page} / {totalPages}</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(p => p + 1)}
                disabled={page === totalPages}
              >
                Suivant
              </Button>
            </div>
          )}
        </div>
      </MainContent>
    </PageContainer>
  )
}
