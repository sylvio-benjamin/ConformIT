"""Catalogue des types sélectionnables. Connaissance, pas moteur.

Le type est un contexte explicite fourni en amont.
Il oriente l'EXTRACTOR et les questions. Il ne calcule rien.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

TYPE_CONTEXT_RULE = (
    "Le type de document est un contexte explicite fourni en amont, "
    "pas une déduction du moteur."
)

SELECTOR_REDUCES_STRUCTURAL_UNKNOWN = True
SELECTOR_PRESERVES_DOCUMENTARY_UNKNOWN = True

SELECTABLE_DOCUMENT_TYPES: Tuple[Dict[str, str], ...] = (
    {
        "id": "extrait_kbis",
        "label": "Kbis",
        "upload_prompt": "Déposez votre Kbis.",
        "mismatch": (
            "Ce document ne semble pas correspondre à un Kbis. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "comptes_sociaux",
        "label": "Comptes sociaux",
        "upload_prompt": "Déposez vos comptes sociaux.",
        "mismatch": (
            "Ce document ne semble pas correspondre à des comptes sociaux. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "bilan_comptable",
        "label": "Bilan comptable",
        "upload_prompt": "Déposez votre bilan comptable.",
        "mismatch": (
            "Ce document ne semble pas correspondre à un bilan comptable. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "compte_resultat",
        "label": "Compte de résultat",
        "upload_prompt": "Déposez votre compte de résultat.",
        "mismatch": (
            "Ce document ne semble pas correspondre à un compte de résultat. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "liasse_fiscale",
        "label": "Liasse fiscale",
        "upload_prompt": "Déposez votre liasse fiscale.",
        "mismatch": (
            "Ce document ne semble pas correspondre à une liasse fiscale. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "releve_bancaire",
        "label": "Relevé bancaire",
        "upload_prompt": "Déposez votre relevé bancaire.",
        "mismatch": (
            "Ce document ne semble pas correspondre à un relevé bancaire. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "statuts",
        "label": "Statuts",
        "upload_prompt": "Déposez vos statuts.",
        "mismatch": (
            "Ce document ne semble pas correspondre à des statuts. "
            "Vérifiez le type sélectionné."
        ),
    },
    {
        "id": "attestation_assurance",
        "label": "Attestation d'assurance",
        "upload_prompt": "Déposez votre attestation d'assurance.",
        "mismatch": (
            "Ce document ne semble pas correspondre à une attestation d'assurance. "
            "Vérifiez le type sélectionné."
        ),
    },
)

SELECTABLE_IDS = frozenset(item["id"] for item in SELECTABLE_DOCUMENT_TYPES)

DOCUMENT_TYPE_LABELS = {
    item["id"]: item["label"] for item in SELECTABLE_DOCUMENT_TYPES
}
DOCUMENT_TYPE_LABELS.update({
    "autorisation_commerciale": "Autorisation commerciale",
    "type_inconnu": "Document non identifié",
})


def public_catalog() -> List[Dict[str, str]]:
    return [
        {
            "id": item["id"],
            "label": item["label"],
            "upload_prompt": item["upload_prompt"],
        }
        for item in SELECTABLE_DOCUMENT_TYPES
    ]


def is_selectable(document_type: Optional[str]) -> bool:
    return bool(document_type) and document_type in SELECTABLE_IDS


def label_for(document_type: str) -> str:
    return DOCUMENT_TYPE_LABELS.get(document_type, document_type.replace("_", " ").title())


def mismatch_message(document_type: str) -> str:
    for item in SELECTABLE_DOCUMENT_TYPES:
        if item["id"] == document_type:
            return item["mismatch"]
    return "Ce document ne semble pas correspondre au type sélectionné. Vérifiez le type."


def catalog_entry(document_type: str) -> Optional[Dict[str, Any]]:
    for item in SELECTABLE_DOCUMENT_TYPES:
        if item["id"] == document_type:
            return dict(item)
    return None
