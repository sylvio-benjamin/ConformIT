"""
Calculs pour le document "Relevé bancaire".
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
    """Détermine si une valeur est positive (Oui, True, stable, etc.)."""
    return is_positive(value, additional_keywords=["positif", "positive", "stable", "regular", "récurrent", "recurrent"])


def calculer_score_releve(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule le score pour le relevé bancaire.
    
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

    # Question 1 : Solde moyen positif
    rep1 = _is_positive(reponses.get(1))
    enregistrer(1, rep1, "Solde moyen positif" if rep1 else "Solde moyen négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 2 : Incidents de paiement (RISQUE)
    rep2 = _is_positive(reponses.get(2))
    enregistrer(2, rep2, "Incidents de paiement détectés" if rep2 else "Aucun incident de paiement", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 3 : Découvert utilisé régulièrement (RISQUE)
    rep3 = _is_positive(reponses.get(3))
    enregistrer(3, rep3, "Découvert utilisé régulièrement" if rep3 else "Découvert peu utilisé", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 4 : Agios pour dépassement (RISQUE)
    rep4 = _is_positive(reponses.get(4))
    enregistrer(4, rep4, "Agios pour dépassement détectés" if rep4 else "Aucun agios pour dépassement", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 5 : Rejets de prélèvements
    rep5 = _is_positive(reponses.get(5))
    enregistrer(5, rep5, "Aucun rejet de prélèvement" if rep5 else "Rejets de prélèvements détectés", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 6 : Encaissements réguliers
    rep6 = _is_positive(reponses.get(6))
    enregistrer(6, rep6, "Encaissements réguliers" if rep6 else "Encaissements irréguliers", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 7 : Décaissements sains
    rep7 = _is_positive(reponses.get(7))
    enregistrer(7, rep7, "Décaissements sains" if rep7 else "Décaissements problématiques", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 8 : Virements urgents répétés (RISQUE)
    rep8 = _is_positive(reponses.get(8))
    enregistrer(8, rep8, "Virements urgents répétés détectés" if rep8 else "Aucun virement urgent répété", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 9 : Variation stable
    rep9 = _is_positive(reponses.get(9))
    enregistrer(9, rep9, "Variation du solde stable" if rep9 else "Variation du solde instable", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 10 : Opérations suspectes (RISQUE)
    rep10 = _is_positive(reponses.get(10))
    enregistrer(10, rep10, "Opérations suspectes détectées" if rep10 else "Aucune opération suspecte", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Calcul de la précision
    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Le score total est déjà sur 100 points (10 questions * 10 points max = 100 points max)
    score_max_theorique = TOTAL_QUESTIONS * PENALTY_HIGH  # 100
    score_brut = total
    score_normalise = round((score_brut / score_max_theorique) * 100) if score_brut > 0 else 0
    score_total = min(score_normalise, MAX_SCORE)
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

