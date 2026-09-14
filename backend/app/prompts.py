"""
Module contenant les prompts Groq optimisés pour chaque type de document.
Chaque type de document a des instructions spécifiques pour améliorer la qualité des réponses.
"""

from typing import Dict, Optional


# ===========================================================
# PROMPTS SPÉCIFIQUES PAR TYPE DE DOCUMENT
# ===========================================================

def get_prompt_for_question(document_type: str, question: str, texte_document: str, question_num: int) -> str:
    """
    Génère un prompt optimisé pour une question spécifique selon le type de document.
    
    Args:
        document_type: Type de document (extrait_kbis, compte_resultat, liasse_fiscale, etc.)
        question: Question à poser
        texte_document: Texte du document (limité à 3000 caractères)
        question_num: Numéro de la question
    
    Returns:
        Prompt optimisé pour Groq
    """
    prompts_specifiques = {
        "extrait_kbis": get_prompt_kbis,
        "compte_resultat": get_prompt_compte_resultat,
        "liasse_fiscale": get_prompt_liasse_fiscale,
        "releve_bancaire": get_prompt_releve_bancaire,
        "statuts": get_prompt_statuts,
        "attestation_assurance": get_prompt_attestation,
    }
    
    generateur = prompts_specifiques.get(document_type, get_prompt_generique)
    return generateur(question, texte_document, question_num)


