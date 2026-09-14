'use client'

import { useEffect, useState } from 'react'
import { FileCheck, CheckCircle, XCircle, AlertCircle, TrendingUp } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import { toast } from 'react-hot-toast'

export default function CompliancePage() {
  const { user } = useAuth()
  const [compliance, setCompliance] = useState({
    iso31000: { status: 'not_assessed', score: 0 },
    iso27005: { status: 'not_assessed', score: 0 },
    coso_erm: { status: 'not_assessed', score: 0 },
    cobit: { status: 'not_assessed', score: 0 },
    sox: { status: 'not_assessed', score: 0 },
    rgpd: { status: 'not_assessed', score: 0 },
  })
  const [profile, setProfile] = useState({
    sector: '',
    size: 'PME',
    country: 'FR',
    criticality: 'medium',
    processes_personal_data: false,
    hosting: 'cloud',
    listed_company: false,
  })
  const [decisions, setDecisions] = useState([])
  const [catalogStandards, setCatalogStandards] = useState([])
  const [evidence, setEvidence] = useState([])
  const [savingProfile, setSavingProfile] = useState(false)
  const [loading, setLoading] = useState(true)

  const loadApplicableStandards = () =>
    grcAPI.applicability.standards()
      .then((payload) => {
        if (payload.decisions) setDecisions(payload.decisions)
        setCatalogStandards(payload.standards || [])
      })
      .catch(() => setCatalogStandards([]))

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    Promise.all([
      grcAPI.compliance.get().catch(() => ({})),
      grcAPI.profile.get().catch(() => ({})),
      grcAPI.applicability.standards().catch(() => ({ decisions: [], standards: [] })),
      grcAPI.evidence.list().catch(() => ({ evidence: [] })),
    ])
      .then(([scores, orgProfile, applicability, evidenceData]) => {
        setCompliance((prev) => ({ ...prev, ...scores }))
        setProfile((prev) => ({ ...prev, ...orgProfile }))
        setDecisions(applicability.decisions || [])
        setCatalogStandards(applicability.standards || [])
        setEvidence(evidenceData.evidence || [])
      })
      .finally(() => setLoading(false))
  }, [user])

  const decisionByFramework = Object.fromEntries(
    (decisions || []).map((item) => [item.framework_code, item])
  )

  const handleReviewEvidence = async (id, status) => {
    try {
      const updated = await grcAPI.evidence.review(id, status)
      setEvidence((prev) => prev.map((item) => (item.id === id ? updated : item)))
      toast.success(status === 'accepted' ? 'Preuve acceptée' : 'Preuve rejetée')
    } catch (error) {
      toast.error(error.message || 'Impossible de revoir cette preuve')
    }
  }

  const handleSaveProfile = async (event) => {
    event.preventDefault()
    setSavingProfile(true)
    try {
      const result = await grcAPI.profile.save({
        sector: profile.sector || null,
        size: profile.size || null,
        country: profile.country || 'FR',
        criticality: profile.criticality,
        processes_personal_data: !!profile.processes_personal_data,
        hosting: profile.hosting,
        listed_company: !!profile.listed_company,
        notes: profile.notes || null,
      })
      setProfile((prev) => ({ ...prev, ...result.profile }))
      setDecisions(result.applicability || [])
      await loadApplicableStandards()
      toast.success('Profil enregistré. Applicabilité recalculée.')
    } catch (error) {
      toast.error(error.message || 'Impossible d’enregistrer le profil')
    } finally {
      setSavingProfile(false)
    }
  }

  const frameworks = [
    {
      id: 'iso31000',
      name: 'ISO 31000',
      description: 'Gestion des risques - Principes et lignes directrices',
      status: compliance.iso31000?.status || 'not_assessed',
      score: compliance.iso31000?.score || 0,
    },
    {
      id: 'iso27005',
      name: 'ISO 27005',
      description: 'Gestion des risques de sécurité de l\'information',
      status: compliance.iso27005?.status || 'not_assessed',
      score: compliance.iso27005?.score || 0,
    },
    {
      id: 'coso_erm',
      name: 'COSO ERM',
      description: 'Enterprise Risk Management - Integrated Framework',
      status: compliance.coso_erm?.status || 'not_assessed',
      score: compliance.coso_erm?.score || 0,
    },
    {
      id: 'cobit',
      name: 'COBIT',
      description: 'Control Objectives for Information and Related Technologies',
      status: compliance.cobit?.status || 'not_assessed',
      score: compliance.cobit?.score || 0,
    },
    {
      id: 'sox',
      name: 'SOX',
      description: 'Sarbanes-Oxley Act - Contrôles financiers',
      status: compliance.sox?.status || 'not_assessed',
      score: compliance.sox?.score || 0,
    },
    {
      id: 'rgpd',
      name: 'RGPD',
      description: 'Règlement Général sur la Protection des Données',
      status: compliance.rgpd?.status || 'not_assessed',
      score: compliance.rgpd?.score || 0,
    },
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="h-6 w-6 text-green-500" />
      case 'non_compliant':
        return <XCircle className="h-6 w-6 text-red-500" />
      case 'partially_compliant':
        return <AlertCircle className="h-6 w-6 text-yellow-500" />
      default:
        return <AlertCircle className="h-6 w-6 text-gray-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-700'
      case 'non_compliant':
        return 'bg-red-100 text-red-700'
      case 'partially_compliant':
        return 'bg-yellow-100 text-yellow-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'compliant':
        return 'Conforme'
      case 'non_compliant':
        return 'Non conforme'
      case 'partially_compliant':
        return 'Partiellement conforme'
      default:
        return 'Non évalué'
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003366] mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement de la conformité...</p>
        </div>
      </div>
    )
  }

  const overallScore = frameworks.reduce((sum, f) => sum + (f.score || 0), 0) / frameworks.length

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Conformité</h1>
        <p className="text-gray-600">
          Profil d’organisation, applicabilité, puis preuves issues des analyses.{' '}
          <a href="/analyses" className="font-medium text-[#003366]">Voir les analyses →</a>
        </p>
      </div>

      <form onSubmit={handleSaveProfile} className="mb-8 bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Profil d’organisation</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="text-sm text-gray-700">
            Secteur
            <select
              className="mt-1 w-full border rounded-lg px-3 py-2"
              value={profile.sector || ''}
              onChange={(e) => setProfile((p) => ({ ...p, sector: e.target.value }))}
            >
              <option value="">Non renseigné</option>
              <option value="it">IT / numérique</option>
              <option value="finance">Finance</option>
              <option value="banque">Banque</option>
              <option value="assurance">Assurance</option>
              <option value="industrie">Industrie</option>
              <option value="sante">Santé</option>
              <option value="autre">Autre</option>
            </select>
          </label>
          <label className="text-sm text-gray-700">
            Taille
            <select
              className="mt-1 w-full border rounded-lg px-3 py-2"
              value={profile.size || 'PME'}
              onChange={(e) => setProfile((p) => ({ ...p, size: e.target.value }))}
            >
              <option value="TPE">TPE</option>
              <option value="PME">PME</option>
              <option value="ETI">ETI</option>
              <option value="GE">Grande entreprise</option>
            </select>
          </label>
          <label className="text-sm text-gray-700">
            Pays
            <input
              className="mt-1 w-full border rounded-lg px-3 py-2 uppercase"
              maxLength={2}
              value={profile.country || 'FR'}
              onChange={(e) => setProfile((p) => ({ ...p, country: e.target.value.toUpperCase() }))}
            />
          </label>
          <label className="text-sm text-gray-700">
            Criticité
            <select
              className="mt-1 w-full border rounded-lg px-3 py-2"
              value={profile.criticality || 'medium'}
              onChange={(e) => setProfile((p) => ({ ...p, criticality: e.target.value }))}
            >
              <option value="low">Faible</option>
              <option value="medium">Moyenne</option>
              <option value="high">Élevée</option>
              <option value="critical">Critique</option>
            </select>
          </label>
          <label className="text-sm text-gray-700">
            Hébergement
            <select
              className="mt-1 w-full border rounded-lg px-3 py-2"
              value={profile.hosting || 'cloud'}
              onChange={(e) => setProfile((p) => ({ ...p, hosting: e.target.value }))}
            >
              <option value="cloud">Cloud</option>
              <option value="onprem">On-premise</option>
              <option value="hybrid">Hybride</option>
            </select>
          </label>
          <div className="flex flex-col justify-end gap-2 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!profile.processes_personal_data}
                onChange={(e) => setProfile((p) => ({ ...p, processes_personal_data: e.target.checked }))}
              />
              Données personnelles
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!profile.listed_company}
                onChange={(e) => setProfile((p) => ({ ...p, listed_company: e.target.checked }))}
              />
              Société cotée
            </label>
          </div>
        </div>
        <button
          type="submit"
          disabled={savingProfile}
          className="mt-4 bg-[#003366] text-white px-4 py-2 rounded-lg hover:bg-[#002244] disabled:opacity-60"
        >
          {savingProfile ? 'Enregistrement…' : 'Enregistrer et recalculer'}
        </button>
      </form>

      <div className="mb-8 bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Normes potentiellement applicables</h2>
        <p className="mb-4 text-sm text-gray-600">
          Applicabilité = quelles normes sont pertinentes, et pourquoi. Cela ne calcule pas le risque.
          Métadonnées ISO Open Data uniquement — le résumé catalogue n’est pas une exigence.
        </p>
        <ul className="mb-4 space-y-2">
          {decisions.filter((item) => item.applicable).map((item) => (
            <li key={item.framework_code} className="rounded-lg border border-gray-100 px-3 py-2 text-sm">
              <p className="font-medium text-gray-900">{(item.framework_code || '').toUpperCase()} — applicable</p>
              <p className="text-xs text-gray-500">
                {(item.reasons || [item.reason]).filter(Boolean).join(' · ') || 'Aucun critère d’applicabilité détecté'}
              </p>
            </li>
          ))}
        </ul>
        <p className="mb-3 text-xs text-gray-500">
          L’évaluation actuelle utilise les questions documentaires existantes (Kbis, attestation, comptes).
          Les questions détaillées ISO (Niveau C) restent bloquées tant que la licence n’est pas obtenue.
        </p>
        {catalogStandards.length === 0 ? (
          <p className="text-xs text-gray-500">
            Aucune métadonnée catalogue liée pour le moment. Importer le CSV officiel en staging si besoin.
          </p>
        ) : (
          <ul className="space-y-2">
            {catalogStandards.map((item) => (
              <li key={item.iso_id} className="text-sm text-gray-700">
                <span className="font-medium">{item.reference}</span>
                {item.title_fr || item.title_en ? ` — ${item.title_fr || item.title_en}` : ''}
              </li>
            ))}
          </ul>
        )}
      </div>

      {evidence.length > 0 && (
        <div className="mb-8 bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Preuves proposées</h2>
          <p className="text-sm text-gray-600 mb-4">
            Issues des findings d’analyse (sévérité moyenne et plus), pour les cadres applicables.
          </p>
          <ul className="space-y-3">
            {evidence.map((item) => (
              <li key={item.id} className="border border-gray-100 rounded-lg p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                  <p className="font-medium text-gray-900">{item.title}</p>
                  <p className="text-xs text-gray-500">
                    {(item.framework_code || 'iso31000').toUpperCase()} · {item.severity || '—'} · {item.status}
                  </p>
                  {item.detail && <p className="text-sm text-gray-600 mt-1">{item.detail}</p>}
                </div>
                {item.status === 'proposed' && (
                  <div className="flex gap-2 shrink-0">
                    <button
                      type="button"
                      className="px-3 py-1 text-sm rounded-lg bg-green-100 text-green-800"
                      onClick={() => handleReviewEvidence(item.id, 'accepted')}
                    >
                      Accepter
                    </button>
                    <button
                      type="button"
                      className="px-3 py-1 text-sm rounded-lg bg-red-100 text-red-800"
                      onClick={() => handleReviewEvidence(item.id, 'rejected')}
                    >
                      Rejeter
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Overall Score */}
      <div className="mb-8 bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Score global de conformité</h2>
          <div className="text-4xl font-bold text-[#003366]">{overallScore.toFixed(1)}%</div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="bg-[#00A859] h-4 rounded-full transition-all"
            style={{ width: `${overallScore}%` }}
          />
        </div>
      </div>

      {/* Frameworks */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {frameworks.map((framework) => (
          <div
            key={framework.id}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(framework.status)}
                <h3 className="text-lg font-semibold text-gray-900">{framework.name}</h3>
              </div>
              {decisionByFramework[framework.id] && (
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  decisionByFramework[framework.id].applicable
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {decisionByFramework[framework.id].applicable ? 'Applicable' : 'Hors périmètre'}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 mb-2">{framework.description}</p>
            {decisionByFramework[framework.id]?.reason && (
              <p className="text-xs text-gray-500 mb-4">{decisionByFramework[framework.id].reason}</p>
            )}
            <div className="flex items-center justify-between mb-4">
              <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(framework.status)}`}>
                {getStatusLabel(framework.status)}
              </span>
              <span className="text-sm font-medium text-gray-700">
                Score: {framework.score}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  framework.status === 'compliant' ? 'bg-green-500' :
                  framework.status === 'non_compliant' ? 'bg-red-500' :
                  framework.status === 'partially_compliant' ? 'bg-yellow-500' :
                  'bg-gray-400'
                }`}
                style={{ width: `${framework.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Assessment Guide */}
      <div className="mt-8 bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Guide d'évaluation</h2>
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Pour évaluer votre conformité, vous pouvez :
          </p>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
            <li>Réaliser un audit interne selon chaque framework</li>
            <li>Consulter un expert en conformité</li>
            <li>Utiliser des outils d'évaluation automatisés</li>
            <li>Mettre à jour régulièrement votre état de conformité</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

