"""
Module de base pour les calculs de scores.
Contient les fonctions communes à tous les types de documents.
"""

from typing import Dict, Any, Optional
from enum import Enum


class NiveauRisque(str, Enum):
    """Niveaux de risque possibles."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


def determiner_risque(score_total: int) -> str:
    """
    Détermine le niveau de risque à partir du score.
    
    Args:
        score_total: Score total (0-100)
    
    Returns:
        Niveau de risque (Low, Medium, High, Critical)
    """
    if score_total <= 30:
        return NiveauRisque.LOW.value
    elif score_total <= 60:
        return NiveauRisque.MEDIUM.value
    elif score_total <= 80:
        return NiveauRisque.HIGH.value
    else:
        return NiveauRisque.CRITICAL.value


def is_positive(value: Any, additional_keywords: Optional[list] = None) -> bool:
    """
    Détermine si une valeur est positive (Oui, True, etc.).
    
    Cette fonction détecte les mots-clés positifs même s'ils sont dans une phrase plus longue.
    Par exemple, "Oui, l'entreprise est bénéficiaire" sera détecté comme positif.
    
    Args:
        value: Valeur à vérifier
        additional_keywords: Liste de mots-clés supplémentaires à accepter (peut contenir des strings ou des listes)
    
    Returns:
        True si la valeur est positive, False sinon
    """
    if value is None:
        return False
    
    if isinstance(value, (int, float)):
        return value > 0
    
    text = str(value).strip().lower()
    
    # Mots-clés de base (recherche dans le texte, pas correspondance exacte)
    base_keywords = [
        "oui", "yes", "true", "ok", "positif", "positive",
        "supérieur", "superieur", "sup", "augmenté", "augmente",
        "présent", "present", "présente", "presente",
        "complet", "détaillé", "detaille", "spécifié", "specifie",
        "stable", "régulier", "regulier", "récurrent", "recurrent",
        "équilibré", "equilibre", "claire", "défini", "defini",
    ]
    
    # Mots-clés supplémentaires (normaliser en liste de strings)
    if additional_keywords:
        for kw in additional_keywords:
            if isinstance(kw, str):
                base_keywords.append(kw.lower())
            elif isinstance(kw, list):
                base_keywords.extend([k.lower() for k in kw if isinstance(k, str)])
    
    # Chercher si un des mots-clés est présent dans le texte
    # Vérifier d'abord la correspondance exacte (pour compatibilité)
    if text in base_keywords:
        return True
    
    # Ensuite, chercher les mots-clés dans le texte (même dans une phrase)
    for keyword in base_keywords:
        # Chercher le mot-clé comme mot entier (pas comme partie d'un autre mot)
        # Utiliser des limites de mots (\b) si possible
        import re
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
        # Fallback : chercher simplement dans le texte
        if keyword in text:
            return True
    
    # Vérifier les mots-clés négatifs (pour éviter les faux positifs)
    negative_keywords = [
        "non", "no", "false", "négatif", "negatif", "negative",
        "absent", "manquant", "indisponible", "erreur",
        "inférieur", "inferieur", "inf", "diminué", "diminue",
    ]
    for keyword in negative_keywords:
        if keyword in text:
            return False
    
    return False


def normaliser_score(score_brut: int, score_max_theorique: int, score_max: int = 100) -> int:
    """
    Normalise un score sur une échelle de 0 à score_max.
    
    Cette fonction est utilisée pour normaliser les scores de tous les types de documents
    sur une échelle cohérente de 0 à 100 points.
    
    Args:
        score_brut: Score brut calculé (somme des pénalités)
        score_max_theorique: Score maximum théorique (somme des pénalités maximales possibles)
        score_max: Score maximum cible (par défaut 100)
    
    Returns:
        Score normalisé (0-score_max)
        
    Exemples:
        >>> normaliser_score(50, 100, 100)  # 50% = 50 points
        50
        >>> normaliser_score(76, 104, 100)  # 76/104 * 100 = 73 points
        73
        >>> normaliser_score(0, 100, 100)  # 0% = 0 points
        0
    """
    if score_max_theorique == 0:
        # Si le score max théorique est 0, retourner le score max (cas d'erreur)
        return score_max
    
    # Normaliser : (score_brut / score_max_theorique) * score_max
    score_normalise = round((score_brut / score_max_theorique) * score_max) if score_brut > 0 else 0
    # Limiter entre 0 et score_max
    return min(max(score_normalise, 0), score_max)


def calculer_precision(reponses: Dict[int, Any], questions_total: int) -> float:
    """
    Calcule la précision de l'analyse basée sur les réponses.
    
    Args:
        reponses: Dictionnaire avec les réponses aux questions
        questions_total: Nombre total de questions
    
    Returns:
        Précision en pourcentage (0-100)
    """
    if questions_total == 0:
        return 0.0
    
    reponses_valides = sum(
        1 for r in reponses.values()
        if r and str(r).strip().lower() not in ["non précisé", "erreur", ""]
    )
    
    return (reponses_valides / questions_total) * 100

