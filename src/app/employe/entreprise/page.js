'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { API_URL, getAuthHeaders } from '@/lib/apiConfig'
import RiskBadge from '@/components/RiskBadge'
import ScoreBreakdown from '@/components/ScoreBreakdown'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import NavUtilisateur from '@/components/NavUtilisateur'
import { grcAPI } from '@/services/api'

const API_BASE = API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function VisionnageAnalysePage() {
  const searchParams = useSearchParams()
  const slugParam = searchParams.get('slug')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [evidence, setEvidence] = useState([])

  const slug = useMemo(() => {
    if (typeof window === 'undefined') return slugParam
    if (slugParam) {
      localStorage.setItem('slug', slugParam)
      return slugParam
    }
    return localStorage.getItem('slug')
  }, [slugParam])

  useEffect(() => {
    if (!slug) {
      setLoading(false)
      setError("Aucun identifiant d'analyse fourni.")
      return
    }

    const controller = new AbortController()

    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/resultat/${slug}`, {
          headers: getAuthHeaders(),
          signal: controller.signal,
          mode: 'cors',
        })

        if (!res.ok) {
          throw new Error(`Erreur serveur (${res.status})`)
        }

        const json = await res.json()
        if (!json || Object.keys(json).length === 0) {
          throw new Error("Analyse introuvable.")
        }
        setData(json)
        setError(null)
        grcAPI.evidence.list().then((payload) => {
          const rows = payload.evidence || []
          const related = rows.filter((item) => {
            const hay = `${item.title || ''} ${item.detail || ''} ${item.source_slug || ''} ${item.analysis_slug || ''}`
            return slug && hay.toLowerCase().includes(String(slug).toLowerCase())
          })
          setEvidence(related.length ? related : rows.filter((item) => item.status === 'proposed').slice(0, 5))
        }).catch(() => setEvidence([]))
      } catch (err) {
        if (err.name === 'AbortError') return
        console.error('Erreur récupération analyse:', err)
        setError(err.message || "Échec de récupération de l'analyse.")
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    return () => controller.abort()
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <LoadingSpinner message="Chargement de l'analyse en cours..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <div className="flex flex-col justify-center items-center min-h-screen gap-3 text-red-600">
          <p>{error}</p>
          <button
            onClick={() => typeof window !== 'undefined' && window.history.back()}
            className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 transition"
          >
            Retour
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="p-6 text-red-500 text-center">Aucune analyse trouvée.</div>
          </div>
        </div>
      </div>
    )
  }

  const risque = data.niveau_risque || data.risque
  const details = data.details || []
  const reponses = data.reponses || {}

  return (
    <div className="min-h-screen bg-gray-50">
      <NavUtilisateur />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md p-6 space-y-6">
            <PageHeader
              title="Résultat de l'analyse"
              description={`Slug : ${slug}`}
            />

        <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InfoCard title="Entreprise" value={data.nom || data.nom_entreprise || '—'} />
          <InfoCard title="RCS" value={data.rcs || '—'} />
          <InfoCard title="Score total" value={data.score_global ?? data.score_total ?? '—'} />
          <InfoCard title="Qualité" value={data.qualite ?? data.precision ?? '—'} />
        </section>

            <section>
              <h2 className="text-lg font-semibold mb-2 text-gray-900">Niveau de risque</h2>
              <RiskBadge
                risk={data.niveau_risque_label || risque}
                score={data.score_global ?? data.score_total}
              />
            </section>

            <ScoreBreakdown breakdown={data.score_breakdown} />

        {data.synthese && (
          <section>
            <h2 className="text-lg font-semibold mb-2">Synthèse</h2>
            <p className="bg-gray-100 p-4 rounded">{data.synthese}</p>
          </section>
        )}

            {details.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-3 text-gray-900">Détails</h2>
                <div className="space-y-3">
                  {details.map((detail, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <p className="font-semibold text-gray-900">{detail.question}</p>
                      <p className="mt-1 text-sm text-gray-700">{detail.reponse || '—'}</p>
                      {detail.rule_id && (
                        <p className="mt-1 text-xs text-gray-500">
                          {detail.rule_id}
                          {detail.risk_type ? ` · ${detail.risk_type}` : ''}
                          {detail.evidence?.page ? ` · page ${detail.evidence.page}` : ''}
                        </p>
                      )}
                      {detail.justification && (
                        <p className="mt-1 text-xs text-gray-500">Justification : {detail.justification}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="border-t border-gray-100 pt-6">
              <h2 className="text-lg font-semibold mb-2 text-gray-900">Findings et preuves</h2>
              <p className="mb-3 text-sm text-gray-600">
                Les constats de cette analyse peuvent devenir des preuves de conformité.
              </p>
              {evidence.length === 0 ? (
                <p className="text-sm text-gray-500">Aucune preuve liée pour le moment.</p>
              ) : (
                <ul className="mb-3 space-y-2">
                  {evidence.map((item) => (
                    <li key={item.id} className="rounded-lg border border-gray-100 px-3 py-2 text-sm">
                      <p className="font-medium text-gray-900">{item.title}</p>
                      <p className="text-xs text-gray-500">
                        {(item.framework_code || '').toUpperCase()} · {item.status}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
              <Link href="/conformite" className="text-sm font-medium text-[#003366]">
                Valider les preuves dans Conformité →
              </Link>
            </section>

            {Object.keys(reponses).length > 0 && (
              <section>
                <h2 className="text-lg font-semibold mb-2 text-gray-900">Réponses brutes</h2>
                <ul className="list-disc ml-6 space-y-2 text-gray-700">
                  {Object.entries(reponses).map(([question, reponse]) => (
                    <li key={question}>
                      <strong>{question}</strong> : {reponse}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function InfoCard({ title, value }) {
  return (
    <div className="rounded-lg border bg-gray-50 p-4">
      <p className="text-xs uppercase tracking-wide text-gray-500">{title}</p>
      <p className="mt-1 text-lg font-semibold text-gray-800">{value}</p>
    </div>
  )
}
