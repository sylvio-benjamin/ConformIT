"""
Calculs génériques pour les types de documents sans calculs spécifiques.
Utilisé pour les documents comme "autorisation_commerciale", "type_inconnu", etc.
"""

from typing import Dict, Any
from .calculs_base import determiner_risque, calculer_precision, NiveauRisque

# Note: Les imports relatifs utilisent .calculs_base car nous sommes dans le dossier calculs/

MAX_SCORE = 100  # Score maximum = 100 points
TOTAL_QUESTIONS = 10  # Par défaut, 10 questions


def calculer_score_generique(reponses: Dict[int, Any]) -> Dict[str, Any]:
    """
    Calcule un score générique pour un type de document sans calculs spécifiques.
    
    Args:
        reponses: Dictionnaire avec les réponses aux questions
    
    Returns:
        Dictionnaire avec le score, les détails, le niveau de risque et la précision
    """
    # Pour les documents génériques, on retourne un score par défaut (50 = Medium)
    score_total = 50
    niveau_risque = determiner_risque(score_total)
    precision = calculer_precision(reponses, TOTAL_QUESTIONS)
    
    scores_detail: Dict[int, int] = {}
    for question_num, reponse in reponses.items():
        # Score par défaut : 5 points par question (Medium)
        scores_detail[question_num] = 5
    
    return {
        "score_total": score_total,
        "score_max": MAX_SCORE,
        "scores_detail": scores_detail,
        "precision": precision,
        "reponses": {k: str(v) for k, v in reponses.items()},
        "justifications": {k: "Calcul générique" for k in reponses.keys()},
        "niveau_risque": niveau_risque.value if isinstance(niveau_risque, NiveauRisque) else niveau_risque,
        "risque": niveau_risque.value if isinstance(niveau_risque, NiveauRisque) else niveau_risque,
    }

