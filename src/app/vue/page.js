'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { useAnalyses } from '@/hooks/useAnalyses'
import { analysesAPI, grcAPI } from '@/services/api'
import NavUtilisateur from '@/components/NavUtilisateur'
import PageContainer from '@/components/PageContainer'
import MainContent from '@/components/MainContent'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import StatCard from '@/components/StatCard'
import { labelRisque } from '@/lib/riskLabels'

export default function VueEnsemblePage() {
  const { user, loading } = useAuth()
  const { analyses, loading: analysesLoading } = useAnalyses()
  const [jobs, setJobs] = useState([])
  const [decisions, setDecisions] = useState([])
  const [evidence, setEvidence] = useState([])
  const [stats, setStats] = useState({})
  const [extraLoading, setExtraLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setExtraLoading(false)
      return
    }
    Promise.all([
      analysesAPI.listJobs().catch(() => ({ jobs: [] })),
      grcAPI.applicability.get().catch(() => ({ decisions: [] })),
      grcAPI.evidence.list().catch(() => ({ evidence: [] })),
      grcAPI.stats(user).catch(() => ({})),
    ])
      .then(([jobData, appl, ev, st]) => {
        setJobs(Array.isArray(jobData?.jobs) ? jobData.jobs : [])
        setDecisions(appl.decisions || [])
        setEvidence(ev.evidence || [])
        setStats(st || {})
      })
      .finally(() => setExtraLoading(false))
  }, [user])

  if (loading || !user || analysesLoading || extraLoading) {
    return (
      <PageContainer>
        <NavUtilisateur />
        <LoadingSpinner message="Chargement de la vue d’ensemble..." />
      </PageContainer>
    )
  }

  const running = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length
  const proposed = evidence.filter((item) => item.status === 'proposed').length
  const applicable = decisions.filter((item) => item.applicable).length
  const recent = [...analyses]
    .sort((a, b) => String(b.created_at || b.date || '').localeCompare(String(a.created_at || a.date || '')))
    .slice(0, 5)

  return (
    <PageContainer>
      <NavUtilisateur />
      <MainContent>
        <PageHeader
          title="Vue d’ensemble"
          description="Pilotage : analyses, preuves et conformité de votre organisation"
        />

        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard title="Analyses" value={analyses.length} color="blue" />
          <StatCard title="Jobs en cours" value={running} subtitle={`${jobs.length} au total`} color="orange" />
          <StatCard title="Preuves à valider" value={proposed} subtitle={`${evidence.length} au total`} color="red" />
          <StatCard title="Cadres applicables" value={applicable} subtitle={`${decisions.length} évalués`} color="blue" />
        </div>

        <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="rounded-xl bg-white p-6 shadow-md">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Analyses récentes</h2>
              <Link href="/analyses" className="text-sm font-medium text-[#003366]">
                Voir toutes →
              </Link>
            </div>
            {recent.length === 0 ? (
              <p className="text-sm text-gray-500">Aucune analyse. Déposez un document depuis Analyses.</p>
            ) : (
              <ul className="space-y-3">
                {recent.map((item) => (
                  <li key={item.slug || item.id} className="flex items-center justify-between gap-3 text-sm">
                    <Link
                      href={`/employe/entreprise?slug=${item.slug || item.id}`}
                      className="font-medium text-gray-900 hover:text-[#003366]"
                    >
                      {item.nom || item.nom_entreprise || item.slug || 'Document'}
                    </Link>
                    <span className="text-gray-500">{labelRisque(item.risque || item.niveau_risque)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-xl bg-white p-6 shadow-md">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Preuves proposées</h2>
              <Link href="/conformite" className="text-sm font-medium text-[#003366]">
                Valider →
              </Link>
            </div>
            {proposed === 0 ? (
              <p className="text-sm text-gray-500">
                Aucune preuve en attente. Les findings d’analyse alimentent la conformité après traitement.
              </p>
            ) : (
              <ul className="space-y-3">
                {evidence.filter((item) => item.status === 'proposed').slice(0, 5).map((item) => (
                  <li key={item.id} className="text-sm">
                    <p className="font-medium text-gray-900">{item.title}</p>
                    <p className="text-xs text-gray-500">
                      {(item.framework_code || '').toUpperCase()} · {item.severity || '—'}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <section className="rounded-xl bg-white p-6 shadow-md">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Conformité et risques</h2>
            <div className="flex gap-4 text-sm font-medium text-[#003366]">
              <Link href="/risques">Risques ({stats.totalRisks ?? 0})</Link>
              <Link href="/controles">Contrôles ({stats.totalControls ?? 0})</Link>
              <Link href="/conformite">Cadres applicables</Link>
            </div>
          </div>
          {decisions.length === 0 ? (
            <p className="text-sm text-gray-500">Complétez le profil d’organisation dans Conformité pour calculer l’applicabilité.</p>
          ) : (
            <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {decisions.map((item) => (
                <li key={item.framework_code} className="rounded-lg border border-gray-100 px-4 py-3 text-sm">
                  <p className="font-medium text-gray-900">{(item.framework_code || '').toUpperCase()}</p>
                  <p className={item.applicable ? 'text-green-700' : 'text-gray-500'}>
                    {item.applicable ? 'Applicable' : 'Hors périmètre'}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">{item.reason}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </MainContent>
    </PageContainer>
  )
}
