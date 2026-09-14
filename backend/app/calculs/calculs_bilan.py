"""
Module de calcul de score pour les bilans comptables.
Extraction de valeurs depuis PDF et calcul de ratios financiers.
"""

import re
import json
import os
import logging
from typing import Any, Dict, Optional
from .calculs_base import determiner_risque

logger = logging.getLogger(__name__)

# ===========================================================
# 🔹 1. Extraction de valeurs depuis le texte PDF
# ===========================================================

class BilanParser:
    """
    Parseur pour extraire les valeurs financières d'un bilan comptable depuis le texte PDF.
    """
    
    def __init__(self, texte: str):
        """
        Initialise le parseur avec le texte du PDF.
        
        Args:
            texte: Texte extrait du PDF du bilan comptable
        """
        # Normaliser le texte (espaces non-breaking, etc.)
        self.texte = texte.replace('\xa0', ' ').replace('\u00a0', ' ')
        self.texte_lower = self.texte.lower()
    
    def _extraire_valeur(self, patterns: list, section: Optional[str] = None) -> Optional[float]:
        """
        Extrait une valeur numérique à partir de patterns de recherche.
        
        Args:
            patterns: Liste de patterns à chercher (ex: ["disponibilités", "banque", "caisse"])
            section: Section du bilan ("actif" ou "passif") pour limiter la recherche
        
        Returns:
            Valeur numérique trouvée ou None
        """
        # Délimiter la section si spécifiée
        texte_recherche = self.texte
        if section:
            section_patterns = {
                "actif": ["actif", "total actif", "bilan actif"],
                "passif": ["passif", "total passif", "bilan passif"]
            }
            section_keys = section_patterns.get(section.lower(), [])
            if section_keys:
                # Trouver les indices de début et fin de section
                for key in section_keys:
                    idx = self.texte_lower.find(key)
                    if idx != -1:
                        # Extraire jusqu'à 5000 caractères après le début de la section
                        texte_recherche = self.texte[idx:idx+5000]
                        break
        
        # Chercher les patterns dans le texte
        for pattern in patterns:
            pattern_lower = pattern.lower()
            # Rechercher le pattern avec variations (avec/sans accents, pluriel, etc.)
            variations = [
                pattern_lower,
                pattern_lower.replace('é', 'e').replace('è', 'e').replace('ê', 'e'),
                pattern_lower + 's',  # pluriel
                pattern_lower.replace('é', 'e') + 's'
            ]
            
            for var in variations:
                idx = texte_recherche.lower().find(var)
                if idx != -1:
                    # Extraire le contexte autour du pattern (200 caractères)
                    contexte = texte_recherche[max(0, idx-50):idx+200]
                    
                    # Chercher un nombre dans le contexte
                    # Patterns pour trouver les nombres: 123 456,78 ou 123456.78 ou 123 456.78
                    number_patterns = [
                        r'(\d{1,3}(?:[\s\u00a0]\d{3})*(?:[.,]\d{2})?)',  # Format français: 123 456,78
                        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Format anglo-saxon: 123,456.78
                        r'(\d+(?:[.,]\d{2})?)',  # Format simple: 12345.67 ou 12345,67
                    ]
                    
                    for num_pattern in number_patterns:
                        matches = re.findall(num_pattern, contexte)
                        if matches:
                            # Prendre le dernier nombre trouvé (généralement la valeur NET)
                            # ou le plus grand nombre dans le contexte
                            valeurs = []
                            for match in matches:
                                # Nettoyer le nombre (enlever espaces, remplacer virgule par point)
                                nombre_str = match.replace(' ', '').replace('\u00a0', '').replace(',', '.')
                                try:
                                    valeur = float(nombre_str)
                                    if valeur > 0:  # Ignorer les zéros
                                        valeurs.append(valeur)
                                except ValueError:
                                    continue
                            
                            if valeurs:
                                # Prendre la valeur la plus grande (généralement le total)
                                return max(valeurs)
        
        return None
    
    def parser(self) -> Dict[str, Any]:
        """
        Parse le texte et extrait toutes les valeurs financières.
        
        Returns:
            Dictionnaire avec les valeurs extraites
        """
        # Extraction des valeurs de l'ACTIF
        disponibilites = self._extraire_valeur(
            ["disponibilités", "banque", "caisse", "valeur disponible", "liquidités"],
            "actif"
        )
        
        creances_clients = self._extraire_valeur(
            ["créances clients", "créances sur clients", "clients", "créances commerciales"],
            "actif"
        )
        
        stocks = self._extraire_valeur(
            ["stocks", "stock", "inventaire", "marchandises"],
            "actif"
        )
        
        # Calcul de l'actif circulant
        actif_circulant = None
        valeurs_actif_circulant = [v for v in [stocks, creances_clients, disponibilites] if v is not None]
        if valeurs_actif_circulant:
            actif_circulant = sum(valeurs_actif_circulant)
        else:
            # Essayer de trouver directement "actif circulant"
            actif_circulant = self._extraire_valeur(["actif circulant", "actifs circulants"], "actif")
        
        # Extraction des valeurs du PASSIF
        dettes_fournisseurs = self._extraire_valeur(
            ["dettes fournisseurs", "fournisseurs", "dettes commerciales"],
            "passif"
        )
        
        dettes_fiscales = self._extraire_valeur(
            ["dettes fiscales", "impôts", "taxes à payer"],
            "passif"
        )
        
        dettes_sociales = self._extraire_valeur(
            ["dettes sociales", "charges sociales", "cotisations sociales"],
            "passif"
        )
        
        # Dettes court terme (somme des dettes à court terme)
        dettes_court_terme = None
        valeurs_dct = [v for v in [dettes_fournisseurs, dettes_fiscales, dettes_sociales] if v is not None]
        if valeurs_dct:
            dettes_court_terme = sum(valeurs_dct)
        else:
            # Essayer de trouver directement "dettes à court terme"
            dettes_court_terme = self._extraire_valeur(
                ["dettes à court terme", "passif circulant", "dettes courantes"],
                "passif"
            )
        
        dettes_financieres = self._extraire_valeur(
            ["emprunts", "dettes financières", "dettes à long terme", "emprunts bancaires"],
            "passif"
        )
        
        capitaux_propres = self._extraire_valeur(
            ["capitaux propres", "capital social", "réserves", "apports", "fonds propres"],
            "passif"
        )
        
        resultat_exercice = self._extraire_valeur(
            ["résultat de l'exercice", "résultat", "bénéfice", "perte"],
            "passif"
        )
        
        # Calcul du financement permanent
        financement_permanent = None
        valeurs_fp = [v for v in [capitaux_propres, dettes_financieres] if v is not None]
        if valeurs_fp:
            financement_permanent = sum(valeurs_fp)
        
        # Calcul du total passif
        total_passif = None
        valeurs_tp = [v for v in [capitaux_propres, dettes_financieres, dettes_court_terme] if v is not None]
        if valeurs_tp:
            total_passif = sum(valeurs_tp)
        else:
            # Essayer de trouver directement "total passif"
            total_passif = self._extraire_valeur(["total passif", "passif total"], "passif")
        
        # Trésorerie nette
        tresorerie_nette = None
        if disponibilites is not None and dettes_court_terme is not None:
            tresorerie_nette = disponibilites - dettes_court_terme
        
        # Autres valeurs nécessaires (peuvent être dans le compte de résultat)
        chiffre_affaires = self._extraire_valeur(
            ["chiffre d'affaires", "chiffre daffaires", "ca", "ventes", "produits"]
        )
        
        achats = self._extraire_valeur(
            ["achats", "achats de marchandises", "achats de matières"]
        )
        
        # Logging pour debug
        logger.info(f"📊 Valeurs extraites du bilan:")
        logger.info(f"   - Disponibilités: {disponibilites}")
        logger.info(f"   - Créances clients: {creances_clients}")
        logger.info(f"   - Stocks: {stocks}")
        logger.info(f"   - Actif circulant: {actif_circulant}")
        logger.info(f"   - Dettes court terme: {dettes_court_terme}")
        logger.info(f"   - Dettes financières: {dettes_financieres}")
        logger.info(f"   - Capitaux propres: {capitaux_propres}")
        logger.info(f"   - Total passif: {total_passif}")
        logger.info(f"   - Financement permanent: {financement_permanent}")
        logger.info(f"   - Trésorerie nette: {tresorerie_nette}")
        logger.info(f"   - Chiffre d'affaires: {chiffre_affaires}")
        logger.info(f"   - Achats: {achats}")
        
        return {
            "disponibilites": disponibilites,
            "creances_clients": creances_clients,
            "stocks": stocks,
            "actif_circulant": actif_circulant,
            "dettes_fournisseurs": dettes_fournisseurs,
            "dettes_court_terme": dettes_court_terme,
            "dettes_financieres": dettes_financieres,
            "capitaux_propres": capitaux_propres,
            "capitaux_propres_n1": None,  # Nécessiterait deux exercices
            "resultat_exercice": resultat_exercice,
            "financement_permanent": financement_permanent,
            "total_passif": total_passif,
            "tresorerie_nette": tresorerie_nette,
            "chiffre_affaires": chiffre_affaires,
            "achats": achats,
        }


