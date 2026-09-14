'use client'

import { FileEdit, CheckCircle, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { API_URL } from '@/lib/apiConfig'
import ScoreBreakdown from '@/components/ScoreBreakdown'

export default function DetailEntreprise() {
  const { user, loading } = useAuth()
  const [infos, setInfos] = useState(null)
  const [loadingData, setLoadingData] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [editedDetails, setEditedDetails] = useState([])
  const [titreDocument, setTitreDocument] = useState('')
  const router = useRouter()

  useEffect(() => {
    const slug = localStorage.getItem('slug')
    if (!slug) return

    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/resultat/${slug}`, {
          method: 'GET',
          credentials: 'include',
        })
        
        if (!res.ok) {
          console.error(`❌ Erreur HTTP ${res.status}`)
          setLoadingData(false)
          return
        }
        
        const data = await res.json()
        if (!data.analyseTerminee) {
          console.log("\u23f3 Analyse toujours en cours, nouvelle tentative dans 3s...")
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
  }, [router])

  const handleValidate = async () => {
    if (!infos || !user) return alert("Impossible de valider l'analyse.")

    try {

      const risque = (infos.niveau_risque_label || infos.risque || '').toLowerCase()
      const risqueEstEleve = risque.includes('high') || risque.includes('critical') || risque.includes('élevé') || risque.includes('eleve') || risque.includes('critique')

      if (risqueEstEleve) {
        try {
          await fetch(`${API_URL}/api/v1/alerts/high-risk`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              entreprise: infos.nom,
              risque: infos.risque,
              score: infos.score_total,
              rcs: infos.rcs || infos.RCS || '',
            }),
          })
        } catch {
          // Webhook best-effort : ne bloque pas la validation
        }
      }

      localStorage.removeItem('slug')
      router.push('/analyses')
    } catch (error) {
      console.error("Erreur de validation :", error)
      alert("Erreur de validation")
    }
  }



  const handleEditChange = (idx, value) => {
    setEditedDetails(prev => prev.map((item, i) => i === idx ? { ...item, reponse: value } : item))
  }

  const handleEditSave = () => {
    setInfos(prev => ({ ...prev, details: editedDetails }))
    setEditMode(false)
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
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-blue-700">{infos.nom || 'Entreprise inconnue'}</h1>
            <p className="mt-2">
  <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium
    ${infos?.type_document === 'extrait_kbis' ? 'bg-blue-100 text-blue-700' :
      infos?.type_document === 'attestation_assurance' ? 'bg-green-100 text-green-700' :
      infos?.type_document === 'bilan_comptable' ? 'bg-yellow-100 text-yellow-700' :
      infos?.type_document === 'autorisation_commerciale' ? 'bg-purple-100 text-purple-700' :
      'bg-gray-100 text-gray-600'}
  `}>
    📄 {infos?.type_document?.replaceAll('_', ' ') ?? 'Inconnu'}
  </span>
</p>


            <p className="text-sm text-gray-500">RCS : {infos.rcs || 'Non renseigné'}</p>
          </div>
          {!editMode && (
            <button
              onClick={() => setEditMode(true)}
              title="Modifier les réponses"
              className="flex items-center gap-2 text-orange-500 hover:text-orange-600"
            >
              <FileEdit size={18} /> Modifier
            </button>
          )}
        </div>
  
        {/* Résumé de l'analyse */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gray-100 rounded-md p-4 text-center">
            <p className="text-sm text-gray-500">Score total</p>
            <p className="text-xl font-bold text-gray-800">{infos.score_global ?? infos.score_total ?? '—'}</p>
          </div>
          <div className={`rounded-md p-4 text-center 
            ${(infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('critical') || (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('élevé') || (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('high') ? 'bg-red-100 text-red-700' :
              (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('modér') || (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('medium') ? 'bg-yellow-100 text-yellow-700' :
                (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('low') || (infos.niveau_risque_label || infos.risque || '').toLowerCase().includes('faible') ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-600'}
          `}>
            <p className="text-sm">Niveau de risque</p>
            <p className="text-xl font-bold capitalize">{infos.niveau_risque_label || infos.risque || '—'}</p>
          </div>
          <div className="bg-gray-100 rounded-md p-4 text-center">
            <p className="text-sm text-gray-500">Qualité des données</p>
            <p className="text-xl font-bold text-gray-800">{infos.qualite ?? '—'}</p>
          </div>
        </div>

        <ScoreBreakdown breakdown={infos.score_breakdown} />
  
        {/* Titre du document */}
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
  
        {/* Liste des réponses */}
        <div className="space-y-4">
          {infos.details?.length > 0 ? (
            editMode ? (
              editedDetails.map((item, idx) => (
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
              ))
            ) : (
              infos.details.map((item, idx) => (
                <div key={idx} className="bg-white border rounded-md p-4 shadow-sm">
                  <p className="font-semibold">{item.question}</p>
                  <p className="text-sm mt-1">
                    {item.reponse}{' '}
                    <span className="text-gray-400 text-xs">({item.justification})</span>
                  </p>
                </div>
              ))
            )
          ) : (
            <p className="text-gray-500">Aucune analyse fournie.</p>
          )}
        </div>
  
        {editMode && (
          <div className="flex justify-end gap-4">
            <button onClick={handleEditSave} className="bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-700 transition">
              Enregistrer
            </button>
            <button
              onClick={() => {
                setEditMode(false)
                setEditedDetails(infos.details || [])
              }}
              className="bg-gray-400 text-white px-5 py-2 rounded hover:bg-gray-500 transition"
            >
              Annuler
            </button>
          </div>
        )}
  
        {/* Validation */}
        <div className="flex justify-center gap-4 pt-8">
          <button
            onClick={handleValidate}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <CheckCircle size={20} />
            Valider
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
