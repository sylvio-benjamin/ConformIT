"""
Calculs pour le document "Liasse fiscale".
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
    """Détermine si une valeur est positive (Oui, True, supérieur, etc.)."""
    return is_positive(value, additional_keywords=["positif", "positive", "supérieur", "sup", "superieur"])


def calculer_score_liasse(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule le score pour la liasse fiscale.
    
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

    # Question 1 : Flux opérationnel positif
    rep1 = _is_positive(reponses.get(1))
    enregistrer(1, rep1, "Flux opérationnel positif" if rep1 else "Flux opérationnel négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 2 : Créances douteuses < 5% (inverse : si créances douteuses > 5%, c'est un risque)
    rep2 = _is_positive(reponses.get(2))
    enregistrer(2, not rep2, "Créances douteuses < 5%" if not rep2 else "Créances douteuses > 5%", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 3 : Rotation des stocks rapide
    rep3 = _is_positive(reponses.get(3))
    enregistrer(3, rep3, "Rotation des stocks rapide (< 90 jours)" if rep3 else "Rotation des stocks lente", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 4 : Immobilisations amorties
    rep4 = _is_positive(reponses.get(4))
    enregistrer(4, rep4, "Immobilisations correctement amorties" if rep4 else "Immobilisations non amorties", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 5 : Provisions importantes (RISQUE)
    rep5 = _is_positive(reponses.get(5))
    enregistrer(5, rep5, "Provisions importantes détectées" if rep5 else "Provisions normales", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 6 : Produits exceptionnels importants (RISQUE)
    rep6 = _is_positive(reponses.get(6))
    enregistrer(6, rep6, "Produits exceptionnels importants" if rep6 else "Produits exceptionnels normaux", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_HIGH)

    # Question 7 : Charges à payer cohérentes
    rep7 = _is_positive(reponses.get(7))
    enregistrer(7, rep7, "Charges à payer cohérentes" if rep7 else "Charges à payer incohérentes", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 8 : Produits constatés d'avance significatifs
    rep8 = _is_positive(reponses.get(8))
    enregistrer(8, rep8, "Produits constatés d'avance significatifs" if rep8 else "Produits constatés d'avance normaux", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Question 9 : Report à nouveau positif
    rep9 = _is_positive(reponses.get(9))
    enregistrer(9, rep9, "Report à nouveau positif" if rep9 else "Report à nouveau négatif", penalty_if_false=PENALTY_HIGH, penalty_if_true=PENALTY_LOW)

    # Question 10 : Subventions < 20% du résultat
    rep10 = _is_positive(reponses.get(10))
    enregistrer(10, rep10, "Subventions < 20% du résultat" if rep10 else "Subventions > 20% du résultat", penalty_if_false=PENALTY_MEDIUM, penalty_if_true=PENALTY_LOW)

    # Calcul de la précision
    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 1, 2, 3, 9 = 4 questions
    # Questions avec PENALTY_MEDIUM (5 points) : 4, 7, 8, 10 = 4 questions
    # Questions avec PENALTY_LOW si False et PENALTY_HIGH si True : 5, 6 = 2 questions (max 10 chacun)
    # Score maximum théorique = 4 * 10 + 4 * 5 + 2 * 10 = 40 + 20 + 20 = 80 points
    score_max_theorique = (4 * PENALTY_HIGH) + (4 * PENALTY_MEDIUM) + (2 * PENALTY_HIGH)  # 80 points
    
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
