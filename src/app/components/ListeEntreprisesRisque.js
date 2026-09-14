'use client'

export default function ListeEntreprisesRisque() {
  const entreprises = [
    { entreprise: 'TechCorp', score_risque: 82 },
    { entreprise: 'EcoFinance', score_risque: 91 },

  ] 
  
  // Seuil à 2 : n'affiche que les entreprises à risque >= 2
  const entreprisesARisque = entreprises.filter(e => e.score_risque >= 2)
  return (
    <div className="bg-white p-4 rounded-xl shadow">
      <h2 className="text-lg font-semibold mb-2 text-center">Entreprises à risque</h2>
      {entreprisesARisque.length === 0 ? (
        <p className="text-center text-green-600">Aucune entreprise à risque détectée.</p>
      ) : (
        <ul className="list-disc pl-6 space-y-1">
          {entreprisesARisque.map((e, index) => (
            <li key={index}>
              <span className="font-medium">{e.entreprise}</span> — Score : <span className="text-red-600 font-bold">{e.score_risque}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}