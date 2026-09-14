export default function ConditionsUtilisation() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-12 text-gray-800">
      <h1 className="text-3xl font-bold mb-6">Conditions Générales d’Utilisation</h1>

      <p className="mb-4">
        L&apos;application <strong>ConformIT</strong> est une plateforme destinée à analyser des documents administratifs, puis à relier les résultats à la conformité.
        Elle est accessible uniquement aux utilisateurs disposant d’un compte valide.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">1. Accès et inscription</h2>
      <p className="mb-4">
        L’accès à la plateforme nécessite la création d’un compte utilisateur. L’utilisateur s’engage à fournir des informations exactes lors de son inscription
        et à maintenir à jour ses informations personnelles.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">2. Utilisation du service</h2>
      <p className="mb-4">
        L’utilisateur s’engage à utiliser le service uniquement dans le cadre légal de ses activités. Toute tentative de contournement des limitations du plan d’abonnement, 
        d’accès non autorisé ou d’exploitation abusive de la plateforme est strictement interdite.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">3. Abonnements et paiements</h2>
      <p className="mb-4">
        L’accès à certaines fonctionnalités est soumis à un abonnement mensuel ou annuel. Les paiements sont gérés par Stripe. Les abonnements sont reconduits automatiquement,
        sauf résiliation de la part de l’utilisateur avant la date d’échéance.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">4. Données et confidentialité</h2>
      <p className="mb-4">
        Les données traitées restent confidentielles et ne sont ni revendues ni partagées. Chaque utilisateur est responsable de la sécurité de son compte.
        Pour plus de détails, consultez notre politique de confidentialité.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">5. Propriété intellectuelle</h2>
      <p className="mb-4">
        Tous les contenus, algorithmes et documents générés par la plateforme sont protégés. Toute reproduction, diffusion ou réutilisation sans autorisation est interdite.
      </p>

      <h2 className="text-xl font-semibold mt-6 mb-2">6. Responsabilité</h2>
      <p className="mb-4">
        Les résultats d’analyse sont fournis à titre indicatif. La société éditrice ne saurait être tenue responsable des décisions prises sur la base des données générées.
      </p>

      <p className="text-sm text-gray-500 mt-6">
        Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}
      </p>
    </div>
  );
}
