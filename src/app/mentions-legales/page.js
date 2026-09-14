export default function MentionsLegales() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-12 text-gray-800">
      <h1 className="text-3xl font-bold mb-6">Mentions légales</h1>

      <p className="mb-4">
        Ce site est édité par : <strong>SB Technologies</strong>, société spécialisée dans l’analyse automatisée de documents administratifs.
      </p>

      <p className="mb-4">
        Siège social : 123 Rue de l&apos;Analyse, 97150 Saint-Martin<br />
        Email : contact@sb-tech.com<br />
        SIRET : 123 456 789 00012<br />
        Directeur de la publication : Sylvio M.
      </p>

      <p className="mb-4">
        Hébergeur : Vercel Inc. – 440 N Barranca Ave #4133, Covina, CA 91723, USA
      </p>

      <p className="text-sm text-gray-500 mt-6">
        Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}
      </p>
    </div>
  );
}
