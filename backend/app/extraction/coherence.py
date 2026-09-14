"""Vérification minimale de cohérence type ↔ document. Sans Mistral.

Le sélecteur réduit l'inconnu structurel. Il ne supprime pas l'inconnu
documentaire : un Kbis cohérent peut toujours laisser Q16 en INCONNU.
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Dict, Optional, Tuple

from app.extraction.document_types import is_selectable, mismatch_message
from app.extraction.model import FactSet
from app.extraction.normalize import fold
from app.extraction.registry import EXTRACTORS, extract_facts

USES_MISTRAL = False

# Indices structurels attendus. Un hit suffit : contrôle minimal, pas classification.
COHERENCE_MARKERS: Dict[str, Tuple[str, ...]] = {
    "extrait_kbis": (
        r"extrait k\s*bis",
        r"registre du commerce",
        r"\bsiren\b",
        r"\br\.?\s*c\.?\s*s\.?\b",
        r"immatriculation",
        r"\bgreffe\b",
    ),
    "comptes_sociaux": (
        r"comptes sociaux",
        r"comptes annuels",
        r"chiffre d['’ ]affaires",
        r"capitaux propres",
        r"compte de resultat",
        r"annexe comptable",
    ),
    "bilan_comptable": (
        r"\bbilan\b",
        r"total actif",
        r"total passif",
        r"actif",
        r"passif",
    ),
    "compte_resultat": (
        r"compte de resultat",
        r"chiffre d['’ ]affaires",
        r"resultat net",
        r"resultat d['’ ]exploitation",
    ),
    "liasse_fiscale": (
        r"liasse fiscale",
        r"\bcerfa\b",
        r"declaration fiscale",
        r"\b2050\b",
        r"\b2052\b",
        r"impot sur les societes",
    ),
    "releve_bancaire": (
        r"releve bancaire",
        r"\biban\b",
        r"\bbic\b",
        r"\bsolde\b",
        r"\bcredit\b",
        r"\bdebit\b",
    ),
    "statuts": (
        r"\bstatuts\b",
        r"objet social",
        r"capital social",
        r"assemblee (generale|constitutive)",
        r"\barticle\s+1\b",
    ),
    "attestation_assurance": (
        r"attestation",
        r"assurance",
        r"numero de police",
        r"compagnie d['’ ]assurance",
        r"contrat d['’ ]assurance",
    ),
}

STRUCTURAL_FACTS: Dict[str, Tuple[str, ...]] = {
    "extrait_kbis": ("siren",),
    "comptes_sociaux": ("chiffre_affaires", "capitaux_propres"),
}

MIN_HITS = 1


class DocumentTypeMismatch(ValueError):
    """Le PDF n'a aucun indice structurel du type choisi."""

    def __init__(self, document_type: str, message: Optional[str] = None):
        self.document_type = document_type
        self.message = message or mismatch_message(document_type)
        super().__init__(self.message)


def _fact_hits(document_type: str, facts: Optional[FactSet]) -> Tuple[str, ...]:
    if not facts:
        return ()
    found = []
    for name in STRUCTURAL_FACTS.get(document_type, ()):
        fact = facts.get(name)
        if fact is not None and fact.present:
            found.append(name)
    return tuple(found)


def _marker_hits(document_type: str, text: str) -> Tuple[str, ...]:
    folded = fold(text or "")
    found = []
    for pattern in COHERENCE_MARKERS.get(document_type, ()):
        if re.search(pattern, folded, re.IGNORECASE):
            found.append(pattern)
    return tuple(found)


def check_coherence(
    document_type: str,
    text: str,
    facts: Optional[FactSet] = None,
) -> Dict[str, Any]:
    """Cohérent si un indice structurel est présent. Sinon blocage."""
    if not is_selectable(document_type):
        raise DocumentTypeMismatch(
            document_type or "",
            "Type de document non supporté.",
        )
    local_facts = facts
    if local_facts is None and document_type in EXTRACTORS:
        local_facts = extract_facts(document_type, text or "")
    hits = list(_fact_hits(document_type, local_facts)) + list(_marker_hits(document_type, text))
    coherent = len(hits) >= MIN_HITS
    return {
        "document_type": document_type,
        "coherent": coherent,
        "hits": hits,
        "status": "coherent" if coherent else "incoherent",
        "message": None if coherent else mismatch_message(document_type),
        "uses_mistral": USES_MISTRAL,
        "preserves_documentary_unknown": True,
    }


def assert_no_mistral() -> None:
    module = inspect.getmodule(check_coherence)
    for value in vars(module).values():
        origin = getattr(value, "__module__", "") or ""
        if "mistral" in origin:
            raise AssertionError("La cohérence ne doit pas appeler Mistral")
