'use client'

import { useEffect, useState } from 'react'
import { Plug, Plus, Settings, Trash2, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'react-hot-toast'
import { API_URL, getAuthHeaders } from '@/lib/apiConfig'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Card from '@/components/Card'

const AVAILABLE_INTEGRATIONS = [
  {
    id: 'infogreffe',
    type: 'infogreffe',
    name: 'Infogreffe',
    description: 'Intégration avec la base de données Infogreffe pour récupérer les données d\'entreprises',
    icon: '🏢',
    configFields: [
      { key: 'api_key', label: 'Clé API', type: 'password', required: true }
    ]
  },
  {
    id: 'insee',
    type: 'insee',
    name: 'INSEE',
    description: 'Intégration avec l\'INSEE pour récupérer les données statistiques et économiques',
    icon: '📊',
    configFields: [
      { key: 'api_key', label: 'Clé API', type: 'password', required: true }
    ]
  },
  {
    id: 'dun_bradstreet',
    type: 'dun_bradstreet',
    name: 'Dun & Bradstreet',
    description: 'Intégration avec Dun & Bradstreet pour récupérer les données financières et de crédit',
    icon: '💼',
    configFields: [
      { key: 'api_key', label: 'Clé API', type: 'password', required: true }
    ]
  },
  {
    id: 'powerbi',
    type: 'powerbi',
    name: 'PowerBI',
    description: 'Intégration avec PowerBI pour générer des dashboards et rapports',
    icon: '📈',
    configFields: [
      { key: 'client_id', label: 'Client ID (Azure AD)', type: 'text', required: true },
      { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
      { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true }
    ]
  },
]

export default function IntegrationsPage() {
  const { user } = useAuth()
  const [integrations, setIntegrations] = useState([])
  const [loading, setLoading] = useState(true)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState(null)
  const [configForm, setConfigForm] = useState({})
  const [testingConnection, setTestingConnection] = useState(false)

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }
    fetchIntegrations()
  }, [user])

  const fetchIntegrations = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/integrations`,
        {
          method: 'GET',
          credentials: 'include',
          headers: getAuthHeaders(),
        }
      )

      if (!res.ok) {
        throw new Error(`Erreur ${res.status}`)
      }

      const data = await res.json()
      setIntegrations(data || [])
    } catch (error) {
      console.error('Erreur lors du chargement des intégrations:', error)
      toast.error('Erreur lors du chargement des intégrations')
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = (integration) => {
    setSelectedIntegration(integration)
    setConfigForm({})
    setShowConfigModal(true)
  }

  const handleConfigChange = (key, value) => {
    setConfigForm(prev => ({ ...prev, [key]: value }))
  }

  const handleTestConnection = async () => {
    if (!selectedIntegration || !user) return

    setTestingConnection(true)
    try {
      const res = await fetch(`${API_URL}/api/integrations`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          integration_type: selectedIntegration.type,
          name: selectedIntegration.name,
          config: configForm,
          sync_frequency: 'manual',
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || `Erreur ${res.status}`)
      }

      const integration = await res.json()

      // Tester la connexion
      const testRes = await fetch(`${API_URL}/api/integrations/${integration.id}/test`, {
        method: 'POST',
        headers: getAuthHeaders(),
      })

      if (!testRes.ok) {
        throw new Error('Échec du test de connexion')
      }

      const testResult = await testRes.json()

      if (testResult.success) {
        toast.success(`${selectedIntegration.name} connecté avec succès !`)
        setShowConfigModal(false)
        fetchIntegrations()
      } else {
        toast.error('Échec de la connexion. Vérifiez vos identifiants.')
      }
    } catch (error) {
      console.error('Erreur lors de la connexion:', error)
      toast.error(error.message || 'Erreur lors de la connexion')
    } finally {
      setTestingConnection(false)
    }
  }

  const handleDisconnect = async (integrationId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir déconnecter cette intégration ?')) return

    try {
      const res = await fetch(`${API_URL}/api/integrations/${integrationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      })

      if (!res.ok) {
        throw new Error(`Erreur ${res.status}`)
      }

      toast.success('Intégration déconnectée avec succès')
      fetchIntegrations()
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error)
      toast.error('Erreur lors de la déconnexion')
    }
  }

  const handleSync = async (integrationId) => {
    try {
      const res = await fetch(`${API_URL}/api/integrations/${integrationId}/sync`, {
        method: 'POST',
        headers: getAuthHeaders(),
      })

      if (!res.ok) {
        throw new Error(`Erreur ${res.status}`)
      }

      const result = await res.json()
      toast.success(`Synchronisation réussie: ${result.records_synced} enregistrements`)
      fetchIntegrations()
    } catch (error) {
      console.error('Erreur lors de la synchronisation:', error)
      toast.error('Erreur lors de la synchronisation')
    }
  }

  const getIntegrationStatus = (integrationType) => {
    const integration = integrations.find(i => i.integration_type === integrationType)
    return integration?.status || 'not_connected'
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">
            <CheckCircle className="h-3 w-3" />
            Connecté
          </span>
        )
      case 'error':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700">
            <XCircle className="h-3 w-3" />
            Erreur
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700">
            <XCircle className="h-3 w-3" />
            Non connecté
          </span>
        )
    }
  }

  if (loading) {
    return <LoadingSpinner message="Chargement des intégrations..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Intégrations"
        description="Gestion des intégrations externes (Infogreffe, INSEE, APIs financières, PowerBI)"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        {AVAILABLE_INTEGRATIONS.map((integration) => {
          const status = getIntegrationStatus(integration.type)
          const existingIntegration = integrations.find(i => i.integration_type === integration.type)
          const isConnected = status === 'active'

          return (
            <Card key={integration.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{integration.icon}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                    {getStatusBadge(status)}
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4">{integration.description}</p>

              <div className="flex gap-2">
                {isConnected ? (
                  <>
                    <Button
                      onClick={() => handleSync(existingIntegration.id)}
                      variant="secondary"
                      size="sm"
                      icon={<RefreshCw className="h-4 w-4" />}
                    >
                      Synchroniser
                    </Button>
                    <Button
                      onClick={() => handleConnect(integration)}
                      variant="secondary"
                      size="sm"
                      icon={<Settings className="h-4 w-4" />}
                    >
                      Configurer
                    </Button>
                    <Button
                      onClick={() => handleDisconnect(existingIntegration.id)}
                      variant="danger"
                      size="sm"
                      icon={<Trash2 className="h-4 w-4" />}
                    />
                  </>
                ) : (
                  <Button
                    onClick={() => handleConnect(integration)}
                    variant="primary"
                    icon={Plus}
                    className="w-full"
                  >
                    Connecter
                  </Button>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Modal de configuration */}
      {showConfigModal && selectedIntegration && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Configurer {selectedIntegration.name}
            </h2>

            <div className="space-y-4">
              {selectedIntegration.configFields.map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type={field.type}
                    value={configForm[field.key] || ''}
                    onChange={(e) => handleConfigChange(field.key, e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
                    required={field.required}
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button
                onClick={() => setShowConfigModal(false)}
                variant="secondary"
              >
                Annuler
              </Button>
              <Button
                onClick={handleTestConnection}
                variant="primary"
                disabled={testingConnection}
                icon={testingConnection ? <RefreshCw className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              >
                {testingConnection ? 'Test en cours...' : 'Tester et Connecter'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
