"""OCR local, uniquement si le PDF n'a pas de couche texte exploitable.

Ce n'est pas une étape d'analyse ni de scoring.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "3"))


def extract_text_ocr(pdf_path: str) -> str:
    """Tente un OCR local. Chaîne vide si l'outil n'est pas installé."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.info("OCR ignoré : pytesseract/pdf2image non installés")
        return ""

    try:
        pages = convert_from_path(pdf_path, first_page=1, last_page=OCR_MAX_PAGES)
    except Exception as exc:
        logger.warning("OCR impossible (rendu PDF) : %s", exc)
        return ""

    chunks = []
    for page in pages:
        try:
            chunks.append(pytesseract.image_to_string(page, lang="fra+eng") or "")
        except Exception as exc:
            logger.warning("OCR page échouée : %s", exc)
    return "\n".join(chunks).strip()
