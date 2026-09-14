'use client'

import { useEffect, useState } from 'react'
import { Eye, Building2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { analysesAPI } from '@/services/api'
import NavUtilisateur from '@/components/NavUtilisateur'
import PageContainer from '@/components/PageContainer'
import MainContent from '@/components/MainContent'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import DataTable from '@/components/DataTable'

export default function ListeEntreprisesPage() {
  const [entreprises, setEntreprises] = useState([])
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!user) return

    analysesAPI.listCompanies(user)
      .then((data) => {
        const liste = (data.companies || []).map((val) => ({
          id: val.id || val.slug,
          nom: val.nom || 'Sans nom',
          rcs: val.rcs || 'Pas de RCS',
        }))
        setEntreprises(liste)
      })
      .catch(() => setEntreprises([]))
  }, [user])

  if (loading || !user) {
    return (
      <PageContainer>
        <NavUtilisateur />
        <LoadingSpinner message="Chargement des entreprises..." />
      </PageContainer>
    )
  }

  const headers = ['Nom', 'RCS', 'Actions']
  const rows = entreprises.map((e) => [
    <div key="nom" className="flex items-center gap-2">
      <Building2 className="h-5 w-5 text-blue-500" />
      <span className="text-sm font-medium text-gray-900">{e.nom}</span>
    </div>,
    <span key="rcs" className="text-sm text-gray-500">{e.rcs}</span>,
    <button
      key="actions"
      onClick={() => router.push(`/employe/entreprise-graph?slug=${encodeURIComponent(e.nom)}`)}
      title="Voir l'évolution"
      className="text-blue-600 hover:text-blue-800 transition"
    >
      <Eye className="h-5 w-5" />
    </button>,
  ])

  return (
    <PageContainer>
      <NavUtilisateur />
      <MainContent>
        <PageHeader
          title="Liste des entreprises analysées"
          description="Consultation de toutes les entreprises analysées"
        />
        <DataTable
          headers={headers}
          rows={rows}
          emptyMessage="Aucune entreprise trouvée"
        />
      </MainContent>
    </PageContainer>
  )
}
