'use client'

import { useEffect, useState } from 'react'
import { Shield, Plus, Edit, Trash2, CheckCircle, XCircle, Search } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import { toast } from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'

export default function ControlsPage() {
  const { user } = useAuth()
  const [controls, setControls] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  const refresh = async () => {
    const data = await grcAPI.controls.list(user, user.organization_id)
    setControls(data.controls || data || [])
  }

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    refresh().catch(() => setControls([])).finally(() => setLoading(false))
  }, [user])

  const filteredControls = controls.filter((control) =>
    control.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    control.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleAddControl = async (controlData) => {
    if (!user?.uid) return

    try {
      await grcAPI.controls.create(user, user.organization_id, {
        name: controlData.name,
        description: controlData.description,
        control_type: controlData.type || controlData.control_type,
      })
      toast.success('Contrôle ajouté avec succès')
      setShowAddModal(false)
      await refresh()
    } catch (error) {
      toast.error('Erreur lors de l\'ajout du contrôle')
    }
  }

  const handleDeleteControl = async (controlId) => {
    if (!user?.uid || !window.confirm('Êtes-vous sûr de vouloir supprimer ce contrôle ?')) return

    try {
      await grcAPI.controls.delete(user, user.organization_id, controlId)
      setControls((prev) => prev.filter((c) => c.id !== controlId))
      toast.success('Contrôle supprimé avec succès')
    } catch (error) {
      console.error('Erreur lors de la suppression du contrôle:', error)
      toast.error('Erreur lors de la suppression du contrôle')
    }
  }

  if (loading) {
    return <LoadingSpinner message="Chargement des contrôles..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Contrôles"
        description="Gestion des contrôles et mesures de mitigation"
        action={
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            <Plus className="h-5 w-5 mr-2" />
            Ajouter un contrôle
          </Button>
        }
      />

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Rechercher un contrôle..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

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
                Type
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
            {filteredControls.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                  Aucun contrôle trouvé
                </td>
              </tr>
            ) : (
              filteredControls.map((control) => (
                <tr key={control.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {control.name || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {control.description || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {control.type || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {control.status === 'active' ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">
                        Actif
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700">
                        Inactif
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <div className="flex justify-center gap-2">
                      <button
                        onClick={() => handleDeleteControl(control.id)}
                        className="text-red-600 hover:text-red-800"
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

      {showAddModal && (
        <ControlModal
          onClose={() => setShowAddModal(false)}
          onSave={handleAddControl}
        />
      )}
    </div>
  )
}

function ControlModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'preventive',
    status: 'active',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Ajouter un contrôle</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nom du contrôle"
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
            >
              <option value="preventive">Préventif</option>
              <option value="detective">Détectif</option>
              <option value="corrective">Correctif</option>
            </select>
          </div>
          <div className="flex justify-end gap-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Annuler
            </Button>
            <Button type="submit" variant="primary">
              Ajouter
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