def extraire_valeurs_bilan(texte: str, format_type: str = "texte") -> Dict[str, Any]:
    """
    Extrait les valeurs financières d'un bilan depuis le texte PDF.
    
    Args:
        texte: Texte extrait du PDF du bilan comptable
        format_type: Type de format ("texte" pour PDF, "csv" pour CSV - deprecated)
    
    Returns:
        Dictionnaire avec les valeurs financières extraites
    """
    if format_type == "csv":
        logger.warning("⚠️ Format CSV déprécié, utilisez convertir_csv_en_json pour les CSV")
        return {}
    
    parser = BilanParser(texte)
    return parser.parser()


# ===========================================================
# 🔹 2. Calcul de score normalisé pour l'application
# ===========================================================

# Barème sur 100 points : chaque question vaut 10 points maximum
PENALTY_HIGH = 10  # Mauvaise réponse = 10 points de pénalité (sur 10)
PENALTY_MEDIUM = 6  # Mauvaise réponse = 6 points de pénalité (sur 10)
PENALTY_LOW = 0  # Bonne réponse = 0 point de pénalité
TOTAL_QUESTIONS = 10
MAX_SCORE = 100  # Score maximum = 100 points (10 questions * 10 points)


def _safe_div(numerateur: Optional[float], denominateur: Optional[float]) -> Optional[float]:
    """Division sécurisée avec gestion des None et zéro."""
    if numerateur is None or denominateur in (None, 0):
        return None
    try:
        return numerateur / denominateur
    except ZeroDivisionError:
        return None


