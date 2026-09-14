"""
Module d'analyse de documents avec optimisations async, corrections de bugs critiques.
"""

import os
import json
import re
import math
import tempfile
import asyncio
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
from fastapi import APIRouter, Request, HTTPException
import aiofiles
import aiohttp
import PyPDF2

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None


logger = logging.getLogger(__name__)


def _extract_pdf_text(path: str, max_chars: int, document_type: Optional[str] = None) -> str:
    """
    Extrait le texte d'un PDF en utilisant le module pdf_parser.
    Utilise l'extraction simple pour les documents simples, PDF Vector pour les complexes.
    """
    try:
        # Si pas de type fourni, essayer de le détecter depuis le chemin
        if not document_type:
            # Essayer de deviner depuis le nom du fichier
            filename_lower = os.path.basename(path).lower()
            if "kbis" in filename_lower or "rcs" in filename_lower:
                document_type = "extrait_kbis"
            elif "attestation" in filename_lower:
                document_type = "attestation_assurance"
            else:
                document_type = "comptes_sociaux"  # Par défaut pour les comptes sociaux
        
        # Utiliser le nouveau module de parsing
        parse_result = parse_pdf(path, document_type)
        logger.info(f"📄 Document parsé avec : {parse_result.get('method', 'unknown')}")
        
        # Extraire le texte du résultat
        texte = get_text_from_result(parse_result)
        
        # Limiter à max_chars
        return texte[:max_chars]
        
    except PDFParserError as e:
        logger.warning(f"⚠️ Erreur parsing PDF : {e}, fallback sur extraction basique")
        # Fallback sur l'ancienne méthode en cas d'erreur
        texte = ""
        try:
            with open(path, "rb") as f:
                lecteur = PyPDF2.PdfReader(f)
                max_pages = min(10, len(lecteur.pages))
                for i in range(max_pages):
                    page_text = lecteur.pages[i].extract_text()
                    if page_text:
                        texte += page_text + "\n"
                        if len(texte) >= max_chars:
                            break
        except Exception as e2:
            logger.error(f"❌ Erreur extraction PDF fallback : {e2}")
        return texte[:max_chars]


def _extract_csv_text(path: str, max_chars: int) -> str:
    contenu = ""

    def _read_with_encoding(enc: str) -> str:
        texte_local = ""
        try:
            with open(path, newline="", encoding=enc) as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    ligne = " ".join(cell.strip() for cell in row if cell)
                    if ligne:
                        texte_local += ligne + "\n"
                    if len(texte_local) >= max_chars:
                        break
        except Exception as err:
            logger.warning(f"⚠️ Erreur lecture CSV ({enc}) : {err}")
        return texte_local

    if os.path.exists(path):
        contenu = _read_with_encoding("utf-8")
        if not contenu:
            contenu = _read_with_encoding("latin-1")
    return contenu[:max_chars]


def _extract_excel_text(path: str, max_chars: int) -> str:
    texte = ""
    if load_workbook is None:
        logger.warning("⚠️ openpyxl indisponible : impossible de lire le fichier Excel.")
        return texte

    try:
        wb = load_workbook(path, read_only=True, data_only=True)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                cellules = [str(cell).strip() for cell in row if cell not in (None, "", "None")]
                if cellules:
                    texte += " ".join(cellules) + "\n"
                if len(texte) >= max_chars:
                    break
            if len(texte) >= max_chars:
                break
    except Exception as e:
        logger.warning(f"⚠️ Erreur extraction Excel : {e}")
    return texte[:max_chars]


_EXTRACTORS = {
    ".csv": _extract_csv_text,
    ".xls": _extract_excel_text,
    ".xlsx": _extract_excel_text,
    ".xlsm": _extract_excel_text,
}


def extraire_contenu_document(fichier: str, max_chars: int = 10000, document_type: Optional[str] = None) -> str:
    """
    Extrait le contenu d'un document (PDF, CSV, Excel).
    Pour les PDFs, utilise le nouveau module pdf_parser.
    """
    suffix = Path(fichier).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(fichier, max_chars, document_type)
    extractor = _EXTRACTORS.get(suffix)
    if extractor:
        return extractor(fichier, max_chars)
    # Fallback pour les extensions non reconnues : essayer comme PDF
    return _extract_pdf_text(fichier, max_chars, document_type)


def extraire_texte_pdf(fichier_pdf: str, max_chars: int = 10000, document_type: Optional[str] = None) -> str:
    """Version synchrone de l'extraction de texte."""
    return extraire_contenu_document(fichier_pdf, max_chars, document_type)

from app.parser import parser_document_async, detecter_type_document
from app.calculs.calculs_kbis import analyser_et_calculer as analyser_et_calculer_kbis
from app.calculs.calculs_bilan import calculer_score_bilan, extraire_valeurs_bilan
from app.calculs.calculs_comptes_sociaux import calculer_score_comptes_sociaux, extraire_valeurs_comptes_sociaux
from app.pdf_parser import parse_pdf, get_text_from_result, PDFParserError
from app.calculs.calculs_compte_resultat import calculer_score_compte_resultat
from app.calculs.calculs_liasse import calculer_score_liasse
from app.calculs.calculs_releve import calculer_score_releve
from app.calculs.calculs_statuts import calculer_score_statuts
from app.calculs.calculs_attestation import calculer_score_attestation
from app.calculs.calculs_generique import calculer_score_generique
from app.groq_client import appel_api_securise_async as groq_call_async
from app.services.analyse_service import AnalyseService
from app.prompts import get_prompt_for_question
from app.scoring.engine import apply_deterministic_scoring
from app.scoring.pages import extract_pages
from app.extraction.comptes.questions import impacts_from_evaluations as impacts_from_comptes
from app.extraction.kbis import apply_fact_overrides, expected_unknown_facts
from app.extraction.kbis.questions import impacts_from_evaluations as impacts_from_kbis
from app.extraction.kbis_facts import extract_company_name
from app.extraction.model import EVAL_INCONNU
from app.extraction.mistral_fallback import extract_missing_facts_mistral, fill_unresolved_with_mistral
from app.extraction.coherence import DocumentTypeMismatch, check_coherence
from app.extraction.document_types import DOCUMENT_TYPE_LABELS, is_selectable
from app.extraction.registry import EXTRACTORS, evaluate_facts, extract_facts


