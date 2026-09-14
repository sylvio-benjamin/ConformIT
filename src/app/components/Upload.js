'use client'

import { useEffect, useState } from 'react'
import { Loader2, UploadCloud, CheckCircle, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { API_URL } from '@/lib/apiConfig'
import { DOCUMENT_TYPES, uploadPromptFor } from '@/lib/documentTypes'
import Select from '@/components/Select'

function errorMessage(data) {
  if (!data) return 'Erreur inconnue'
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || item).join(' ')
  }
  return data.error || data.message || 'Aucun slug renvoyé'
}

export default function Upload() {
  const [fichier, setFichier] = useState(null)
  const [loading, setLoading] = useState(false)
  const [afficherInterface, setAfficherInterface] = useState(false)
  const [documentType, setDocumentType] = useState('')
  const [types, setTypes] = useState(DOCUMENT_TYPES)

  useEffect(() => {
    if (!afficherInterface) return undefined
    let cancelled = false
    fetch(`${API_URL}/document-types/`, { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : null))
      .then((payload) => {
        if (cancelled || !payload?.types?.length) return
        setTypes(
          payload.types.map((item) => ({
            id: item.id,
            label: item.label,
            uploadPrompt: item.upload_prompt || uploadPromptFor(item.id),
          }))
        )
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [afficherInterface])

  const selected = types.find((item) => item.id === documentType)
  const uploadPrompt = selected?.uploadPrompt || uploadPromptFor(documentType)

  const resetModal = () => {
    setAfficherInterface(false)
    setFichier(null)
    setDocumentType('')
  }

  const handleValidate = async () => {
    if (!documentType) {
      toast.error('Veuillez d’abord sélectionner le type de document.')
      return
    }
    if (!fichier) {
      toast.error('Veuillez sélectionner un fichier (PDF, CSV ou Excel).')
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('pdf', fichier)
    formData.append('document_type', documentType)

    try {
      const url = `${API_URL}/analyser/`
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      const text = await res.text()
      let data

      try {
        data = JSON.parse(text)
      } catch {
        toast.error('❌ Réponse du serveur invalide (pas de JSON)')
        setLoading(false)
        return
      }

      if (res.ok && data?.slug) {
        localStorage.setItem('slug', data.slug)
        toast.success('✅ Fichier bien téléversé.\nRedirection en cours...')
        window.location.href = '/employe/attente'
      } else {
        toast.error(errorMessage(data))
      }
    } catch (error) {
      toast.error('Erreur réseau : ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) {
      setFichier(null)
      return
    }

    const allowedTypes = [
      'application/pdf',
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]

    const allowedExtensions = ['.pdf', '.csv', '.xls', '.xlsx']

    const fileTypeOk = allowedTypes.includes(file.type)
    const fileExtensionOk = allowedExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    )

    if (fileTypeOk || fileExtensionOk) {
      setFichier(file)
    } else {
      setFichier(null)
      toast.error('Formats autorisés : PDF, CSV, XLS, XLSX.')
    }
  }

  return (
    <>
      <div className="my-12 flex justify-center">
        <button
          onClick={() => setAfficherInterface(true)}
          className="px-8 py-3 bg-indigo-600 text-white text-lg font-semibold rounded-xl hover:bg-indigo-700 shadow transition"
        >
          📄 Démarrer l’analyse de document
        </button>
      </div>

      {afficherInterface && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center transition-opacity duration-300">
          <div className="relative bg-white w-full max-w-3xl mx-auto rounded-2xl p-8 shadow-xl animate-slide-in-up">
            <button
              onClick={resetModal}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
            >
              <X size={24} />
            </button>

            <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">
              Analyser un document
            </h2>
            <p className="text-center text-sm text-gray-500 mb-6">
              Le type choisi oriente l’extracteur et les questions. Il ne remplace pas les preuves du document.
            </p>

            <div className="mb-6">
              <Select
                label="Quel document souhaitez-vous analyser ?"
                required
                value={documentType}
                onChange={(event) => setDocumentType(event.target.value)}
                options={[
                  { value: '', label: 'Choisir un type' },
                  ...types.map((item) => ({ value: item.id, label: item.label })),
                ]}
              />
            </div>

            {documentType ? (
              <label
                htmlFor="fichier"
                className="flex flex-col items-center justify-center w-full border-2 border-dashed border-gray-300 rounded-xl px-6 py-10 text-center cursor-pointer hover:border-indigo-500 transition"
              >
                <UploadCloud size={42} className="text-indigo-500 mb-2" />
                <span className="text-gray-700 font-medium">{uploadPrompt}</span>
                <span className="mt-1 text-sm text-gray-500">PDF, CSV ou Excel</span>
                <input
                  type="file"
                  accept=".pdf,.csv,.xls,.xlsx,application/pdf,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={handleFileChange}
                  id="fichier"
                  className="hidden"
                />
              </label>
            ) : (
              <div className="w-full border-2 border-dashed border-gray-200 rounded-xl px-6 py-10 text-center text-gray-400">
                Sélectionnez d’abord le type de document.
              </div>
            )}

            {fichier && (
              <p className="mt-4 text-sm text-gray-600">
                <strong>Fichier sélectionné :</strong> {fichier.name}
              </p>
            )}

            <button
              onClick={handleValidate}
              disabled={loading}
              className={`mt-8 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold transition
                ${loading ? 'bg-gray-400 text-white cursor-wait' : 'bg-green-600 text-white hover:bg-green-700'}
              `}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <CheckCircle size={18} />
                  Lancer l’analyse
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
