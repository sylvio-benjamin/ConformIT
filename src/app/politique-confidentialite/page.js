export default function PolitiqueConfidentialite() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-12 text-gray-800">
      <h1 className="text-3xl font-bold mb-6">Politique de confidentialité</h1>

      <p className="mb-4">
        ConformIT respecte la confidentialité de vos données. Aucune information personnelle ne sera vendue ou partagée avec des tiers sans votre consentement.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">Collecte des données</h2>
      <p className="mb-4">
        Lors de la création de compte ou l’utilisation de notre service, nous collectons uniquement les données nécessaires à la fourniture du service : nom, email, identifiant Firebase, historique d’analyse.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">Utilisation des données</h2>
      <p className="mb-4">
        Les données sont utilisées pour générer des rapports, gérer les abonnements et améliorer le service. Elles ne sont accessibles qu’aux administrateurs autorisés.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">Sécurité</h2>
      <p className="mb-4">
        Les données sont stockées dans Firebase (Google) avec authentification sécurisée. Toutes les communications sont chiffrées via HTTPS.
      </p>

      <p className="text-sm text-gray-500 mt-6">
        Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}
      </p>
    </div>
  );
}
