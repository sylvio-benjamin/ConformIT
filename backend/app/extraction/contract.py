"""Contrat de sortie des extracteurs. Indépendant du référentiel et du scoring.

Extraire ≠ évaluer ≠ scorer.
"""

from __future__ import annotations

from typing import Any, Dict

from app.extraction.model import (
    EVAL_INCONNU,
    EVAL_NON,
    EVAL_NON_APPLICABLE,
    EVAL_OUI,
    EVAL_VALEUR,
    STATUS_ABSENT,
    STATUS_PRESENT,
    STATUS_UNKNOWN,
    Evaluation,
    Fact,
    FactSet,
)

SEPARATION_RULE = "Extraire ≠ évaluer ≠ scorer."

PIPELINE = (
    "pdf",
    "texte",
    "normalisation",
    "extractor",
    "faits_types",
    "conditions",
    "reponse",
    "rules",
    "findings",
    "aggregate_from_rules",
)

FACT_STATUSES = frozenset({STATUS_PRESENT, STATUS_ABSENT, STATUS_UNKNOWN})
EVAL_STATUSES = frozenset({EVAL_OUI, EVAL_NON, EVAL_INCONNU, EVAL_NON_APPLICABLE, EVAL_VALEUR})
FACT_REQUIRED_KEYS = ("fact", "type", "status", "value")
EVIDENCE_KEYS = ("source", "matched_pattern", "snippet", "page")
FACT_TYPES = frozenset({
    "identifiant", "texte", "enum", "montant", "date", "duree", "booleen", "entier", "adresse", "ratio",
})
FORBIDDEN_VALUE_MARKERS = (
    "erreur api",
    "rate limit",
    "je pense",
    "d'après le document",
    "selon le document",
    "il semblerait",
)
MAX_CONTROLLED_TEXT = 160
UNKNOWN_ANSWERS = frozenset({"Inconnu", "INCONNU"})

INVARIANTS = (
    "Un mot trouvé n'est jamais directement une réponse",
    "Un fait present doit satisfaire ses critères de contexte",
    "Une négation peut produire absent",
    "L'absence de preuve produit INCONNU, pas une supposition",
    "INCONNU n'est pas une erreur : le document ne permet pas de conclure",
    "Un fait a une source et une preuve (source, matched_pattern, snippet, page)",
    "La base ne stocke pas de raisonnement ou de phrase inventée par le LLM",
    "Une question n'évalue que des faits : elle ne connaît pas Mistral",
    "Une règle transforme le résultat en impact/finding : elle ne connaît pas Mistral",
    "aggregate_from_rules ne connaît rien du référentiel",
    "OCR est uniquement une préoccupation d'extraction, en amont",
)


def assert_controlled_value(fact: Fact) -> None:
    """Un FactSet n'est pas une collection de phrases libres."""
    if fact.type not in FACT_TYPES:
        raise ValueError(f"Type de fait hors vocabulaire : {fact.type}")
    value = fact.value
    if value is None:
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_VALUE_MARKERS):
            raise ValueError("FactSet refuse une phrase d'IA ou une erreur d'extraction")
        if len(value) > MAX_CONTROLLED_TEXT:
            raise ValueError("FactSet refuse un texte libre trop long")
        if fact.type == "identifiant" and not value.isdigit():
            raise ValueError("identifiant hors contrat")
        if fact.type == "enum" and (len(value) > 32 or "\n" in value):
            raise ValueError("enum hors contrat")
        if fact.type == "date" and len(value) != 10:
            raise ValueError("date hors contrat")
    elif fact.type in {"montant", "entier", "duree", "ratio"}:
        if fact.type == "duree" and value == "indéterminée":
            return
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("valeur numérique hors contrat")
    elif fact.type == "booleen" and not isinstance(value, bool):
        raise ValueError("booléen hors contrat")


def assert_fact_contract(fact: Fact) -> None:
    if fact.status not in FACT_STATUSES:
        raise ValueError(f"Statut de fait hors contrat : {fact.status}")
    payload = fact.to_dict()
    for key in FACT_REQUIRED_KEYS:
        if key not in payload:
            raise ValueError(f"Fait incomplet : {key}")
    if fact.status == STATUS_PRESENT and fact.evidence is None:
        raise ValueError(f"Fait present sans preuve : {fact.name}")
    assert_controlled_value(fact)


def assert_factset_contract(facts: FactSet) -> None:
    if not isinstance(facts, FactSet):
        raise TypeError("L'extracteur doit retourner un FactSet")
    for name in facts.names():
        assert_fact_contract(facts[name])


def assert_evaluation_contract(evaluation: Evaluation) -> None:
    if evaluation.status not in EVAL_STATUSES:
        raise ValueError(f"Statut d'évaluation hors contrat : {evaluation.status}")
    if evaluation.status == EVAL_INCONNU and evaluation.answer not in UNKNOWN_ANSWERS:
        raise ValueError("INCONNU ne doit pas inventer une réponse métier")
    if evaluation.status == EVAL_INCONNU and evaluation.answer in {"Oui", "Non", "OUI", "NON"}:
        raise ValueError("INCONNU ne doit pas être converti en OUI ou NON")


def serialize_facts(facts: FactSet) -> Dict[str, Any]:
    """Seuls des faits contrôlés : jamais une phrase LLM."""
    assert_factset_contract(facts)
    return facts.to_dict()


def unknown_is_not_an_error(evaluation: Evaluation) -> bool:
    return evaluation.status == EVAL_INCONNU
