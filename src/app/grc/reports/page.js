'use client'

import { useEffect, useState } from 'react'
import { FileText, Plus, Download, Eye, Calendar, Clock } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import { toast } from 'react-hot-toast'

export default function ReportsPage() {
  const { user } = useAuth()
  const [reports, setReports] = useState([])
  const [audits, setAudits] = useState([])
  const [loading, setLoading] = useState(true)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [auditTitle, setAuditTitle] = useState('')
  const [auditType, setAuditType] = useState('internal')

  const refresh = async () => {
    const [data, auditData] = await Promise.all([
      grcAPI.reports.list(user, user.organization_id),
      grcAPI.audits.list().catch(() => ({ audits: [] })),
    ])
    setReports(data.reports || data || [])
    setAudits(auditData.audits || [])
  }

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    refresh().catch(() => {
      setReports([])
      setAudits([])
    }).finally(() => setLoading(false))
  }, [user])

  const handleGenerateReport = async (reportData) => {
    if (!user?.uid) return

    try {
      await grcAPI.reports.create(user, user.organization_id, {
        title: reportData.title || reportData.name || 'Rapport GRC',
        report_type: reportData.type || 'risk_report',
      })
      await refresh()
      toast.success('Rapport en cours de génération...')
      setShowGenerateModal(false)
    } catch (error) {
      console.error('Erreur lors de la génération du rapport:', error)
      toast.error('Erreur lors de la génération du rapport')
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003366] mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement des rapports...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Rapports</h1>
          <p className="text-gray-600">Génération et gestion des rapports GRC</p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#003366] text-white rounded-lg hover:bg-[#004080] transition"
        >
          <Plus className="h-5 w-5" />
          Générer un rapport
        </button>
      </div>

      <div className="mb-10 bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Audits GRC</h2>
        <form
          className="flex flex-col md:flex-row gap-3 mb-4"
          onSubmit={async (event) => {
            event.preventDefault()
            if (!auditTitle.trim()) return
            try {
              const created = await grcAPI.audits.create({
                title: auditTitle.trim(),
                audit_type: auditType,
              })
              setAudits((prev) => [created, ...prev])
              setAuditTitle('')
              toast.success('Audit créé')
            } catch (error) {
              toast.error(error.message || 'Impossible de créer l’audit')
            }
          }}
        >
          <input
            className="flex-1 px-3 py-2 border rounded-lg"
            placeholder="Titre de l’audit"
            value={auditTitle}
            onChange={(e) => setAuditTitle(e.target.value)}
          />
          <select
            className="px-3 py-2 border rounded-lg"
            value={auditType}
            onChange={(e) => setAuditType(e.target.value)}
          >
            <option value="internal">Interne</option>
            <option value="external">Externe</option>
            <option value="self_assessment">Auto-évaluation</option>
          </select>
          <button type="submit" className="px-4 py-2 bg-[#003366] text-white rounded-lg">
            Créer
          </button>
        </form>
        {audits.length === 0 ? (
          <p className="text-sm text-gray-500">Aucun audit. Créez-en un, puis importez les preuves acceptées.</p>
        ) : (
          <ul className="space-y-3">
            {audits.map((audit) => (
              <li key={audit.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-3">
                <div>
                  <p className="font-medium text-gray-900">{audit.title}</p>
                  <p className="text-xs text-gray-500">{audit.audit_type} · {audit.status}</p>
                </div>
                <button
                  type="button"
                  className="text-sm px-3 py-1 rounded-lg bg-blue-50 text-blue-800"
                  onClick={async () => {
                    try {
                      const result = await grcAPI.audits.importEvidence(audit.id)
                      toast.success(`${result.created || 0} preuve(s) importée(s)`)
                    } catch (error) {
                      toast.error(error.message || 'Import impossible')
                    }
                  }}
                >
                  Importer les preuves acceptées
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            Aucun rapport trouvé
          </div>
        ) : (
          reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition"
            >
              <div className="flex items-center justify-between mb-4">
                <FileText className="h-8 w-8 text-[#003366]" />
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  report.status === 'completed' ? 'bg-green-100 text-green-700' :
                  report.status === 'generating' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {report.status === 'completed' ? 'Terminé' :
                   report.status === 'generating' ? 'En cours' :
                   'En attente'}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{report.name || 'Rapport'}</h3>
              <p className="text-sm text-gray-600 mb-4">{report.description || '—'}</p>
              <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {report.createdAt ? new Date(report.createdAt).toLocaleDateString() : '—'}
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {report.type || '—'}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  className="flex-1 px-4 py-2 bg-[#003366] text-white rounded-lg hover:bg-[#004080] transition text-sm"
                  onClick={() => toast('Téléchargement du rapport...')}
                >
                  <Download className="h-4 w-4 inline mr-2" />
                  Télécharger
                </button>
                <button
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                  onClick={() => toast('Visualisation du rapport...')}
                >
                  <Eye className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {showGenerateModal && (
        <GenerateReportModal
          onClose={() => setShowGenerateModal(false)}
          onGenerate={handleGenerateReport}
        />
      )}
    </div>
  )
}

function GenerateReportModal({ onClose, onGenerate }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'risk',
    format: 'pdf',
    period: 'monthly',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onGenerate(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Générer un rapport</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom du rapport
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              rows="3"
              required
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="risk">Risques</option>
                <option value="compliance">Conformité</option>
                <option value="incidents">Incidents</option>
                <option value="kris">KRIs</option>
                <option value="controls">Contrôles</option>
                <option value="full">Complet</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Format
              </label>
              <select
                value={formData.format}
                onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="pdf">PDF</option>
                <option value="excel">Excel</option>
                <option value="csv">CSV</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Période
              </label>
              <select
                value={formData.period}
                onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="daily">Quotidien</option>
                <option value="weekly">Hebdomadaire</option>
                <option value="monthly">Mensuel</option>
                <option value="quarterly">Trimestriel</option>
                <option value="yearly">Annuel</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-[#003366] text-white rounded-lg hover:bg-[#004080] transition"
            >
              Générer
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

