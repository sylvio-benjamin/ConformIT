"""Extraction de pages (texte + numéro) pour localiser une preuve."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def extract_pages(pdf_path: str, max_pages: int = 20) -> List[Dict[str, Any]]:
    if not pdf_path:
        return []
    try:
        import PyPDF2
    except ImportError:
        return []
    pages: List[Dict[str, Any]] = []
    try:
        with open(pdf_path, "rb") as handle:
            reader = PyPDF2.PdfReader(handle)
            limit = min(max_pages, len(reader.pages))
            for index in range(limit):
                text = reader.pages[index].extract_text() or ""
                pages.append({"number": index + 1, "text": text})
    except Exception as exc:
        logger.debug("Extraction des pages indisponible : %s", exc)
        return []
    return pages
