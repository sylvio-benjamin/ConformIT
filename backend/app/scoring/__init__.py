"""Socle produit : extraction → règles → scoring → GRC.

Le scoring est un moteur déterministe indépendant de l'OCR et de l'extraction.
"""

from app.scoring.engine import apply_deterministic_scoring, attach_breakdown_if_missing

__all__ = ["apply_deterministic_scoring", "attach_breakdown_if_missing"]