def get_prompt_kbis(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions Kbis.
    Les questions Kbis portent sur des informations légales et administratives.
    """
    context_specifique = ""
    
    # Instructions spécifiques selon la question
    if question_num == 2:  # RCS
        context_specifique = """
CONTEXTE : Cherche un numéro RCS (Registre du Commerce et des Sociétés) à 9 chiffres.
Le RCS apparaît généralement sous la forme "RCS Paris 123 456 789" ou "RCS : 123456789".
Réponds UNIQUEMENT par "Oui" si tu trouves un numéro RCS, sinon "Non".
"""
    elif question_num == 3:  # Forme juridique
        context_specifique = """
CONTEXTE : Cherche la forme juridique de l'entreprise (SAS, SARL, SA, EURL, etc.).
Elle apparaît généralement dans la section "Forme juridique" ou "Nature".
Réponds par la forme juridique exacte (ex: "SAS", "SARL", "SA", "EURL", "EI", "SNC").
"""
    elif question_num == 4:  # Capital social
        context_specifique = """
CONTEXTE : Cherche le capital social de l'entreprise (montant en euros).
Il apparaît généralement dans la section "Capital social" ou "Capital".
Réponds par le montant en euros (ex: "50000", "100000", "750000") sans le symbole €.
"""
    elif question_num == 5:  # Adresse stable
        context_specifique = """
CONTEXTE : Cherche depuis combien de temps l'entreprise est à cette adresse.
Vérifie si l'adresse du siège social a changé récemment ou est stable depuis plusieurs années.
Réponds par le nombre d'années (ex: "3 ans", "5 ans", "10 ans") ou "Moins de 1 an".
"""
    elif question_num == 6:  # Ancienneté
        context_specifique = """
CONTEXTE : Cherche la date d'immatriculation de l'entreprise.
Calcule depuis combien de temps l'entreprise est immatriculée.
Réponds par le nombre d'années (ex: "5 ans", "10 ans") ou "Moins de 3 ans".
"""
    elif question_num == 7:  # Commissaire aux comptes
        context_specifique = """
CONTEXTE : Cherche si l'entreprise a un commissaire aux comptes.
Vérifie dans les mentions légales ou les informations sur les organes de contrôle.
Réponds UNIQUEMENT par "Oui" ou "Non".
"""
    elif question_num == 8:  # Établissements
        context_specifique = """
CONTEXTE : Cherche si l'entreprise possède plusieurs établissements.
Vérifie le nombre d'établissements secondaires ou succursales.
Réponds par "Grande entreprise" (plusieurs établissements), "Moyenne entreprise" (1-2 établissements) ou "Petite entreprise" (1 seul établissement).
"""
    elif question_num == 9:  # Durée de vie
        context_specifique = """
CONTEXTE : Cherche la durée de vie prévue de l'entreprise.
Vérifie dans les statuts ou les informations sur la durée de la société.
Réponds par "Oui" si la durée est supérieure à 10 ans, sinon "Non".
"""
    elif question_num == 10:  # Date d'activité
        context_specifique = """
CONTEXTE : Cherche la date de début d'activité et compare-la à la date d'immatriculation.
Vérifie si les deux dates sont proches (moins de 1 an d'écart).
Réponds par le nombre d'années d'écart (ex: "1 an", "2 ans", "3 ans") ou "Proche" si moins de 1 an.
"""
    elif question_num == 11:  # Nationalité dirigeants
        context_specifique = """
CONTEXTE : Cherche la nationalité des dirigeants de l'entreprise.
Vérifie si les dirigeants sont de nationalité française ou étrangère.
Réponds UNIQUEMENT par "Oui" si au moins un dirigeant est de nationalité étrangère, sinon "Non".
"""
    elif question_num == 12:  # Adresse dirigeants
        context_specifique = """
CONTEXTE : Cherche l'adresse personnelle des dirigeants.
Vérifie si les dirigeants ont une adresse en France ou hors de France.
Réponds UNIQUEMENT par "Oui" si au moins un dirigeant a une adresse hors de France, sinon "Non".
"""
    
    return f"""Analyse ce document Kbis (extrait du registre du commerce) et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document contient des informations légales et administratives sur une entreprise
- Cherche les informations dans les sections : "Dénomination", "Forme juridique", "Capital social", "Siège social", "Dirigeants"
- Réponds de manière concise et précise
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante ou non trouvée, réponds "Non précisé"
- Pour les questions binaires, réponds UNIQUEMENT par "Oui" ou "Non"
- Pour les questions numériques, réponds UNIQUEMENT par le nombre (sans unité sauf indication contraire)

TA RÉPONSE :"""


def get_prompt_compte_resultat(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions sur le compte de résultat.
    Les questions portent sur la rentabilité et la performance financière.
    """
    context_specifique = """
CONTEXTE : Ce document est un compte de résultat (état des résultats).
Il contient les produits (chiffre d'affaires, autres produits) et les charges (achats, personnel, impôts, etc.).
Le résultat net est la différence entre les produits et les charges.
"""
    
    return f"""Analyse ce compte de résultat et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document contient des informations financières sur la performance de l'entreprise
- Cherche les valeurs dans les sections : "Chiffre d'affaires", "Achats", "Charges de personnel", "Résultat net", "Résultat d'exploitation", "EBITDA"
- Pour les questions sur les ratios (marge brute, marge nette), calcule-les si nécessaire
- Réponds par "Oui" si la condition est vérifiée, "Non" si elle ne l'est pas, ou une valeur chiffrée si demandé
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""


def get_prompt_liasse_fiscale(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions sur la liasse fiscale.
    Les questions portent sur les tableaux fiscaux et les informations comptables détaillées.
    """
    context_specifique = """
CONTEXTE : Ce document est une liasse fiscale (déclarations fiscales).
Il contient des tableaux comptables détaillés : bilan, compte de résultat, annexe, tableaux fiscaux.
Les informations sont organisées en tableaux numérotés (2050, 2051, 2052, etc.).
"""
    
    return f"""Analyse cette liasse fiscale et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document contient des tableaux fiscaux et comptables détaillés
- Cherche les valeurs dans les tableaux : "Tableau 2050" (bilan), "Tableau 2051" (compte de résultat), "Tableau 2052" (annexe)
- Pour les questions sur les ratios (rotation des stocks, amortissements, provisions), calcule-les si nécessaire
- Réponds par "Oui" si la condition est vérifiée, "Non" si elle ne l'est pas, ou une valeur chiffrée si demandé
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""


def get_prompt_releve_bancaire(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions sur le relevé bancaire.
    Les questions portent sur les mouvements bancaires et la gestion de trésorerie.
    """
    context_specifique = """
CONTEXTE : Ce document est un relevé bancaire (extrait de compte).
Il contient les mouvements bancaires : crédits (encaissements), débits (décaissements), solde.
Les mouvements incluent : virements, prélèvements, chèques, agios, rejets, etc.
"""
    
    return f"""Analyse ce relevé bancaire et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document contient les mouvements bancaires de l'entreprise
- Analyse les mouvements : solde moyen, incidents de paiement (rejets, impayés), utilisation du découvert, agios, rejets de prélèvements
- Pour les questions sur la régularité, vérifie la fréquence et la cohérence des mouvements
- Réponds par "Oui" si la condition est vérifiée, "Non" si elle ne l'est pas, ou une valeur chiffrée si demandé
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""


def get_prompt_statuts(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions sur les statuts.
    Les questions portent sur la structure juridique et les clauses statutaires.
    """
    context_specifique = """
CONTEXTE : Ce document contient les statuts de l'entreprise (acte constitutif).
Il définit : le capital social, la répartition du capital, les pouvoirs des dirigeants, les clauses statutaires, la durée de vie, etc.
"""
    
    return f"""Analyse ces statuts et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document contient les statuts de l'entreprise (acte constitutif)
- Cherche les informations dans les sections : "Capital social", "Répartition du capital", "Pouvoirs du gérant", "Clauses statutaires", "Durée de vie"
- Pour les questions sur les clauses (agrément, préemption, garantie de passif), vérifie leur présence dans le document
- Réponds par "Oui" si la condition est vérifiée, "Non" si elle ne l'est pas, ou une valeur chiffrée si demandé
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""


def get_prompt_attestation(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt optimisé pour les questions sur l'attestation d'assurance.
    Les questions portent sur les garanties et la couverture d'assurance.
    """
    context_specifique = """
CONTEXTE : Ce document est une attestation d'assurance.
Il contient : les coordonnées de l'assuré, le numéro de police, la compagnie d'assurance, les garanties, les montants assurés, les exclusions, la date de validité.
"""
    
    return f"""Analyse cette attestation d'assurance et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}
{context_specifique}

INSTRUCTIONS SPÉCIFIQUES :
- Ce document est une attestation d'assurance
- Cherche les informations dans les sections : "Assuré", "Numéro de police", "Compagnie d'assurance", "Garanties", "Montants assurés", "Exclusions", "Date de validité"
- Pour les questions sur la validité, vérifie la date d'expiration (doit être dans le futur)
- Pour les questions sur la correspondance, compare les coordonnées de l'assuré avec celles de l'entreprise analysée
- Réponds par "Oui" si la condition est vérifiée, "Non" si elle ne l'est pas, ou une valeur chiffrée si demandé
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""


def get_prompt_generique(question: str, texte_document: str, question_num: int) -> str:
    """
    Prompt générique pour les types de documents non spécifiés.
    """
    return f"""Analyse ce document et réponds à la question.

DOCUMENT :
{texte_document[:3000]}

QUESTION {question_num} : {question}

INSTRUCTIONS :
- Réponds clairement (Oui / Non ou une valeur chiffrée)
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non précisé"

TA RÉPONSE :"""

