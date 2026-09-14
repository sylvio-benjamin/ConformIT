"""
Module de parsing PDF avec support de l'API PDF Vector pour les documents complexes.
Utilise l'extraction basique PyPDF2 pour les documents simples (kbis, attestation).
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import PyPDF2
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# Constantes
# Note: L'API PDF Vector peut ne pas être disponible ou avoir une URL différente
# Pour l'instant, on utilise principalement PyPDF2 avec fallback sur PDF Vector si disponible
PDF_VECTOR_API_URL = "https://api.pdfvector.com/v1/parse"  # URL corrigée
PDF_VECTOR_API_KEY = os.getenv("PDF_VECTOR_API_KEY")
SIMPLE_DOCUMENTS = ["kbis", "attestation", "extrait_kbis", "attestation_assurance"]
REQUEST_TIMEOUT = 30  # secondes (réduit pour éviter les attentes trop longues)
USE_PDF_VECTOR = False  # Désactivé par défaut jusqu'à ce que l'API soit correctement configurée
MIN_USABLE_CHARS = 200


class PDFParserError(Exception):
    """Exception personnalisée pour les erreurs de parsing PDF."""
    pass


def is_simple_document(document_type: str) -> bool:
    """
    Détermine si un document est simple (kbis, attestation).
    
    Args:
        document_type: Type de document (ex: "kbis", "bilan_comptable")
    
    Returns:
        True si le document est simple, False sinon
    """
    if not document_type:
        return False
    doc_type_lower = document_type.lower().replace("_", "")
    return any(simple in doc_type_lower for simple in ["kbis", "attestation"])


def _read_pdf_text(pdf_path: str) -> str:
    """Lit la couche texte du PDF. Peut être vide (document scanné)."""
    if not os.path.exists(pdf_path):
        raise PDFParserError(f"Fichier PDF introuvable : {pdf_path}")
    texte = ""
    try:
        with open(pdf_path, "rb") as f:
            lecteur = PyPDF2.PdfReader(f)
            max_pages = min(10, len(lecteur.pages))
            for i in range(max_pages):
                page_text = lecteur.pages[i].extract_text()
                if page_text:
                    texte += page_text + "\n"
                    if len(texte) >= 50000:
                        break
    except Exception as e:
        raise PDFParserError(f"Erreur lors de l'extraction simple : {str(e)}")
    return texte


def extract_text_simple(pdf_path: str) -> str:
    """
    Extraction basique avec PyPDF2.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        Texte extrait du PDF
    
    Raises:
        PDFParserError: Si l'extraction échoue
    """
    texte = _read_pdf_text(pdf_path)
    if not texte or len(texte.strip()) < 100:
        raise PDFParserError("Texte extrait trop court ou vide")
    return texte


def extract_with_pdf_vector(pdf_path: str) -> Dict[str, Any]:
    """
    Extraction via API PDF Vector.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        Dictionnaire contenant les données extraites par l'API
    
    Raises:
        PDFParserError: Si l'extraction échoue
    """
    if not os.path.exists(pdf_path):
        raise PDFParserError(f"Fichier PDF introuvable : {pdf_path}")
    
    if not PDF_VECTOR_API_KEY:
        raise PDFParserError("Clé API PDF Vector manquante (PDF_VECTOR_API_KEY)")
    
    if not USE_PDF_VECTOR:
        raise PDFParserError("API PDF Vector désactivée (USE_PDF_VECTOR=False)")
    
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            headers = {
                "Authorization": f"Bearer {PDF_VECTOR_API_KEY}"
            }
            
            response = requests.post(
                PDF_VECTOR_API_URL,
                files=files,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                # Ne pas logger le contenu HTML complet de la réponse 404
                error_preview = response.text[:200] if len(response.text) > 200 else response.text
                error_msg = f"Erreur API PDF Vector (status {response.status_code}): {error_preview}"
                raise PDFParserError(error_msg)
            
            data = response.json()
            return data
            
    except requests.exceptions.Timeout:
        raise PDFParserError(f"Timeout lors de l'appel à l'API PDF Vector (>{REQUEST_TIMEOUT}s)")
    except requests.exceptions.RequestException as e:
        raise PDFParserError(f"Erreur réseau lors de l'appel à l'API PDF Vector : {str(e)}")
    except Exception as e:
        raise PDFParserError(f"Erreur lors de l'extraction PDF Vector : {str(e)}")


def parse_pdf(pdf_path: str, document_type: str) -> Dict[str, Any]:
    """
    Fonction principale qui choisit automatiquement la méthode d'extraction.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        document_type: Type de document (ex: "kbis", "bilan_comptable")
    
    Returns:
        Dictionnaire avec les clés :
        - method: "simple" | "pdf_vector" | "pdf_vector_fallback"
        - text: str (si méthode simple)
        - data: dict (si méthode pdf_vector)
        - success: bool
    """
    if not os.path.exists(pdf_path):
        return {
            "method": "error",
            "success": False,
            "error": f"Fichier introuvable : {pdf_path}"
        }
    
    try:
        texte = _read_pdf_text(pdf_path)
    except PDFParserError as e:
        return {"method": "error", "success": False, "error": str(e)}

    if len(texte.strip()) >= MIN_USABLE_CHARS:
        logger.info("Document parsé avec : simple")
        return {"method": "simple", "text": texte, "success": True}

    logger.info(
        "Texte simple insuffisant (%s car.) — OCR en fallback, pas d'analyse",
        len(texte.strip()),
    )
    from app.extraction.ocr import extract_text_ocr

    ocr_text = extract_text_ocr(pdf_path)
    if len(ocr_text.strip()) >= MIN_USABLE_CHARS:
        logger.info("Document parsé avec : ocr")
        return {"method": "ocr", "text": ocr_text, "success": True}

    if USE_PDF_VECTOR and PDF_VECTOR_API_KEY:
        try:
            data = extract_with_pdf_vector(pdf_path)
            return {"method": "pdf_vector_fallback", "data": data, "success": True}
        except PDFParserError as e2:
            logger.warning("PDF Vector indisponible : %s", e2)

    if texte.strip():
        logger.info("Document parsé avec : simple (texte mince)")
        return {"method": "simple", "text": texte, "success": True, "thin_text": True}
    if ocr_text.strip():
        return {"method": "ocr", "text": ocr_text, "success": True, "thin_text": True}
    return {
        "method": "error",
        "success": False,
        "error": "Aucune couche texte exploitable (OCR local indisponible ou vide)",
    }


def get_text_from_result(parse_result: Dict[str, Any]) -> str:
    """
    Extrait le texte du résultat de parsing.
    
    Args:
        parse_result: Résultat de parse_pdf()
    
    Returns:
        Texte extrait du document
    
    Raises:
        PDFParserError: Si le texte ne peut pas être extrait
    """
    if not parse_result.get("success"):
        error = parse_result.get("error", "Erreur inconnue")
        raise PDFParserError(f"Parsing échoué : {error}")
    
    method = parse_result.get("method", "")
    
    # Si méthode simple, le texte est directement disponible
    if method in ("simple", "ocr", "pdf_vector_fallback") and "text" in parse_result:
        return parse_result["text"]
    
    # Si méthode PDF Vector, extraire le texte des données
    if method == "pdf_vector" or method == "pdf_vector_fallback":
        if "data" in parse_result:
            data = parse_result["data"]
            # Adapter selon la structure de réponse de l'API PDF Vector
            # (à ajuster selon leur documentation réelle)
            if isinstance(data, dict):
                # Essayer différents champs possibles
                text = data.get("text") or data.get("content") or data.get("extracted_text")
                if text:
                    return str(text)
                
                # Si c'est une structure avec pages
                if "pages" in data and isinstance(data["pages"], list):
                    text_parts = []
                    for page in data["pages"]:
                        if isinstance(page, dict):
                            page_text = page.get("text") or page.get("content")
                            if page_text:
                                text_parts.append(str(page_text))
                    if text_parts:
                        return "\n".join(text_parts)
            
            # Si aucune structure connue, convertir en string
            return str(data)
    
    raise PDFParserError(f"Impossible d'extraire le texte de la méthode : {method}")

