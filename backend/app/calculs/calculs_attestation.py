"""
Calculs pour le document "Attestation d'assurance".
Normalisé sur 100 points : 10 questions, chaque question vaut 10 points maximum.
"""

from typing import Dict, Any, Optional
from .calculs_base import determiner_risque, is_positive

# Barème sur 100 points : 10 questions, chaque question vaut 10 points maximum
PENALTY_HIGH = 10  # Mauvaise réponse = 10 points de pénalité (sur 10)
PENALTY_MEDIUM = 5  # Mauvaise réponse = 5 points de pénalité (sur 10)
PENALTY_LOW = 0  # Bonne réponse = 0 point de pénalité
TOTAL_QUESTIONS = 10
MAX_SCORE = 100  # Score maximum = 100 points (10 questions * 10 points)


def _is_positive(value: Any) -> bool:
    """Détermine si une valeur est positive (Oui, True, présent, complet, etc.)."""
    if value is None:
        return False
    # Gérer les pourcentages
    text = str(value).strip().lower()
    if text.endswith("%"):
        try:
            return float(text[:-1].replace(",", ".")) > 0
        except ValueError:
            return False
    # Gérer les nombres
    try:
        return float(text.replace(",", ".")) > 0
    except ValueError:
        pass
    # Utiliser la fonction de base avec mots-clés supplémentaires
    return is_positive(value, additional_keywords=["ok", "positif", "positive", "complet", "présent", "present", "présente", "presente"])


def calculer_score_attestation(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule le score pour l'attestation d'assurance.
    
    Args:
        reponses: Dictionnaire avec les réponses aux questions (clés: 1-10)
    
    Returns:
        Dictionnaire avec le score, les détails, le niveau de risque et la précision
    """
    scores_detail: Dict[int, int] = {}
    reponses_calculees: Dict[int, str] = {}
    justifications_calculees: Dict[int, str] = {}
    total = 0
    questions_traitees = 0

    def enregistrer(question: int, condition: Optional[bool], justification: str, penalty_if_false: int = PENALTY_HIGH, penalty_if_true: int = PENALTY_LOW):
        nonlocal total, questions_traitees
        
        if condition is None:
            reponses_calculees[question] = "Non précisé"
            justifications_calculees[question] = justification or "Données indisponibles"
            penalty = PENALTY_HIGH
        elif condition:
            reponses_calculees[question] = "Oui"
            justifications_calculees[question] = justification
            penalty = penalty_if_true
            questions_traitees += 1
        else:
            reponses_calculees[question] = "Non"
            justifications_calculees[question] = justification
            penalty = penalty_if_false
            questions_traitees += 1

        scores_detail[question] = penalty
        total += penalty

    # Question 1 : Attestation à jour
    rep1 = _is_positive(reponses.get(1))
    enregistrer(1, rep1, "Attestation à jour (date de validité future)" if rep1 else "Attestation expirée", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 2 : Coordonnées de l'assuré correspondent
    rep2 = _is_positive(reponses.get(2))
    enregistrer(2, rep2, "Coordonnées de l'assuré correspondent" if rep2 else "Coordonnées de l'assuré ne correspondent pas", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 3 : Numéro de police présent
    rep3 = _is_positive(reponses.get(3))
    enregistrer(3, rep3, "Numéro de police présent et lisible" if rep3 else "Numéro de police absent ou illisible", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 4 : Compagnie d'assurance identifiée
    rep4 = _is_positive(reponses.get(4))
    enregistrer(4, rep4, "Compagnie d'assurance identifiée clairement" if rep4 else "Compagnie d'assurance non identifiée", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 5 : Garanties principales détaillées
    rep5 = _is_positive(reponses.get(5))
    enregistrer(5, rep5, "Garanties principales détaillées" if rep5 else "Garanties principales non détaillées", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 6 : Montants assurés spécifiés
    rep6 = _is_positive(reponses.get(6))
    enregistrer(6, rep6, "Montants assurés spécifiés" if rep6 else "Montants assurés non spécifiés", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 7 : Signature ou cachet officiel
    rep7 = _is_positive(reponses.get(7))
    enregistrer(7, rep7, "Signature ou cachet officiel présent" if rep7 else "Signature ou cachet officiel absent", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 8 : Couverture mentionne le domaine d'activité
    rep8 = _is_positive(reponses.get(8))
    enregistrer(8, rep8, "Couverture mentionne le domaine d'activité adéquat" if rep8 else "Couverture ne mentionne pas le domaine d'activité", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 9 : Exclusions ou limites précisées
    rep9 = _is_positive(reponses.get(9))
    enregistrer(9, rep9, "Exclusions ou limites de garantie précisées" if rep9 else "Exclusions ou limites de garantie non précisées", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 10 : Clause de renouvellement ou reconduction
    rep10 = _is_positive(reponses.get(10))
    enregistrer(10, rep10, "Clause de renouvellement ou reconduction mentionnée" if rep10 else "Clause de renouvellement ou reconduction absente", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Calcul de la précision
    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 1, 2, 4, 5, 6, 7, 8, 9, 10 = 9 questions
    # Questions avec PENALTY_MEDIUM (5 points) : 3 = 1 question
    # Score maximum théorique = 9 * 10 + 1 * 5 = 90 + 5 = 95 points
    score_max_theorique = (9 * PENALTY_HIGH) + (1 * PENALTY_MEDIUM)  # 95 points
    
    # Normaliser sur 100 points
    score_brut = total
    if score_max_theorique == 0:
        score_total = 100
    else:
        score_normalise = round((score_brut / score_max_theorique) * 100) if score_brut > 0 else 0
        score_total = min(max(score_normalise, 0), MAX_SCORE)
    
    score_max = MAX_SCORE
    risque = determiner_risque(score_total)

    return {
        "score_total": score_total,
        "score_max": score_max,
        "scores_detail": scores_detail,
        "precision": precision,
        "reponses": reponses_calculees,
        "justifications": justifications_calculees,
        "niveau_risque": risque,
        "risque": risque,
    }

