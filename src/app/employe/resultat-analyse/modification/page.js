'use client'

import { CheckCircle, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { API_URL } from '@/lib/apiConfig'
import { analysesAPI } from '@/services/api'

export default function Modification() {
  const { user, loading } = useAuth()
  const [infos, setInfos] = useState(null)
  const [loadingData, setLoadingData] = useState(true)
  const [editedDetails, setEditedDetails] = useState([])
  const [titreDocument, setTitreDocument] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const slugFromUrl = searchParams.get('slug')
    const storedSlug = typeof window !== 'undefined' ? localStorage.getItem('slug') : null
    const analyseId = typeof window !== 'undefined' ? localStorage.getItem('analyseId') : null
    const slugToUse = slugFromUrl || storedSlug

    if (slugFromUrl && typeof window !== 'undefined') {
      localStorage.setItem('slug', slugFromUrl)
    }

    if (!slugToUse) {
      setLoadingData(false)
      return
    }

    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/resultat/${slugToUse}`, {
          method: 'GET',
          credentials: 'include',
        })
        const data = await res.json()
        if (!data.analyseTerminee) {
          console.log('⌛ Analyse toujours en cours, nouvelle tentative dans 3s...')
          setTimeout(fetchData, 3000)
          return
        }
        setInfos(data)
        setEditedDetails(data.details || [])
        setLoadingData(false)
      } catch (error) {
        console.error('❌ Erreur chargement des données :', error)
        setLoadingData(false)
      }
    }
    fetchData()
  }, [router, searchParams])

  const handleEditChange = (idx, value) => {
    setEditedDetails(prev => prev.map((item, i) => (i === idx ? { ...item, reponse: value } : item)))
  }

  const handleValidate = async () => {
    const slug = searchParams.get('slug') || localStorage.getItem('slug')
    if (!slug || !infos || !user) return alert("ID ou infos manquants.")

    try {
      await analysesAPI.update(user, slug, { details: editedDetails })
      router.push('/analyses')
    } catch (err) {
      console.error('Erreur mise à jour analyse :', err)
      alert("Erreur de mise à jour")
    }
  }

  if (loading || loadingData) {
    return <div className="min-h-screen flex items-center justify-center">Chargement des données...</div>
  }

  if (!infos) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">Aucune donnée disponible.</div>
  }

  return (
    <div className="min-h-screen p-10 bg-gray-50 text-gray-800">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-blue-700">{infos.nom || 'Entreprise inconnue'}</h1>
          <p className="text-sm text-gray-500">Complétez ou modifiez les réponses avant validation finale.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gray-100 rounded-md p-4 text-center">
            <p className="text-sm text-gray-500">Score total</p>
            <p className="text-xl font-bold text-gray-800">{infos.score_total ?? '—'}</p>
          </div>
          <div className={`rounded-md p-4 text-center ${
            infos.risque?.toLowerCase().includes('critical') || infos.risque?.toLowerCase().includes('high')
              ? 'bg-red-100 text-red-700'
              : infos.risque?.toLowerCase().includes('medium')
              ? 'bg-yellow-100 text-yellow-700'
              : infos.risque?.toLowerCase().includes('low') || infos.risque?.toLowerCase().includes('faible')
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600'
          }`}>
            <p className="text-sm">Niveau de risque</p>
            <p className="text-xl font-bold capitalize">{infos.risque ?? '—'}</p>
          </div>
          <div className="bg-gray-100 rounded-md p-4 text-center">
            <p className="text-sm text-gray-500">Qualité des données</p>
            <p className="text-xl font-bold text-gray-800">{infos.qualite ?? '—'}</p>
          </div>
        </div>

        <div>
          <label htmlFor="titre" className="block text-sm font-semibold text-gray-600 mb-1">
            Titre du document
          </label>
          <input
            type="text"
            id="titre"
            value={titreDocument}
            onChange={(e) => setTitreDocument(e.target.value)}
            placeholder="Document de suivi..."
            className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-300"
          />
        </div>

        <div className="space-y-4">
          {editedDetails.map((item, idx) => (
            <div key={idx} className="bg-gray-100 rounded-md p-4">
              <p className="font-semibold text-sm text-gray-600">{item.question}</p>
              <input
                type="text"
                value={item.reponse}
                onChange={e => handleEditChange(idx, e.target.value)}
                className="w-full mt-2 px-3 py-2 border rounded-md"
              />
              <p className="text-xs text-gray-500 mt-1">Justification : {item.justification}</p>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-4 pt-8">
          <button
            onClick={handleValidate}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <CheckCircle size={20} />
            Valider et sauvegarder
          </button>
          <button
            onClick={() => router.push('/analyses')}
            className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            <XCircle size={20} />
            Annuler
          </button>
        </div>
      </div>
    </div>
  )
}
