"""
Calculs pour le document "Compte de résultat".
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
    """Détermine si une valeur est positive (Oui, True, supérieur, augmenté, etc.)."""
    return is_positive(value, additional_keywords=["positif", "positive", "supérieur", "sup", "superieur", "augmenté", "augmente"])


def calculer_score_compte_resultat(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule le score pour le compte de résultat.
    
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

    # Question 1 : Résultat net positif
    rep1 = _is_positive(reponses.get(1))
    enregistrer(1, rep1, "Résultat net positif" if rep1 else "Résultat net négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 2 : Marge brute > 20%
    rep2 = _is_positive(reponses.get(2))
    enregistrer(2, rep2, "Marge brute > 20%" if rep2 else "Marge brute < 20%", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 3 : Résultat d'exploitation (EBIT) positif
    rep3 = _is_positive(reponses.get(3))
    enregistrer(3, rep3, "Résultat d'exploitation (EBIT) positif" if rep3 else "Résultat d'exploitation (EBIT) négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 4 : Marge nette > 5%
    rep4 = _is_positive(reponses.get(4))
    enregistrer(4, rep4, "Marge nette > 5%" if rep4 else "Marge nette < 5%", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 5 : EBITDA positif
    rep5 = _is_positive(reponses.get(5))
    enregistrer(5, rep5, "EBITDA positif" if rep5 else "EBITDA négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 6 : Croissance du CA sur 3 ans
    rep6 = _is_positive(reponses.get(6))
    enregistrer(6, rep6, "Croissance du CA sur 3 ans" if rep6 else "Pas de croissance du CA", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 7 : Charges de personnel < 60% du CA
    rep7 = _is_positive(reponses.get(7))
    enregistrer(7, rep7, "Charges de personnel < 60% du CA" if rep7 else "Charges de personnel > 60% du CA", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 8 : Charges financières < 5% du CA
    rep8 = _is_positive(reponses.get(8))
    enregistrer(8, rep8, "Charges financières < 5% du CA" if rep8 else "Charges financières > 5% du CA", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 9 : Résultat exceptionnel impact négatif > 20% (RISQUE)
    rep9 = _is_positive(reponses.get(9))
    enregistrer(9, rep9, "Résultat exceptionnel impact négatif > 20%" if rep9 else "Résultat exceptionnel impact normal", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 10 : Capacité d'autofinancement (CAF) positive
    rep10 = _is_positive(reponses.get(10))
    enregistrer(10, rep10, "Capacité d'autofinancement (CAF) positive" if rep10 else "Capacité d'autofinancement (CAF) négative", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Calcul de la précision
    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 1, 2, 3, 4, 5, 10 = 6 questions
    # Questions avec PENALTY_MEDIUM (5 points) : 6, 7, 8 = 3 questions
    # Question 9 : PENALTY_LOW si False (0), PENALTY_HIGH si True (10) = 1 question (max 10)
    # Score maximum théorique = 6 * 10 + 3 * 5 + 1 * 10 = 60 + 15 + 10 = 85 points
    score_max_theorique = (6 * PENALTY_HIGH) + (3 * PENALTY_MEDIUM) + (1 * PENALTY_HIGH)  # 85 points
    
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