def formatter_type_document(type_key: str) -> str:
    if not type_key:
        return "Document non identifié"
    return DOCUMENT_TYPE_LABELS.get(type_key, type_key.replace("_", " ").title())


def determiner_couleur_risque(score: int) -> str:
    try:
        score_int = int(score)
    except (ValueError, TypeError):
        score_int = 0

    if score_int <= 30:
        return "green"
    if score_int <= 60:
        return "orange"
    if score_int <= 80:
        return "orange-dark"
    return "red"


def determiner_niveau_risque_score(score: int) -> str:
    try:
        score_int = int(score)
    except (ValueError, TypeError):
        score_int = 0

    if score_int <= 30:
        return "Low"
    if score_int <= 60:
        return "Medium"
    if score_int <= 80:
        return "High"
    return "Critical"


router = APIRouter()

# === Constantes ===
DOCUMENTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents")

# Mapping des types de documents vers les fichiers de questions
# IMPORTANT: Assurez-vous que chaque type détecté par detecter_type_document
# a un fichier de questions correspondant dans ce dictionnaire
QUESTION_FILES = {
    "extrait_kbis": "questions.json",
    "comptes_sociaux": "questions_comptes_sociaux.json",
    "bilan_comptable": "questions_bilan_comptable.json",  # Conservé pour compatibilité (utilise comptes_sociaux en réalité)
    "compte_resultat": "questions_compte_resultat.json",
    "liasse_fiscale": "questions_liasse_fiscale.json",
    "releve_bancaire": "questions_releve_bancaire.json",
    "statuts": "questions_statuts.json",
    "attestation_assurance": "questions_attestation.json",
    # Types sans fichier de questions dédié (utilisent calculer_score_generique)
    # "autorisation_commerciale": None,  # Pas de fichier de questions
    # "type_inconnu": None,  # Pas de fichier de questions
}

CALCULATEURS_DOCUMENTS = {
    "extrait_kbis": analyser_et_calculer_kbis,
    # "bilan_comptable": géré séparément dans analyser_questions_async (extraction PDF)
    "compte_resultat": calculer_score_compte_resultat,
    "liasse_fiscale": calculer_score_liasse,
    "releve_bancaire": calculer_score_releve,
    "statuts": calculer_score_statuts,
    "attestation_assurance": calculer_score_attestation,
    "autorisation_commerciale": calculer_score_generique,
    "type_inconnu": calculer_score_generique,
}

indices_binaires_kbis = {2, 7, 9, 11, 12}

# Service d'analyse
analyse_service = AnalyseService()


def _verifier_mapping_type_questions() -> bool:
    """
    Vérifie que tous les types de documents détectés ont un fichier de questions correspondant.
    
    Cette fonction vérifie :
    1. Que tous les types détectés par parser.py sont dans QUESTION_FILES ou sont des types spéciaux
    2. Que tous les types retournés par schemas.py.infer_document_type sont dans QUESTION_FILES ou sont des types spéciaux
    3. Que tous les fichiers de questions référencés dans QUESTION_FILES existent
    
    Returns:
        True si tous les types sont mappés, False sinon
    """
    # Types détectés par detecter_type_document dans parser.py
    types_parser = [
        "extrait_kbis",
        "attestation_assurance",
        "statuts",
        "releve_bancaire",
        "liasse_fiscale",
        "compte_resultat",
        "comptes_sociaux",
        "autorisation_commerciale",
        "type_inconnu",
    ]
    
    # Types retournés par infer_document_type dans schemas.py
    types_schemas = [
        "comptes_sociaux",  # Pour CSV/XLS/XLSX
        "extrait_kbis",  # Pour PDF avec patterns Kbis
        "attestation_assurance",  # Pour PDF avec patterns assurance
        "statuts",  # Pour PDF avec patterns statuts
        "releve_bancaire",  # Pour PDF avec patterns relevé bancaire
        "liasse_fiscale",  # Pour PDF avec patterns liasse fiscale
        "autorisation_commerciale",  # Pour PDF avec patterns autorisation
    ]
    
    # Tous les types uniques
    types_detectes = list(set(types_parser + types_schemas))
    
    # Vérifier que tous les types sont dans QUESTION_FILES ou sont des types spéciaux
    types_speciaux = ["autorisation_commerciale", "type_inconnu"]  # Types sans fichier de questions
    
    tous_mappes = True
    logger.info("🔍 Vérification du mapping type → fichier de questions...")
    
    for type_doc in sorted(types_detectes):
        if type_doc not in QUESTION_FILES and type_doc not in types_speciaux:
            logger.error(f"❌ Type '{type_doc}' détecté mais non mappé dans QUESTION_FILES")
            logger.error(f"   Types disponibles dans QUESTION_FILES : {list(QUESTION_FILES.keys())}")
            tous_mappes = False
        elif type_doc in QUESTION_FILES:
            fichier = QUESTION_FILES[type_doc]
            chemin = os.path.join(DOCUMENTS_ROOT, fichier)
            if not os.path.exists(chemin):
                logger.error(f"❌ Fichier de questions manquant pour '{type_doc}': {chemin}")
                logger.error(f"   DOCUMENTS_ROOT : {DOCUMENTS_ROOT}")
                tous_mappes = False
            else:
                logger.info(f"✅ Type '{type_doc}' → Fichier '{fichier}' existe")
        elif type_doc in types_speciaux:
            logger.info(f"ℹ️ Type '{type_doc}' est un type spécial (pas de fichier de questions)")
    
    # Vérifier aussi que tous les fichiers dans QUESTION_FILES existent
    logger.info("🔍 Vérification de l'existence des fichiers de questions...")
    for type_doc, fichier in QUESTION_FILES.items():
        chemin = os.path.join(DOCUMENTS_ROOT, fichier)
        if not os.path.exists(chemin):
            logger.error(f"❌ Fichier de questions référencé n'existe pas : '{type_doc}' → '{fichier}' ({chemin})")
            tous_mappes = False
        else:
            logger.debug(f"✅ Fichier '{fichier}' existe pour le type '{type_doc}'")
    
    if tous_mappes:
        logger.info("✅ Tous les types de documents sont correctement mappés aux fichiers de questions")
    else:
        logger.error("❌ Des problèmes ont été détectés dans le mapping type → fichier de questions")
    
    return tous_mappes


