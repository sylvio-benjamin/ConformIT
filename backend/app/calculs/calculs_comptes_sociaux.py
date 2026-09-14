"""
Module de calcul de score pour les comptes sociaux.
Extraction de valeurs depuis PDF et calcul de ratios financiers.
Les comptes sociaux incluent : bilan comptable, compte de résultat et annexe.
"""

import re
import logging
from typing import Any, Dict, Optional
from .calculs_base import determiner_risque

logger = logging.getLogger(__name__)

# ===========================================================
# 🔹 1. Extraction de valeurs depuis le texte PDF
# ===========================================================

class ComptesSociauxParser:
    """
    Parseur pour extraire les valeurs financières des comptes sociaux depuis le texte PDF.
    """
    
    def __init__(self, texte: str):
        """
        Initialise le parseur avec le texte du PDF.
        
        Args:
            texte: Texte extrait du PDF des comptes sociaux
        """
        # Normaliser le texte (espaces non-breaking, etc.)
        self.texte = texte.replace('\xa0', ' ').replace('\u00a0', ' ')
        self.texte_lower = self.texte.lower()
    
    def _extraire_valeur(self, patterns: list, section: Optional[str] = None) -> Optional[float]:
        """
        Extrait une valeur numérique à partir de patterns de recherche.
        
        Args:
            patterns: Liste de patterns à chercher (ex: ["disponibilités", "banque", "caisse"])
            section: Section des comptes ("actif", "passif", "produits", "charges") pour limiter la recherche
        
        Returns:
            Valeur numérique trouvée ou None
        """
        # Délimiter la section si spécifiée
        texte_recherche = self.texte
        if section:
            section_patterns = {
                "actif": ["actif", "total actif", "bilan actif"],
                "passif": ["passif", "total passif", "bilan passif"],
                "produits": ["produits", "chiffre d'affaires", "ca", "ventes"],
                "charges": ["charges", "achats", "personnel", "impôts"]
            }
            section_terms = section_patterns.get(section, [])
            if section_terms:
                # Trouver la section dans le texte
                for term in section_terms:
                    idx = self.texte_lower.find(term)
                    if idx != -1:
                        # Prendre un extrait autour de la section
                        start = max(0, idx - 500)
                        end = min(len(self.texte), idx + 2000)
                        texte_recherche = self.texte[start:end]
                        break
        
        # Chercher les patterns dans le texte
        for pattern in patterns:
            pattern_lower = pattern.lower()
            idx = texte_recherche.lower().find(pattern_lower)
            if idx != -1:
                # Extraire le contexte autour du pattern
                context_start = max(0, idx - 100)
                context_end = min(len(texte_recherche), idx + len(pattern) + 200)
                context = texte_recherche[context_start:context_end]
                
                # Chercher un nombre après le pattern
                # Patterns pour trouver des nombres (avec espaces, virgules, points)
                number_patterns = [
                    r'(\d{1,3}(?:\s+\d{3})*(?:[.,]\d+)?)',  # Format français : 123 456,78
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',      # Format US : 123,456.78
                    r'(\d+(?:[.,]\d+)?)',                    # Format simple : 123456.78
                ]
                
                for num_pattern in number_patterns:
                    matches = re.finditer(num_pattern, context, re.IGNORECASE)
                    for match in matches:
                        num_str = match.group(1)
                        # Nettoyer le nombre
                        num_clean = num_str.replace(' ', '').replace(',', '.')
                        # Gérer les cas où la virgule est le séparateur décimal
                        if ',' in num_str and '.' not in num_str:
                            # Compter les chiffres après la virgule
                            parts = num_str.split(',')
                            if len(parts) == 2 and len(parts[1]) <= 2:
                                num_clean = num_str.replace(',', '.')
                            else:
                                num_clean = num_str.replace(',', '')
                        
                        try:
                            valeur = float(num_clean)
                            if valeur > 0:
                                logger.debug(f"✅ Valeur extraite pour '{pattern}': {valeur}")
                                return valeur
                        except ValueError:
                            continue
        
        logger.debug(f"❌ Aucune valeur trouvée pour patterns: {patterns}")
        return None
    
    def parser(self) -> Dict[str, Optional[float]]:
        """
        Parse le texte et extrait toutes les valeurs financières nécessaires.
        
        Returns:
            Dictionnaire avec les valeurs extraites
        """
        # Valeurs du bilan (actif)
        disponibilites = self._extraire_valeur(
            ["disponibilités", "banque", "caisse", "valeur en banque", "liquidités"],
            "actif"
        )
        
        creances_clients = self._extraire_valeur(
            ["créances clients", "creances clients", "clients", "créances à recevoir"],
            "actif"
        )
        
        stocks = self._extraire_valeur(
            ["stocks", "marchandises", "matières premières", "en-cours"],
            "actif"
        )
        
        actif_circulant = self._extraire_valeur(
            ["actif circulant", "actif courant", "actif à court terme"],
            "actif"
        )
        if actif_circulant is None:
            # Calculer si possible
            valeurs_ac = [v for v in [disponibilites, creances_clients, stocks] if v is not None]
            if valeurs_ac:
                actif_circulant = sum(valeurs_ac)
        
        # Valeurs du bilan (passif)
        dettes_fournisseurs = self._extraire_valeur(
            ["dettes fournisseurs", "fournisseurs", "dettes à payer"],
            "passif"
        )
        
        dettes_fiscales = self._extraire_valeur(
            ["dettes fiscales", "impôts à payer", "tva à payer"],
            "passif"
        )
        
        dettes_sociales = self._extraire_valeur(
            ["dettes sociales", "charges sociales à payer", "urssaf"],
            "passif"
        )
        
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
        
        # Valeurs du compte de résultat
        chiffre_affaires = self._extraire_valeur(
            ["chiffre d'affaires", "chiffre daffaires", "ca", "ventes", "produits"],
            "produits"
        )
        
        achats = self._extraire_valeur(
            ["achats", "achats de marchandises", "achats de matières"],
            "charges"
        )
        
        resultat_net = self._extraire_valeur(
            ["résultat net", "bénéfice net", "perte nette", "résultat de l'exercice"],
            "charges"
        )
        if resultat_net is None:
            resultat_net = resultat_exercice
        
        # Marge brute (CA - Achats)
        marge_brute = None
        if chiffre_affaires is not None and achats is not None:
            marge_brute = chiffre_affaires - achats
        
        # Charges financières
        charges_financieres = self._extraire_valeur(
            ["charges financières", "intérêts", "charges d'intérêts"],
            "charges"
        )
        
        # Résultat d'exploitation
        resultat_exploitation = self._extraire_valeur(
            ["résultat d'exploitation", "ebit", "résultat exploitation"],
            "charges"
        )
        
        # Logging pour debug
        logger.info(f"📊 Valeurs extraites des comptes sociaux:")
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
        logger.info(f"   - Résultat net: {resultat_net}")
        logger.info(f"   - Marge brute: {marge_brute}")
        logger.info(f"   - Charges financières: {charges_financieres}")
        logger.info(f"   - Résultat d'exploitation: {resultat_exploitation}")
        
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
            "resultat_net": resultat_net,
            "marge_brute": marge_brute,
            "charges_financieres": charges_financieres,
            "resultat_exploitation": resultat_exploitation,
        }


