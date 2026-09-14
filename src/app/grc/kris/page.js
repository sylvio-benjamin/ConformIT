'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, Plus, Edit, Trash2, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import { toast } from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'

export default function KRIsPage() {
  const { user } = useAuth()
  const [kris, setKris] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)

  const refresh = async () => {
    const data = await grcAPI.kris.list(user, user.organization_id)
    setKris(data.kris || data || [])
  }

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    refresh().catch(() => setKris([])).finally(() => setLoading(false))
  }, [user])

  const handleAddKRI = async (kriData) => {
    if (!user?.uid) return

    try {
      await grcAPI.kris.create(user, user.organization_id, {
        name: kriData.name,
        description: kriData.description,
      })
      await refresh()
      toast.success('KRI ajouté avec succès')
      setShowAddModal(false)
    } catch (error) {
      console.error('Erreur lors de l\'ajout du KRI:', error)
      toast.error('Erreur lors de l\'ajout du KRI')
    }
  }

  const handleDeleteKRI = async (kriId) => {
    if (!user?.uid || !window.confirm('Êtes-vous sûr de vouloir supprimer ce KRI ?')) return

    try {
      await grcAPI.kris.delete(user, user.organization_id, kriId)
      setKris((prev) => prev.filter((k) => k.id !== kriId))
      toast.success('KRI supprimé avec succès')
    } catch (error) {
      console.error('Erreur lors de la suppression du KRI:', error)
      toast.error('Erreur lors de la suppression du KRI')
    }
  }

  if (loading) {
    return <LoadingSpinner message="Chargement des KRIs..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Indicateurs Clés de Risque (KRIs)"
        description="Surveillance des indicateurs clés de risque"
        action={
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            <Plus className="h-5 w-5 mr-2" />
            Ajouter un KRI
          </Button>
        }
      />

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
                Valeur actuelle
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Seuil
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
            {kris.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                  Aucun KRI trouvé
                </td>
              </tr>
            ) : (
              kris.map((kri) => (
                <tr key={kri.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {kri.name || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {kri.description || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {kri.currentValue || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {kri.threshold || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {kri.status === 'alert' ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700">
                        Alerte
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">
                        Normal
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <button
                      onClick={() => handleDeleteKRI(kri.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      {showAddModal && (
        <KRIModal
          onClose={() => setShowAddModal(false)}
          onSave={handleAddKRI}
        />
      )}
    </div>
  )
}

function KRIModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    currentValue: '',
    threshold: '',
    status: 'normal',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Ajouter un KRI</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom du KRI
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valeur actuelle
              </label>
              <input
                type="number"
                value={formData.currentValue}
                onChange={(e) => setFormData({ ...formData, currentValue: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Seuil
              </label>
              <input
                type="number"
                value={formData.threshold}
                onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
                required
              />
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
              Ajouter
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

