/**
 * Catalogue des types sélectionnables. Miroir du backend.
 * Le type est un contexte explicite, pas une déduction du moteur.
 */

export const DOCUMENT_TYPES = [
  { id: 'extrait_kbis', label: 'Kbis', uploadPrompt: 'Déposez votre Kbis.' },
  { id: 'comptes_sociaux', label: 'Comptes sociaux', uploadPrompt: 'Déposez vos comptes sociaux.' },
  { id: 'bilan_comptable', label: 'Bilan comptable', uploadPrompt: 'Déposez votre bilan comptable.' },
  { id: 'compte_resultat', label: 'Compte de résultat', uploadPrompt: 'Déposez votre compte de résultat.' },
  { id: 'liasse_fiscale', label: 'Liasse fiscale', uploadPrompt: 'Déposez votre liasse fiscale.' },
  { id: 'releve_bancaire', label: 'Relevé bancaire', uploadPrompt: 'Déposez votre relevé bancaire.' },
  { id: 'statuts', label: 'Statuts', uploadPrompt: 'Déposez vos statuts.' },
  { id: 'attestation_assurance', label: "Attestation d'assurance", uploadPrompt: "Déposez votre attestation d'assurance." },
]

export function labelForDocumentType(id) {
  return DOCUMENT_TYPES.find((item) => item.id === id)?.label || id
}

export function uploadPromptFor(id) {
  return DOCUMENT_TYPES.find((item) => item.id === id)?.uploadPrompt || 'Déposez votre document.'
}
