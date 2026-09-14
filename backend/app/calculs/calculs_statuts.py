"""
Calculs pour le document "Statuts".
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
    """Détermine si une valeur est positive (Oui, True, etc.)."""
    return is_positive(value, additional_keywords=["presence", "présent", "positif", "positive"])


def calculer_score_statuts(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule le score pour les statuts.
    
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
            penalty = PENALTY_HIGH  # Pénalité maximale si données manquantes
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

    # Question 1 : Répartition du capital équilibrée
    rep1 = _is_positive(reponses.get(1))
    enregistrer(1, rep1, "Répartition du capital équilibrée" if rep1 else "Répartition du capital déséquilibrée", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 2 : Clauses d'agrément
    rep2 = _is_positive(reponses.get(2))
    enregistrer(2, rep2, "Clauses d'agrément présentes" if rep2 else "Clauses d'agrément absentes", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 3 : Apports en numéraire > 50%
    rep3 = _is_positive(reponses.get(3))
    enregistrer(3, rep3, "Apports en numéraire > 50%" if rep3 else "Apports en numéraire < 50%", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 4 : Clauses de préemption
    rep4 = _is_positive(reponses.get(4))
    enregistrer(4, rep4, "Clauses de préemption présentes" if rep4 else "Clauses de préemption absentes", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 5 : Pouvoirs du gérant définis
    rep5 = _is_positive(reponses.get(5))
    enregistrer(5, rep5, "Pouvoirs du gérant clairement définis" if rep5 else "Pouvoirs du gérant non définis", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 6 : Durée de vie > 50 ans
    rep6 = _is_positive(reponses.get(6))
    enregistrer(6, rep6, "Durée de vie > 50 ans" if rep6 else "Durée de vie < 50 ans", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 7 : Modifications fréquentes (RISQUE)
    rep7 = _is_positive(reponses.get(7))
    enregistrer(7, rep7, "Modifications fréquentes (> 3 fois)" if rep7 else "Modifications stables", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 8 : Clauses de garantie de passif
    rep8 = _is_positive(reponses.get(8))
    enregistrer(8, rep8, "Clauses de garantie de passif présentes" if rep8 else "Clauses de garantie de passif absentes", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 9 : Modalités de décision claires
    rep9 = _is_positive(reponses.get(9))
    enregistrer(9, rep9, "Modalités de décision claires" if rep9 else "Modalités de décision floues", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 10 : Pactes d'actionnaires restrictifs
    rep10 = _is_positive(reponses.get(10))
    enregistrer(10, rep10, "Pactes d'actionnaires restrictifs présents" if rep10 else "Pactes d'actionnaires restrictifs absents", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Calcul de la précision
    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 2, 3, 4, 5, 6, 8, 9 = 7 questions
    # Questions avec PENALTY_MEDIUM (5 points) : 1, 10 = 2 questions
    # Question 7 : PENALTY_LOW si False (0), PENALTY_HIGH si True (10) = 1 question (max 10)
    # Score maximum théorique = 7 * 10 + 2 * 5 + 1 * 10 = 70 + 10 + 10 = 90 points
    score_max_theorique = (7 * PENALTY_HIGH) + (2 * PENALTY_MEDIUM) + (1 * PENALTY_HIGH)  # 90 points
    
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