@lru_cache(maxsize=None)
def _charger_questions(type_document: str = "extrait_kbis") -> Dict[int, str]:
    """
    Charge les questions selon le type de document.
    
    Cette fonction garantit que le bon fichier de questions est utilisé
    en fonction du type de document détecté.
    
    Args:
        type_document: Type de document (ex: "extrait_kbis", "comptes_sociaux", etc.)
    
    Returns:
        Dictionnaire avec les questions (clés: numéros de questions, valeurs: texte des questions)
    
    Raises:
        FileNotFoundError: Si le fichier de questions n'existe pas
        Exception: Si une erreur survient lors du chargement
    """
    logger.info(f"📋 === CHARGEMENT DES QUESTIONS ===")
    logger.info(f"📋 Type de document demandé : '{type_document}'")
    logger.info(f"📋 Types de documents supportés : {list(QUESTION_FILES.keys())}")
    
    # Vérifier que le type de document est dans QUESTION_FILES
    if type_document == "extrait_kbis":
        from app.extraction.kbis.catalog import questions_json

        payload = {int(k): v for k, v in questions_json().items()}
        logger.info("✅ Questions Kbis chargées depuis le catalogue (%s)", len(payload))
        return payload

    if type_document not in QUESTION_FILES:
        logger.warning(f"⚠️ Type de document '{type_document}' non trouvé dans QUESTION_FILES")
        logger.warning(f"⚠️ Types disponibles : {list(QUESTION_FILES.keys())}")
        
        # Cas spéciaux : types sans fichier de questions dédié
        if type_document in ["autorisation_commerciale", "type_inconnu"]:
            logger.info(f"ℹ️ Type '{type_document}' n'a pas de fichier de questions dédié (utilise calculer_score_generique)")
            # Retourner un dictionnaire vide pour ces types (ils utilisent calculer_score_generique)
            return {}
        
        # IMPORTANT: Ne pas utiliser Kbis par défaut automatiquement
        # Cela masquerait les problèmes de mapping
        # À la place, logger une erreur et lever une exception si le type est vraiment inconnu
        logger.error(f"❌ Type de document inconnu : '{type_document}'")
        logger.error(f"   Ce type n'est pas dans QUESTION_FILES et n'est pas un type spécial")
        logger.error(f"   Vérifiez que le type est correctement détecté et mappé dans QUESTION_FILES")
        
        # Pour les types vraiment inconnus, essayer de détecter le problème
        # Si c'est un type valide qui n'est juste pas dans QUESTION_FILES, utiliser un fallback
        # Mais logger l'erreur pour qu'elle soit visible
        if type_document in ["bilan_comptable"]:
            # Cas spécial : bilan_comptable est mappé à comptes_sociaux
            logger.warning(f"⚠️ Type 'bilan_comptable' détecté, utilisation de 'comptes_sociaux' à la place")
            type_document = "comptes_sociaux"
        else:
            # Pour les autres types inconnus, utiliser Kbis par défaut mais logger l'erreur
            logger.warning(f"⚠️ Utilisation du fichier Kbis par défaut (type inconnu: '{type_document}')")
            logger.warning(f"   ⚠️ ATTENTION: Cela peut causer des résultats incorrects !")
            type_document = "extrait_kbis"
    
    fichier = QUESTION_FILES.get(type_document)
    if not fichier:
        logger.error(f"❌ Aucun fichier de questions défini pour le type '{type_document}'")
        logger.warning(f"⚠️ Utilisation du fichier Kbis par défaut")
        fichier = QUESTION_FILES.get("extrait_kbis", "questions.json")
        type_document = "extrait_kbis"
    
    logger.info(f"✅ Fichier de questions sélectionné : '{fichier}' pour le type '{type_document}'")
    
    chemin = os.path.join(DOCUMENTS_ROOT, fichier)
    logger.info(f"📂 Chemin complet : {chemin}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(chemin):
        logger.error(f"❌ Le fichier de questions n'existe pas : {chemin}")
        logger.error(f"❌ DOCUMENTS_ROOT : {DOCUMENTS_ROOT}")
        logger.error(f"❌ Type de document : '{type_document}'")
        logger.error(f"❌ Fichier attendu : '{fichier}'")
        
        # Fallback sur Kbis si ce n'est pas déjà Kbis
        if type_document != "extrait_kbis":
            logger.warning(f"⚠️ Fallback sur les questions Kbis (fichier manquant pour '{type_document}')")
            logger.warning(f"   ⚠️ ATTENTION: Les questions Kbis peuvent ne pas être appropriées pour ce type de document !")
            return _charger_questions("extrait_kbis")
        
        # Si même Kbis n'existe pas, lever une exception
        raise FileNotFoundError(f"Fichier questions non trouvé : {chemin}")
    
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            questions_dict = json.load(f)
            questions = {int(k): v for k, v in questions_dict.items()}
            
            logger.info(f"✅ {len(questions)} questions chargées depuis '{fichier}'")
            logger.info(f"✅ Mapping confirmé : Type '{type_document}' → Fichier '{fichier}'")
            
            # Afficher les premières questions pour vérification
            if questions:
                first_q_key = min(questions.keys())
                first_q = questions[first_q_key]
                logger.info(f"📝 Première question (Q{first_q_key}) : {first_q[:80]}...")
                
                # Afficher toutes les clés de questions pour vérification
                question_keys = sorted(questions.keys())
                logger.info(f"📋 Questions disponibles ({len(question_keys)}): {question_keys}")
            else:
                logger.warning(f"⚠️ Aucune question trouvée dans le fichier '{fichier}'")
            
            logger.info(f"📋 === FIN CHARGEMENT DES QUESTIONS ===")
            return questions
    except FileNotFoundError:
        logger.error(f"❌ Fichier questions non trouvé : {chemin}")
        if type_document != "extrait_kbis":
            logger.warning(f"⚠️ Fallback sur les questions Kbis")
            return _charger_questions("extrait_kbis")
        raise FileNotFoundError(f"Fichier questions non trouvé : {chemin}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erreur de parsing JSON dans {chemin} : {e}")
        raise Exception(f"Erreur de parsing JSON dans {chemin} : {e}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement des questions ({chemin}) : {e}", exc_info=True)
        raise Exception(f"Erreur lors du chargement des questions ({chemin}) : {e}")


# Vérifier le mapping au démarrage (toujours, pas seulement en mode debug)
try:
    _verifier_mapping_type_questions()
except Exception as e:
    logger.error(f"❌ Erreur lors de la vérification du mapping : {e}", exc_info=True)


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

async def extraire_texte_pdf_async(fichier_pdf: str, max_chars: int = 15000, document_type: Optional[str] = None) -> str:
    """
    Extrait le texte d'un PDF de manière asynchrone.
    """
    loop = asyncio.get_event_loop()
    texte = await loop.run_in_executor(None, extraire_contenu_document, fichier_pdf, max_chars, document_type)
    return texte


def extraire_numero_rcs(texte: str) -> str:
    """
    Extrait le numéro RCS d'un texte.
    """
    if not texte:
        return "Pas de RCS"
    
    # Patterns pour trouver un RCS
    patterns = [
        r'RCS[:\s]+([A-Z\s]+[:\s]+)?(\d{3}[\s.]?\d{3}[\s.]?\d{3})',  # RCS Paris: 123 456 789
        r'(\d{3}[\s.]?\d{3}[\s.]?\d{3})',  # 123 456 789
        r'(\d{9})',  # 123456789
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, texte, re.IGNORECASE)
        if matches:
            # Prendre le dernier groupe capturé
            numero = matches[0][-1] if isinstance(matches[0], tuple) else matches[0]
            numero = numero.replace(' ', '').replace('.', '')
            
            if len(numero) == 9 and numero.isdigit():
                # Formater : 123 456 789
                return f"{numero[:3]} {numero[3:6]} {numero[6:]}"
    
    return "Pas de RCS"


def valider_score(score: Any) -> int:
    """
    Valide et nettoie un score.
    """
    try:
        if score is None or score == "":
            return 0
        
        score_num = float(score)
        
        # Vérifier les valeurs aberrantes
        if math.isnan(score_num) or math.isinf(score_num) or score_num > 1000:
            return 0
        
        # Limiter à un range raisonnable (0-100)
        score_int = int(score_num)
        return max(0, min(100, score_int))
        
    except (ValueError, TypeError, OverflowError):
        return 0


def nettoyer_reponse_groq(reponse: Any) -> str:
    """
    Nettoie une réponse de Groq.
    """
    if reponse is None:
        return ""
    
    if isinstance(reponse, tuple):
        # Si c'est un tuple d'erreur
        return reponse[0] if len(reponse) > 0 else ""
    
    reponse_str = str(reponse).strip()
    
    # Enlever les markdown
    reponse_str = reponse_str.replace("**", "").replace("*", "")
    
    return reponse_str


def nettoyer_json_pour_sauvegarde(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie toutes les données avant sauvegarde JSON.
    """
    # Nettoyer le score total
    if 'score_total' in data:
        data['score_total'] = valider_score(data['score_total'])
    
    # Nettoyer les scores détaillés
    if 'scores_detail' in data:
        data['scores_detail'] = {
            k: valider_score(v) 
            for k, v in data['scores_detail'].items()
        }
    
    # Nettoyer le RCS
    if 'rcs' in data and isinstance(data['rcs'], str):
        # Si RCS contient des chiffres énormes, le nettoyer
        if len(data['rcs']) > 50 or any(c.isdigit() and len(re.findall(r'\d+', data['rcs'])[0]) > 15 for c in data['rcs']):
            data['rcs'] = "Invalide"
    
    # Nettoyer les détails
    if 'details' in data:
        for detail in data['details']:
            if 'score' in detail:
                detail['score'] = valider_score(detail['score'])
    
    # Nettoyer les résultats
    if 'resultats' in data:
        if 'score_total' in data['resultats']:
            data['resultats']['score_total'] = valider_score(data['resultats']['score_total'])
        if 'scores_detail' in data['resultats']:
            data['resultats']['scores_detail'] = {
                k: valider_score(v)
                for k, v in data['resultats']['scores_detail'].items()
            }
    
    return data


# ============================================================
# PROMPTS GROQ OPTIMISÉS (conservés pour compatibilité avec Kbis)
# ============================================================

PROMPT_RCS = """Analyse ce document et réponds UNIQUEMENT par "Oui" ou "Non".

Question : L'entreprise possède-t-elle un numéro RCS (Registre du Commerce et des Sociétés) ?

Instructions :
- Cherche "RCS" suivi d'un numéro à 9 chiffres
- Réponds UNIQUEMENT par "Oui" ou "Non"
- Base-toi UNIQUEMENT sur le document

Document :
{texte}

Ta réponse :"""

PROMPT_CAPITAL = """Analyse ce document et réponds UNIQUEMENT par le montant du capital social en euros (sans le symbole €).

Question : Quel est le capital social de l'entreprise ?

Instructions :
- Cherche "Capital social" ou "Capital"
- Réponds UNIQUEMENT par le montant en euros (ex: "50000", "100000")
- Base-toi UNIQUEMENT sur le document

Document :
{texte}

Ta réponse :"""


def nettoyer_capital(reponse: str) -> str:
    """Nettoie une réponse de capital."""
    if not reponse:
        return "0"
    
    # Extraire les nombres
    nombres = re.findall(r'\d+', reponse.replace(' ', '').replace(',', '').replace('.', ''))
    if nombres:
        return nombres[0]
    return "0"


async def poser_question_binaire_async(question: str, texte: str) -> Tuple[str, str]:
    """Pose une question binaire à Groq."""
    prompt = f"""Analyse ce document et réponds UNIQUEMENT par "Oui" ou "Non".

Question : {question}

Instructions :
- Réponds UNIQUEMENT par "Oui" ou "Non"
- Base-toi UNIQUEMENT sur le document
- Si l'information est manquante, réponds "Non"

Document :
{texte[:3000]}

Ta réponse :"""
    
    reponse, erreur = await groq_call_async(prompt, temperature=0.2, max_tokens=50)
    
    if erreur:
        return "Indisponible", f"Erreur : {erreur}"
    
    reponse = nettoyer_reponse_groq(reponse)
    reponse_lower = reponse.lower().strip()
    
    if reponse_lower.startswith("oui"):
        return "Oui", "Réponse extraite du document"
    elif reponse_lower.startswith("non"):
        return "Non", "Réponse extraite du document"
    else:
        return "Non", "Réponse non claire"


async def extraire_forme_juridique_async(texte: str) -> Tuple[str, str]:
    """Extrait la forme juridique."""
    prompt = f"""Analyse ce document et réponds UNIQUEMENT par la forme juridique de l'entreprise.

Question : Quelle est la structure juridique de l'entreprise ?

Instructions :
- Cherche la forme juridique (SAS, SARL, SA, EURL, EI, SNC, etc.)
- Réponds UNIQUEMENT par la forme juridique (ex: "SAS", "SARL", "SA")
- Base-toi UNIQUEMENT sur le document

Document :
{texte[:3000]}

Ta réponse :"""
    
    reponse, erreur = await groq_call_async(prompt, temperature=0.2, max_tokens=50)
    
    if erreur:
        return "Indisponible", f"Erreur : {erreur}"
    
    reponse = nettoyer_reponse_groq(reponse)
    return reponse, "Forme juridique extraite du document"


async def extraire_capital_async(texte: str) -> Tuple[str, str]:
    """Extrait le capital social."""
    prompt = PROMPT_CAPITAL.format(texte=texte[:3000])
    
    reponse, erreur = await groq_call_async(prompt, temperature=0.2, max_tokens=50)
    
    if erreur:
        return "Indisponible", f"Erreur : {erreur}"
    
    reponse = nettoyer_reponse_groq(reponse)
    capital_nettoye = nettoyer_capital(reponse)
    
    return capital_nettoye, f"Capital extrait : {capital_nettoye} €"


async def extraire_nom_entreprise_async(texte: str, type_document: str) -> str:
    """
    Extrait le nom de l'entreprise depuis le texte du document.
    """
    prompt = f"""Tu es un assistant spécialisé dans l'extraction d'informations de documents d'entreprise.

Document :
{texte[:4000]}

Type de document : {type_document}

Instructions :
- Extrais le NOM COMPLET de l'entreprise (raison sociale)
- Pour un Kbis : cherche "Dénomination" ou "Raison sociale" ou "Nom commercial"
- Pour des comptes sociaux : cherche "Raison sociale" ou "Dénomination" ou "Nom de l'entreprise"
- Réponds UNIQUEMENT par le nom de l'entreprise, sans texte supplémentaire
- Si tu ne trouves pas de nom clair, réponds "Entreprise inconnue"
- Le nom doit être en majuscules ou avec capitalisation normale (pas de formatage spécial)

Exemples de bonnes réponses :
- "SOCIETE GENERALE"
- "Microsoft Corporation"
- "ACME SARL"
- "Entreprise inconnue" (si non trouvé)

Ta réponse (nom de l'entreprise uniquement) :"""

    try:
        reponse, erreur = await groq_call_async(prompt, temperature=0.2, max_tokens=200)
        
        if erreur:
            logger.warning(f"⚠️ Erreur lors de l'extraction du nom d'entreprise : {erreur}")
            return "Entreprise inconnue"
        
        nom = nettoyer_reponse_groq(reponse).strip()
        
        nom = nom.replace('"', '').replace("'", '').strip()
        nom = ' '.join(nom.split())
        
        # Si le nom est trop long ou semble invalide, retourner une valeur par défaut
        if len(nom) > 100 or nom.lower() in ["non trouvé", "non trouvée", "non disponible", "non précisé"]:
            logger.warning(f"⚠️ Nom d'entreprise invalide extrait : {nom}")
            return "Entreprise inconnue"
        
        if not nom or nom == "":
            return "Entreprise inconnue"
        
        logger.info(f"✅ Nom d'entreprise extrait : {nom}")
        return nom
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction du nom d'entreprise : {e}")
        return "Entreprise inconnue"


# ============================================================
# FONCTION PRINCIPALE D'ANALYSE
# ============================================================

async def analyser_questions_async(
    fichier_pdf: str,
    type_hint: Optional[str] = None,
    type_source: str = "inferred",
) -> Dict[str, Any]:
    """
    Analyse les questions d'un PDF et calcule les scores avec calculs.py.

    type_source=user : le type est un contexte explicite. Pas de détection.
    Cohérence structurelle minimale, sans Mistral. INCONNU documentaire conservé.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📄 Début analyse : {fichier_pdf}")
    
    type_document_key = None
    if type_hint:
        type_document_key = type_hint
        logger.info(f"✅ Type fourni ({type_source}) : {type_document_key}")
    else:
        logger.info("⚠️ Aucun type_hint fourni, détection automatique depuis le contenu")
    
    # Extraire le texte - utiliser type_document_key pour optimiser l'extraction
    texte_pdf = await extraire_texte_pdf_async(fichier_pdf, max_chars=15000, document_type=type_document_key)
    
    if not texte_pdf or len(texte_pdf) < 100:
        raise Exception("Impossible d'extraire le texte du PDF ou texte trop court")
    
    logger.info(f"📝 Texte extrait : {len(texte_pdf)} caractères")

    if type_source == "user":
        if not is_selectable(type_hint):
            raise DocumentTypeMismatch(type_hint or "", "Type de document non supporté.")
        type_document_key = type_hint
        verdict = check_coherence(type_document_key, texte_pdf)
        if not verdict["coherent"]:
            raise DocumentTypeMismatch(type_document_key, verdict["message"])
        logger.info("📎 Type utilisateur confirmé par indices structurels : %s", verdict["hits"])
    elif not type_hint:
        try:
            type_document_key_detected = detecter_type_document(texte_pdf)
            logger.info(f"🔍 Type détecté depuis le texte : {type_document_key_detected}")
            type_document_key = type_document_key_detected
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la détection du type : {e}")
            type_document_key = "type_inconnu"
    
    # S'assurer qu'on a un type valide
    if not type_document_key or type_document_key == "type_inconnu":
        logger.warning(f"⚠️ Type de document inconnu, utilisation par défaut : type_inconnu")
        type_document_key = "type_inconnu"
    
    logger.info(f"🔍 Type de document final utilisé : {type_document_key}")
    type_document_label = formatter_type_document(type_document_key)
    logger.info(f"📝 Label du type de document : {type_document_label}")
    
    # Charger les questions avec le type correct
    # Vérification explicite que le bon fichier est utilisé
    logger.info(f"🔍 === VÉRIFICATION DU MAPPING TYPE → FICHIER DE QUESTIONS ===")
    logger.info(f"🔍 Type de document final utilisé : '{type_document_key}'")
    logger.info(f"🔍 Type_hint fourni : {type_hint}")
    logger.info(f"🔍 Label du type : '{type_document_label}'")
    
    if type_document_key in QUESTION_FILES:
        fichier_attendu = QUESTION_FILES[type_document_key]
        logger.info(f"✅ Mapping trouvé : '{type_document_key}' → '{fichier_attendu}'")
    else:
        logger.warning(f"⚠️ Mapping non trouvé pour '{type_document_key}'")
        if type_document_key in ["autorisation_commerciale", "type_inconnu"]:
            logger.info(f"ℹ️ Type '{type_document_key}' n'utilise pas de fichier de questions (calculer_score_generique)")
        else:
            logger.warning(f"⚠️ Type inconnu dans QUESTION_FILES, vérification en cours...")
            logger.warning(f"   Types disponibles : {list(QUESTION_FILES.keys())}")
    
    # Charger les questions - cette fonction va logger en détail quel fichier est utilisé
    questions = _charger_questions(type_document_key)
    logger.info(f"📋 {len(questions)} questions chargées pour le type '{type_document_key}'")
    
    if questions:
        first_q_key = min(questions.keys())
        first_q = questions[first_q_key]
        logger.info(f"📝 Première question (Q{first_q_key}) : {first_q[:80]}...")
        logger.info(f"📋 Toutes les questions chargées : {sorted(questions.keys())}")
        logger.info(f"✅ Le bon fichier de questions a été utilisé pour le type '{type_document_key}'")
    else:
        if type_document_key in ["autorisation_commerciale", "type_inconnu"]:
            logger.info(f"ℹ️ Aucune question chargée pour '{type_document_key}' (normal, utilise calculer_score_generique)")
        else:
            logger.warning(f"⚠️ Aucune question chargée pour le type '{type_document_key}' (anormal)")
            logger.warning(f"   ⚠️ ATTENTION: Cela peut causer des problèmes dans l'analyse !")
    
    nom_entreprise = (
        extract_company_name(texte_pdf)
        or os.path.splitext(os.path.basename(fichier_pdf))[0]
    )
    logger.info("Nom d'entreprise (règles) : %s", nom_entreprise)

    reponses: Dict[int, Any] = {}
    justifications: Dict[int, str] = {}
    extraction_methods: Dict[int, str] = {}
    evaluation_statuses: Dict[int, str] = {}
    extraction_meta: Dict[str, Any] = {
        "pipeline": "texte → faits → règles → fallback",
        "mistral_calls": 0,
        "facts": None,
    }

    evaluations_by_q = {}
    if type_document_key in EXTRACTORS:
        pages = extract_pages(fichier_pdf)
        fact_set = extract_facts(type_document_key, texte_pdf, pages=pages)
        if fact_set and fact_set.get("denomination") and fact_set["denomination"].present:
            nom_entreprise = str(fact_set["denomination"].value)
        if type_document_key == "extrait_kbis":
            missing_facts = expected_unknown_facts(fact_set)
            if missing_facts:
                overrides = await extract_missing_facts_mistral(texte_pdf, missing_facts)
                apply_fact_overrides(fact_set, overrides)
                extraction_meta["mistral_calls"] = 1 if overrides else 0
            else:
                logger.info("Aucun appel Mistral : faits attendus déjà lus")
        extraction_meta["facts"] = fact_set.to_dict() if fact_set else None
        evaluations_by_q = evaluate_facts(type_document_key, fact_set) or {}
        resolved = 0
        for index, evaluation in evaluations_by_q.items():
            reponses[index] = evaluation.answer
            justifications[index] = evaluation.rationale
            evaluation_statuses[index] = evaluation.status
            extraction_methods[index] = (
                evaluation.evidence.source if evaluation.evidence else "facts"
            )
            if evaluation.status == EVAL_INCONNU:
                extraction_methods[index] = "inconnu"
            else:
                resolved += 1
            if evaluation.evidence:
                extraction_meta.setdefault("evidence", {})[str(index)] = evaluation.evidence.to_dict()
            logger.info("Q%s %s ← %s", index, evaluation.status, evaluation.condition)
        logger.info("%s : %s/%s questions tranchées par faits", type_document_key, resolved, len(evaluations_by_q))
    elif type_document_key == "bilan_comptable":
        logger.info("Type bilan_comptable : extraction financière historique")
        for i in sorted(questions.keys()):
            reponses[i] = "Calculé"
            justifications[i] = "En attente de calcul"
    else:
        missing = list(sorted(questions.items()))
        extras, nom_fb = await fill_unresolved_with_mistral(texte_pdf, missing, nom_demande=True)
        extraction_meta["mistral_calls"] = 1 if missing else 0
        if nom_fb:
            nom_entreprise = nom_fb
        for index, (reponse, justification) in extras.items():
            reponses[index] = reponse
            justifications[index] = justification
            extraction_methods[index] = "mistral_fallback"
    
    logger.info("🧮 Calcul des scores...")
    
    # Pour les comptes sociaux / Kbis : impacts depuis les évaluations (INCONNU → 0)
    if type_document_key == "comptes_sociaux" and evaluations_by_q:
        scores_detail = impacts_from_comptes(evaluations_by_q)
        resolved = sum(1 for ev in evaluations_by_q.values() if ev.status != EVAL_INCONNU)
        resultats_brut = {
            "score_total": sum(scores_detail.values()),
            "scores_detail": scores_detail,
            "precision": (resolved / len(evaluations_by_q) * 100) if evaluations_by_q else 0.0,
        }
    elif type_document_key == "extrait_kbis" and evaluations_by_q:
        scores_detail = impacts_from_kbis(evaluations_by_q)
        resolved = sum(1 for ev in evaluations_by_q.values() if ev.status != EVAL_INCONNU)
        resultats_brut = {
            "score_total": sum(scores_detail.values()),
            "scores_detail": scores_detail,
            "precision": (resolved / len(evaluations_by_q) * 100) if evaluations_by_q else 0.0,
        }
    elif type_document_key == "comptes_sociaux":
        try:
            logger.info("📊 Extraction des valeurs financières des comptes sociaux...")
            valeurs_comptes = extraire_valeurs_comptes_sociaux(texte_pdf, format_type="texte")
            logger.info("🧮 Calcul du score des comptes sociaux...")
            resultats_brut = calculer_score_comptes_sociaux(valeurs_comptes)
        except Exception as e:
            logger.error(f"❌ Erreur calcul score comptes sociaux : {e}", exc_info=True)
            resultats_brut = {"score_total": 0, "scores_detail": {}}
    # Compatibilité avec l'ancien système (bilan_comptable)
    elif type_document_key == "bilan_comptable":
        try:
            logger.info("📊 Extraction des valeurs financières du bilan...")
            # extraire_valeurs_bilan est déjà importé en haut du fichier
            valeurs_bilan = extraire_valeurs_bilan(texte_pdf, format_type="texte")
            logger.info("🧮 Calcul du score du bilan...")
            resultats_brut = calculer_score_bilan(valeurs_bilan)
        except Exception as e:
            logger.error(f"❌ Erreur calcul score bilan : {e}", exc_info=True)
            resultats_brut = {"score_total": 0, "scores_detail": {}}
    else:
        # Pour les autres types de documents, utiliser le calculateur standard
        try:
            calculateur = CALCULATEURS_DOCUMENTS.get(type_document_key, calculer_score_generique)
            resultats_brut = calculateur(reponses)
        except Exception as e:
            logger.error(f"❌ Erreur calcul scores : {e}", exc_info=True)
            resultats_brut = {"score_total": 0, "scores_detail": {}}
    
    raw_score = resultats_brut.get("score_total", 0)
    precision = resultats_brut.get("precision")
    if precision is None:
        precision = 0.0 if type_document_key == "extrait_kbis" else 100.0
    scores_detail = resultats_brut.get("scores_detail", {})
    
    if type_document_key == "extrait_kbis" and precision == 0.0:
        precision = resultats_brut.get("precision", 0.0)
    
    # Synchroniser les réponses et justifications calculées pour comptes sociaux et bilan
    if type_document_key in ["comptes_sociaux", "bilan_comptable"]:
        reponses_calc = resultats_brut.get("reponses") or {}
        justifs_calc = resultats_brut.get("justifications") or {}
        logger.info(f"📊 Synchronisation des réponses calculées : {len(reponses_calc)} réponses pour {len(questions)} questions")
        
        # Remplacer les réponses "Calculé" par les vraies valeurs calculées
        for key, value in reponses_calc.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                idx = key
            if idx in questions:  # Vérifier que la question existe
                reponses[idx] = value
                logger.debug(f"  ✅ Q{idx}: {value}")
        
        for key, value in justifs_calc.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                idx = key
            if idx in questions:  # Vérifier que la question existe
                justifications[idx] = value
        
        # Vérifier que toutes les questions ont une réponse
        for i in questions.keys():
            if i not in reponses:
                logger.warning(f"⚠️ Question {i} n'a pas de réponse calculée, utilisation de 'Non précisé'")
                reponses[i] = "Non précisé"
                justifications[i] = "Données indisponibles pour cette question"
        
        logger.info(f"✅ {len(reponses)} réponses synchronisées sur {len(questions)} questions")
    
    score_normalise = min(max(int(raw_score), 0), 100)
    niveau_risque = determiner_niveau_risque_score(score_normalise)
    risk_color = determiner_couleur_risque(score_normalise)

    if type_document_key == "extrait_kbis":
        a_un_rcs = reponses.get(1, "")
        a_un_siren = reponses.get(2, "")
        justification_rcs = justifications.get(1, "") or justifications.get(2, "")
        if str(a_un_rcs).lower() == "oui" or str(a_un_siren).lower() == "oui":
            numero_rcs = extraire_numero_rcs(justification_rcs + " " + texte_pdf[:1000])
        else:
            numero_rcs = "Pas de RCS"
        forme_fact = None
        if evaluations_by_q:
            # La forme est un fait, pas la réponse Oui/Non de Q4.
            facts_meta = (extraction_meta.get("facts") or {})
            forme_payload = facts_meta.get("forme_juridique") or {}
            forme_fact = forme_payload.get("value")
        type_entreprise = str(forme_fact or reponses.get(4, "") or type_document_label)
    else:
        numero_rcs = "Non applicable"
        type_entreprise = type_document_label
    
    # Construire les détails avec les questions chargées
    details = []
    # Utiliser les questions chargées plutôt que question_items (qui peut ne pas être défini pour comptes sociaux)
    for i in sorted(questions.keys()):
        question = questions[i]
        reponse = reponses.get(i, "Non précisé")
        justification = justifications.get(i, "Aucune justification")
        extraction_failed = str(justification).startswith("Erreur :")
        evaluation_status = evaluation_statuses.get(int(i))
        unknown_fact = evaluation_status == EVAL_INCONNU or str(reponse) == "Inconnu"
        score = 0 if extraction_failed or unknown_fact else scores_detail.get(i, scores_detail.get(str(i), 0))
        evidence = (extraction_meta.get("evidence") or {}).get(str(i), {})
        details.append({
            "question": question,
            "question_index": int(i),
            "reponse": str(reponse),
            "justification": str(justification),
            "score": int(score) if score else 0,
            "extraction_failed": extraction_failed,
            "evaluation_status": evaluation_status,
            "extraction_method": extraction_methods.get(int(i), "inconnu"),
            "evidence": {
                "reponse": str(reponse),
                "justification": str(justification),
                "page": evidence.get("page"),
                "snippet": evidence.get("snippet"),
                "matched_pattern": evidence.get("matched_pattern"),
                "method": "regle_deterministe",
            },
        })

    breakdown = apply_deterministic_scoring(
        details,
        type_document_key,
        pages=extract_pages(fichier_pdf),
    )
    score_normalise = min(max(int(round(breakdown["score_global"])), 0), 100)
    niveau_risque = breakdown["niveau_risque"]
    risk_color = breakdown["risk_color"]

    # Construire le résultat final
    resultat_final = {
        "reponses": reponses,
        "justifications": justifications,
        "questions": questions,
        "details": details,
        "resultats": {
            "score_total": score_normalise,
            "niveau_risque": niveau_risque,
            "niveau_risque_label": breakdown["niveau_risque_label"],
            "precision": precision,
            "scores_detail": scores_detail,
            "score_brut": raw_score,
            "score_breakdown": breakdown,
        },
        "nom": nom_entreprise,
        "type": type_entreprise,
        "rcs": numero_rcs,
        "score_total": score_normalise,
        "score_global": breakdown["score_global"],
        "niveau_risque": niveau_risque,
        "niveau_risque_label": breakdown["niveau_risque_label"],
        "risque": niveau_risque,
        "precision": precision,
        "score": score_normalise,
        "risk_color": risk_color,
        "score_breakdown": breakdown,
        "document_type": type_document_label,
        "document_type_key": type_document_key,
        "extraction": extraction_meta,
        "slug": "",  # Sera rempli par main.py
    }
    
    # NETTOYER TOUTES LES DONNÉES
    resultat_final = nettoyer_json_pour_sauvegarde(resultat_final)
    
    return resultat_final