def _fmt(valeur: Optional[float], suffix: str = "") -> str:
    """Formate une valeur avec un suffixe."""
    if valeur is None:
        return "Données indisponibles"
    try:
        return f"{valeur:,.2f}{suffix}".replace(",", " ")
    except Exception:
        return f"{valeur}{suffix}"


def _determiner_risque(score: int) -> str:
    """Détermine le niveau de risque à partir du score."""
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Medium"
    if score <= 80:
        return "High"
    return "Critical"


def calculer_score_bilan(valeurs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le score du bilan à partir des valeurs extraites.
    
    Args:
        valeurs: Dictionnaire avec les valeurs financières extraites du bilan
    
    Returns:
        Dictionnaire avec le score, les réponses, les justifications et les métriques
    """
    scores_detail: Dict[int, int] = {}
    reponses_calculees: Dict[int, str] = {}
    justifications_calculees: Dict[int, str] = {}
    total = 0
    questions_traitees = 0

    ac = valeurs.get("actif_circulant")
    dct = valeurs.get("dettes_court_terme")
    cp = valeurs.get("capitaux_propres")
    cp_n1 = valeurs.get("capitaux_propres_n1")
    fp = valeurs.get("financement_permanent")
    tp = valeurs.get("total_passif")
    disponibilites = valeurs.get("disponibilites")
    tresorerie_nette = valeurs.get("tresorerie_nette")
    if tresorerie_nette is None and disponibilites is not None and dct is not None:
        tresorerie_nette = disponibilites - dct
    df = valeurs.get("dettes_financieres", 0)
    ca = valeurs.get("chiffre_affaires")
    achats = valeurs.get("achats")
    clients = valeurs.get("creances_clients")
    fournisseurs = valeurs.get("dettes_fournisseurs")

    ratio_liquidite = _safe_div(ac, dct)
    frng = None if fp is None or ac is None else fp - ac
    bfr = None if ac is None or dct is None else ac - dct
    bfr_jours = None if bfr is None or ca in (None, 0) else (bfr / ca) * 365
    ratio_endettement = _safe_div(df, cp)
    ratio_autonomie = _safe_div(cp, tp)
    creances_clients_jours = None if clients is None or ca in (None, 0) else (clients / ca) * 365
    dettes_fournisseurs_jours = None if fournisseurs is None or achats in (None, 0) else (fournisseurs / achats) * 365
    suffix_jours_achats = " jours d'achats"

    def enregistrer(question: int,
                    condition: Optional[bool],
                    justification: str,
                    penalty_if_false: int = PENALTY_HIGH,
                    penalty_if_true: int = PENALTY_LOW):
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

    enregistrer(
        1,
        None if ratio_liquidite is None else ratio_liquidite >= 1.0,
        f"Ratio liquidité = {_fmt(ratio_liquidite)}",
    )

    enregistrer(
        2,
        None if frng is None else frng > 0,
        f"FRNG = {_fmt(frng, ' €')}",
    )

    enregistrer(
        3,
        None if bfr_jours is None else bfr_jours <= 90,
        f"BFR = {_fmt(bfr, ' €')} soit {_fmt(bfr_jours, ' jours de CA')}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    enregistrer(
        4,
        None if cp is None else cp > 0,
        f"Capitaux propres = {_fmt(cp, ' €')}",
    )

    enregistrer(
        5,
        None if ratio_endettement is None else ratio_endettement < 1,
        f"Ratio endettement = {_fmt(ratio_endettement)}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    enregistrer(
        6,
        None if cp is None or cp_n1 is None else cp >= cp_n1,
        f"Capitaux propres N = {_fmt(cp, ' €')} / N-1 = {_fmt(cp_n1, ' €')}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    enregistrer(
        7,
        None if tresorerie_nette is None else tresorerie_nette > 0,
        f"Trésorerie nette = {_fmt(tresorerie_nette, ' €')}",
    )

    enregistrer(
        8,
        None if ratio_autonomie is None else ratio_autonomie >= 0.20,
        f"Autonomie financière = {_fmt(ratio_autonomie * 100 if ratio_autonomie is not None else None, ' %')}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    enregistrer(
        9,
        None if creances_clients_jours is None else creances_clients_jours <= 90,
        f"Créances clients = {_fmt(clients, ' €')} soit {_fmt(creances_clients_jours, ' jours de CA')}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    enregistrer(
        10,
        None if dettes_fournisseurs_jours is None else dettes_fournisseurs_jours <= 90,
        f"Dettes fournisseurs = {_fmt(fournisseurs, ' €')} soit {_fmt(dettes_fournisseurs_jours, suffix_jours_achats)}",
        penalty_if_false=PENALTY_MEDIUM,
    )

    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 1, 2, 4, 7 = 4 questions
    # Questions avec PENALTY_MEDIUM (6 points) : 3, 5, 6, 8, 9, 10 = 6 questions
    # Score maximum théorique = 4 * 10 + 6 * 6 = 40 + 36 = 76 points
    score_max_theorique = (4 * PENALTY_HIGH) + (6 * PENALTY_MEDIUM)  # 76 points
    
    # Normaliser sur 100 points
    if score_max_theorique == 0:
        score_total = 100
    else:
        score_normalise = round((total / score_max_theorique) * 100) if total > 0 else 0
        score_total = min(max(score_normalise, 0), 100)
    
    score_max = MAX_SCORE  # Score maximum = 100 points (normalisé)
    risque = _determiner_risque(score_total)

    return {
        "score_total": score_total,
        "score_max": score_max,
        "scores_detail": scores_detail,
        "precision": precision,
        "reponses": reponses_calculees,
        "justifications": justifications_calculees,
        "metriques": {
            "ratio_liquidite": ratio_liquidite,
            "frng": frng,
            "bfr": bfr,
            "bfr_jours": bfr_jours,
            "ratio_endettement": ratio_endettement,
            "ratio_autonomie": ratio_autonomie,
            "creances_clients_jours": creances_clients_jours,
            "dettes_fournisseurs_jours": dettes_fournisseurs_jours,
        },
        "niveau_risque": risque,
        "risque": risque,
    }


# ===========================================================
# 🔹 3. Fonctions de compatibilité (deprecated - pour CSV)
# ===========================================================

def convertir_csv_en_json(fichier_ou_texte: str, export_path: str = None):
    """
    DEPRECATED: Cette fonction est conservée pour compatibilité mais ne devrait plus être utilisée.
    Utilisez extraire_valeurs_bilan avec du texte PDF à la place.
    """
    logger.warning("⚠️ convertir_csv_en_json est deprecated. Utilisez extraire_valeurs_bilan avec du texte PDF.")
    return []


def extraire_donnees_bilan_json(bilan_json):
    """
    DEPRECATED: Cette fonction est conservée pour compatibilité mais ne devrait plus être utilisée.
    Utilisez extraire_valeurs_bilan avec du texte PDF à la place.
    """
    logger.warning("⚠️ extraire_donnees_bilan_json est deprecated. Utilisez extraire_valeurs_bilan avec du texte PDF.")
    return {}


def analyser_bilan_csv(fichier_csv: str, export_json: Optional[str] = None) -> Dict[str, Any]:
    """
    DEPRECATED: Cette fonction est conservée pour compatibilité mais ne devrait plus être utilisée.
    Utilisez extraire_valeurs_bilan avec du texte PDF à la place.
    """
    logger.warning("⚠️ analyser_bilan_csv est deprecated. Utilisez extraire_valeurs_bilan avec du texte PDF.")
    return {"donnees_extraites": {}, "resultats": {}}


# ===========================================================
# 🔹 4. Exécution principale (pour tests)
# ===========================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyse un bilan comptable depuis un PDF.")
    parser.add_argument("fichier", help="Chemin du fichier PDF à analyser")
    args = parser.parse_args()
    
    # Lire le texte du PDF (nécessite une fonction d'extraction)
    print("⚠️ Cette fonction nécessite d'extraire le texte du PDF d'abord.")
    print("   Utilisez le module analyse.py pour une analyse complète.")
