'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle, Plus, Edit, Trash2, Eye, Search, Filter } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import { toast } from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'

export default function RisksPage() {
  const { user } = useAuth()
  const [risks, setRisks] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingRisk, setEditingRisk] = useState(null)
  const [treatments, setTreatments] = useState([])
  const [treatmentForm, setTreatmentForm] = useState({
    risk_id: '',
    strategy: 'mitigate',
    description: '',
  })

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    Promise.all([
      grcAPI.risks.list(user, user.organization_id).catch(() => []),
      grcAPI.treatments.list().catch(() => ({ treatments: [] })),
    ])
      .then(([data, treatmentData]) => {
        const rows = Array.isArray(data) ? data : data.risks || []
        setRisks(rows.map((risk) => ({
          id: risk.id,
          name: risk.title || risk.name,
          description: risk.description,
          status: risk.status,
          severity: risk.priority || risk.severity,
        })))
        setTreatments(treatmentData.treatments || [])
      })
      .finally(() => setLoading(false))
  }, [user])

  const filteredRisks = risks.filter((risk) => {
    const matchesSearch = risk.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      risk.description?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === 'all' || risk.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const handleAddRisk = async (riskData) => {
    if (!user?.uid) return

    try {
      await grcAPI.risks.create(user, user.organization_id, {
        title: riskData.name || riskData.title,
        description: riskData.description,
        priority: riskData.severity || riskData.priority,
      })
      toast.success('Risque ajouté avec succès')
      setShowAddModal(false)
      const data = await grcAPI.risks.list(user, user.organization_id)
      const rows = Array.isArray(data) ? data : data.risks || []
      setRisks(rows.map((risk) => ({
        id: risk.id,
        name: risk.title || risk.name,
        description: risk.description,
        status: risk.status,
        severity: risk.priority || risk.severity,
      })))
    } catch (error) {
      toast.error('Erreur lors de l\'ajout du risque')
    }
  }

  const handleDeleteRisk = async (riskId) => {
    if (!user?.uid || !window.confirm('Êtes-vous sûr de vouloir supprimer ce risque ?')) return

    try {
      await grcAPI.risks.delete(user, user.organization_id, riskId)
      setRisks((prev) => prev.filter((r) => r.id !== riskId))
      toast.success('Risque supprimé avec succès')
    } catch (error) {
      console.error('Erreur lors de la suppression du risque:', error)
      toast.error('Erreur lors de la suppression du risque')
    }
  }

  const getRiskColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-700'
      case 'high':
        return 'bg-orange-100 text-orange-700'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700'
      case 'low':
        return 'bg-green-100 text-green-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  if (loading) {
    return <LoadingSpinner message="Chargement des risques..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Registre des Risques"
        description="Gestion des risques selon ISO 31000"
        action={
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            <Plus className="h-5 w-5 mr-2" />
            Ajouter un risque
          </Button>
        }
      />

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Rechercher un risque..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
        >
          <option value="all">Tous les statuts</option>
          <option value="open">Ouverts</option>
          <option value="mitigated">Atténués</option>
          <option value="closed">Fermés</option>
        </select>
      </div>

      {/* Risks Table */}
      <Card className="overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Nom
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sévérité
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Probabilité
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Impact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Statut
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredRisks.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                  Aucun risque trouvé
                </td>
              </tr>
            ) : (
              filteredRisks.map((risk) => (
                <tr key={risk.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {risk.name || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {risk.description || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(risk.severity)}`}>
                      {risk.severity || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {risk.probability || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {risk.impact || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {risk.status || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <div className="flex justify-center gap-2">
                      <button
                        onClick={() => {
                          setEditingRisk(risk)
                          setShowAddModal(true)
                        }}
                        className="text-blue-600 hover:text-blue-800 transition"
                        title="Modifier"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteRisk(risk.id)}
                        className="text-red-600 hover:text-red-800 transition"
                        title="Supprimer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      <Card className="mt-8 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Traitements</h2>
        <form
          className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6"
          onSubmit={async (event) => {
            event.preventDefault()
            if (!treatmentForm.risk_id) {
              toast.error('Choisissez un risque')
              return
            }
            try {
              const created = await grcAPI.treatments.create(treatmentForm)
              setTreatments((prev) => [created, ...prev])
              setTreatmentForm((prev) => ({ ...prev, description: '' }))
              toast.success('Traitement enregistré')
            } catch (error) {
              toast.error(error.message || 'Impossible d’enregistrer le traitement')
            }
          }}
        >
          <select
            className="px-3 py-2 border rounded-lg"
            value={treatmentForm.risk_id}
            onChange={(e) => setTreatmentForm((prev) => ({ ...prev, risk_id: e.target.value }))}
          >
            <option value="">Risque…</option>
            {risks.map((risk) => (
              <option key={risk.id} value={risk.id}>{risk.name}</option>
            ))}
          </select>
          <select
            className="px-3 py-2 border rounded-lg"
            value={treatmentForm.strategy}
            onChange={(e) => setTreatmentForm((prev) => ({ ...prev, strategy: e.target.value }))}
          >
            <option value="mitigate">Atténuer</option>
            <option value="accept">Accepter</option>
            <option value="transfer">Transférer</option>
            <option value="avoid">Éviter</option>
          </select>
          <input
            className="px-3 py-2 border rounded-lg"
            placeholder="Description"
            value={treatmentForm.description}
            onChange={(e) => setTreatmentForm((prev) => ({ ...prev, description: e.target.value }))}
          />
          <Button type="submit" variant="primary">Ajouter</Button>
        </form>
        {treatments.length === 0 ? (
          <p className="text-sm text-gray-500">Aucun traitement pour l’instant.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {treatments.map((item) => (
              <li key={item.id} className="flex justify-between gap-3 border-b border-gray-100 pb-2">
                <span>{item.description || item.strategy}</span>
                <span className="text-gray-500">{item.strategy} · {item.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <RiskModal
          risk={editingRisk}
          onClose={() => {
            setShowAddModal(false)
            setEditingRisk(null)
          }}
          onSave={handleAddRisk}
        />
      )}
    </div>
  )
}

function RiskModal({ risk, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: risk?.name || '',
    description: risk?.description || '',
    severity: risk?.severity || 'medium',
    probability: risk?.probability || 'medium',
    impact: risk?.impact || 'medium',
    status: risk?.status || 'open',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {risk ? 'Modifier le risque' : 'Ajouter un risque'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nom du risque"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
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
                Sévérité
              </label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="low">Faible</option>
                <option value="medium">Moyen</option>
                <option value="high">Élevé</option>
                <option value="critical">Critique</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Probabilité
              </label>
              <select
                value={formData.probability}
                onChange={(e) => setFormData({ ...formData, probability: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="low">Faible</option>
                <option value="medium">Moyen</option>
                <option value="high">Élevé</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Impact
              </label>
              <select
                value={formData.impact}
                onChange={(e) => setFormData({ ...formData, impact: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
              >
                <option value="low">Faible</option>
                <option value="medium">Moyen</option>
                <option value="high">Élevé</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Statut
            </label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
            >
              <option value="open">Ouvert</option>
              <option value="mitigated">Atténué</option>
              <option value="closed">Fermé</option>
            </select>
          </div>
          <div className="flex justify-end gap-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Annuler
            </Button>
            <Button type="submit" variant="primary">
              {risk ? 'Modifier' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

