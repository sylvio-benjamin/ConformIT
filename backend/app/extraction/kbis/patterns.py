"""Motifs Kbis : détection, contexte, négation. Pas de scoring."""

from __future__ import annotations

FORME_ENUM = ("SASU", "SAS", "SARL", "SA", "EURL", "EI", "SNC", "SCI")

FORME_LABELS = (
    ("societe par actions simplifiee unipersonnelle", "SASU"),
    ("sasu", "SASU"),
    ("societe par actions simplifiee", "SAS"),
    ("entreprise unipersonnelle a responsabilite limitee", "EURL"),
    ("societe a responsabilite limitee", "SARL"),
    ("societe anonyme", "SA"),
    ("entreprise individuelle", "EI"),
    ("societe en nom collectif", "SNC"),
    ("societe civile immobiliere", "SCI"),
)

FACT_PATTERNS = {
    "siren": {
        "type": "identifiant",
        "labels": [r"\bsiren\b", r"\bsiret\b", r"\br\.?\s*c\.?\s*s\.?\b", r"immatriculation"],
        "value": r"(\d{3}[\s.\-']?\d{3}[\s.\-']?\d{3})",
        "negations": [
            r"n['’]est pas immatricul",
            r"non immatricul",
            r"pas de (siren|rcs|numero)",
            r"sans (siren|rcs)",
        ],
    },
    "mention_rcs": {
        "type": "booleen",
        "labels": [
            r"extrait k\s*bis",
            r"registre du commerce",
            r"\br\.?\s*c\.?\s*s\.?\b",
            r"immatriculation au rcs",
        ],
    },
    "denomination": {
        "type": "texte",
        "labels": [r"denomination(?:\s+sociale)?", r"raison sociale"],
        "value": r"[:\-]\s*(.+)",
    },
    "forme_juridique": {
        "type": "enum",
        "labels": [r"forme juridique", r"forme de la societe"],
        "values": FORME_LABELS,
    },
    "capital_social": {
        "type": "montant",
        "labels": [r"capital social"],
        "value": r"([\d\s\u00a0.,]+)\s*(?:euros?|eur|€)?",
    },
    "capital_variable": {
        "type": "booleen",
        "labels": [r"capital (social )?(variable|variab)", r"a capital variable"],
    },
    "date_immatriculation": {
        "type": "date",
        "labels": [
            r"date d['’]immatriculation",
            r"immatriculation au rcs",
            r"immatriculee? le",
        ],
    },
    "date_debut_activite": {
        "type": "date",
        "labels": [
            r"date de debut d['’]activite",
            r"commencement d['’]activite",
            r"debut d['’]activite",
        ],
    },
    "etat_activite": {
        "type": "enum",
        "labels": [r"etat de l['’]activite", r"situation de l['’]activite"],
        "actif": [
            r"\ben activite\b",
            r"activite en cours",
            r"entreprise en activite",
        ],
        "inactif": [
            r"\bradiee?\b",
            r"\bcessation\b",
            r"\bdissoute?\b",
            r"\bliquidation\b",
            r"activite cessee",
            r"sans activite",
        ],
    },
    "duree_societe": {
        "type": "duree",
        "labels": [r"duree(?:\s+de\s+la\s+personne\s+morale)?"],
        "value": r"(\d{1,3})\s*ans",
        "indeterminee": [r"duree\s+indeterminee", r"pour une duree indeterminee"],
    },
    "duree_nature": {
        "type": "enum",
        "labels": [r"duree(?:\s+de\s+la\s+personne\s+morale)?"],
    },
    "commissaire_comptes": {
        "type": "booleen",
        "labels": [
            r"commissaire aux comptes(?:\s+titulaire)?",
            r"\bcac\b",
        ],
        "negations": [r"neant", r"aucun", r"non designe", r"non nomme", r"pas de commissaire"],
    },
    "nombre_etablissements": {
        "type": "entier",
        "labels": [r"nombre d['’ ]etablissements?"],
        "value": r"(\d+)",
        "secondaire": r"etablissement secondaire",
        "principal": r"etablissement principal",
    },
    "etablissement_principal": {
        "type": "adresse",
        "labels": [r"etablissement principal"],
    },
    "nationalite": {
        "type": "enum",
        "labels": [r"nationalite"],
        "value": r"[:\-]?\s*([a-z\-]+)",
    },
    "adresse_siege": {
        "type": "adresse",
        "labels": [r"adresse du siege", r"siege social"],
    },
    "transfert_siege": {
        "type": "booleen",
        "labels": [r"transfert de siege", r"ancien siege", r"changement d['’]adresse"],
    },
    "adresse_dirigeant": {
        "type": "adresse",
        "labels": [r"demeurant", r"domicile", r"adresse personnelle"],
    },
    "dirigeants_count": {
        "type": "entier",
        "labels": [
            r"\bdirigeant(?:s)?\b",
            r"representant(?:s)? legal(?:aux)?",
            r"\bpresident\b",
            r"\bgerant(?:e)?\b",
            r"directeur general",
        ],
    },
    "dirigeant_fonction": {
        "type": "texte",
        "labels": [
            r"\bpresident\b",
            r"\bgerant(?:e)?\b",
            r"directeur general",
            r"representant legal",
            r"qualite\s*[:\-]",
        ],
    },
    "mention_procedure": {
        "type": "booleen",
        "labels": [
            r"\bradiation\b",
            r"\bdissolution\b",
            r"procedure collective",
            r"redressement judiciaire",
            r"liquidation judiciaire",
            r"sauvegarde judiciaire",
        ],
    },
}

# Uniquement les faits qu'un Kbis doit porter. Jamais l'historique de siège (Q16).
# Une preuve absente reste INCONNU : pas de fallback « pour aider ».
EXPECTED_FACTS = ("siren", "forme_juridique", "capital_social")
AMBIGUOUS_FACTS = ("transfert_siege", "nationalite", "mention_procedure")

FOREIGN_COUNTRIES = (
    "allemagne", "belgique", "suisse", "italie", "espagne", "portugal",
    "royaume-uni", "united kingdom", "angleterre", "luxembourg", "pays-bas",
    "etats-unis", "usa", "maroc", "algerie", "tunisie", "chine", "canada",
)