def extraire_valeurs_comptes_sociaux(texte: str, format_type: str = "texte") -> Dict[str, Any]:
    """
    Extrait les valeurs financières des comptes sociaux depuis le texte PDF.
    
    Args:
        texte: Texte extrait du PDF des comptes sociaux
        format_type: Type de format ("texte" pour PDF)
    
    Returns:
        Dictionnaire avec les valeurs financières extraites
    """
    if format_type != "texte":
        logger.warning(f"⚠️ Format '{format_type}' non supporté pour les comptes sociaux PDF. Utilisation du format texte.")
    
    parser = ComptesSociauxParser(texte)
    return parser.parser()


# ===========================================================
# 🔹 2. Calcul de score normalisé pour l'application
# ===========================================================

# Barème sur 100 points : 15 questions au total
PENALTY_HIGH = 10  # Mauvaise réponse = 10 points de pénalité (sur 10)
PENALTY_MEDIUM = 6  # Mauvaise réponse = 6 points de pénalité (sur 10)
PENALTY_LOW = 0  # Bonne réponse = 0 point de pénalité
TOTAL_QUESTIONS = 15
MAX_SCORE = 100  # Score maximum = 100 points (normalisé)


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




def calculer_score_comptes_sociaux(valeurs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le score des comptes sociaux à partir des valeurs extraites.
    
    Args:
        valeurs: Dictionnaire avec les valeurs financières extraites des comptes sociaux
    
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
    resultat_net = valeurs.get("resultat_net")
    marge_brute = valeurs.get("marge_brute")
    charges_financieres = valeurs.get("charges_financieres")
    resultat_exploitation = valeurs.get("resultat_exploitation")

    # Calculs des ratios
    ratio_liquidite = _safe_div(ac, dct)
    frng = None if fp is None or ac is None else fp - ac
    bfr = None if ac is None or dct is None else ac - dct
    bfr_jours = None if bfr is None or ca in (None, 0) else (bfr / ca) * 365
    ratio_endettement = _safe_div(df, cp)
    ratio_autonomie = _safe_div(cp, tp)
    creances_clients_jours = None if clients is None or ca in (None, 0) else (clients / ca) * 365
    dettes_fournisseurs_jours = None if fournisseurs is None or achats in (None, 0) else (fournisseurs / achats) * 365
    marge_brute_pct = None if marge_brute is None or ca in (None, 0) else (marge_brute / ca) * 100
    ratio_couverture_dettes = None if resultat_exploitation is None or charges_financieres in (None, 0) else resultat_exploitation / charges_financieres
    charges_financieres_pct = None if charges_financieres is None or resultat_exploitation in (None, 0) else (charges_financieres / resultat_exploitation) * 100
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

    # Questions 1-10 : Bilan (comme avant)
    enregistrer(1, None if ratio_liquidite is None else ratio_liquidite >= 1.0, f"Ratio liquidité = {_fmt(ratio_liquidite)}")
    enregistrer(2, None if frng is None else frng > 0, f"FRNG = {_fmt(frng, ' €')}")
    enregistrer(3, None if bfr_jours is None else bfr_jours <= 90, f"BFR = {_fmt(bfr, ' €')} soit {_fmt(bfr_jours, ' jours de CA')}", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(4, None if cp is None else cp > 0, f"Capitaux propres = {_fmt(cp, ' €')}")
    enregistrer(5, None if ratio_endettement is None else ratio_endettement < 1, f"Ratio endettement = {_fmt(ratio_endettement)}", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(6, None if cp is None or cp_n1 is None else cp >= cp_n1, f"Capitaux propres N = {_fmt(cp, ' €')} / N-1 = {_fmt(cp_n1, ' €')}", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(7, None if tresorerie_nette is None else tresorerie_nette > 0, f"Trésorerie nette = {_fmt(tresorerie_nette, ' €')}")
    enregistrer(8, None if ratio_autonomie is None else ratio_autonomie >= 0.20, f"Autonomie financière = {_fmt(ratio_autonomie * 100 if ratio_autonomie is not None else None, ' %')}", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(9, None if creances_clients_jours is None else creances_clients_jours <= 90, f"Créances clients = {_fmt(clients, ' €')} soit {_fmt(creances_clients_jours, ' jours de CA')}", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(10, None if dettes_fournisseurs_jours is None else dettes_fournisseurs_jours <= 90, f"Dettes fournisseurs = {_fmt(fournisseurs, ' €')} soit {_fmt(dettes_fournisseurs_jours, suffix_jours_achats)}", penalty_if_false=PENALTY_MEDIUM)
    
    # Questions 11-15 : Compte de résultat
    enregistrer(11, None if resultat_net is None else resultat_net > 0, f"Résultat net = {_fmt(resultat_net, ' €')}")
    enregistrer(12, None if marge_brute_pct is None else marge_brute_pct >= 30, f"Marge brute = {_fmt(marge_brute_pct, ' %')}", penalty_if_false=PENALTY_MEDIUM)
    # Question 13 : Croissance du CA (nécessiterait plusieurs exercices)
    # Pour l'instant, on ne peut pas calculer la croissance sans données multi-exercices
    # On utilise "Non précisé" avec une pénalité faible car ce n'est pas critique
    enregistrer(13, None, "Croissance du CA : données multi-exercices non disponibles (nécessite plusieurs années)", penalty_if_false=PENALTY_LOW, penalty_if_true=PENALTY_LOW)
    enregistrer(14, None if charges_financieres_pct is None else charges_financieres_pct <= 10, f"Charges financières = {_fmt(charges_financieres_pct, ' %')} du résultat d'exploitation", penalty_if_false=PENALTY_MEDIUM)
    enregistrer(15, None if ratio_couverture_dettes is None else ratio_couverture_dettes >= 3, f"Ratio couverture dettes = {_fmt(ratio_couverture_dettes)}", penalty_if_false=PENALTY_MEDIUM)

    precision = (questions_traitees / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0.0
    
    # Calculer le score maximum théorique réel
    # Questions avec PENALTY_HIGH (10 points) : 1, 2, 4, 7, 11 = 5 questions
    # Questions avec PENALTY_MEDIUM (6 points) : 3, 5, 6, 8, 9, 10, 12, 14, 15 = 9 questions
    # Question 13 : PENALTY_LOW si False et PENALTY_LOW si True (0) = 1 question (ne contribue pas au score max)
    # Score maximum théorique = 5 * 10 + 9 * 6 = 50 + 54 = 104 points
    score_max_theorique = (5 * PENALTY_HIGH) + (9 * PENALTY_MEDIUM)  # 104 points
    
    # Normaliser sur 100 points
    score_brut = total
    if score_max_theorique == 0:
        score_total = 100
    else:
        score_normalise = round((score_brut / score_max_theorique) * 100) if score_brut > 0 else 0
        score_total = min(max(score_normalise, 0), 100)
    
    score_max = MAX_SCORE
    risque = determiner_risque(score_total)

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
            "marge_brute_pct": marge_brute_pct,
            "ratio_couverture_dettes": ratio_couverture_dettes,
        },
        "niveau_risque": risque,
        "risque": risque,
    }

