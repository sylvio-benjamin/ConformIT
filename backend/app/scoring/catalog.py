"""Référentiel de règles : traduction opérationnelle des questions.

Une règle interprète une réponse déjà extraite. Elle ne lit pas le document.
Le moteur de scoring ne dépend donc ni de l'OCR, ni d'un LLM.

Pour le Kbis, les RULE-* viennent du catalogue de connaissances
(`extraction.kbis.catalog`). Pas d'un second barème parallèle.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

Rule = Dict[str, object]

RULE_VERSION = "1.0"


def _rule(
    rule_id: str,
    risk_type: str,
    severity: str,
    max_impact: int,
    title: str,
    question: str,
    condition: str,
    referentiel: str,
) -> Rule:
    return {
        "id": rule_id,
        "referentiel": referentiel,
        "question": question,
        "risk_type": risk_type,
        "severity": severity,
        "max_impact": max_impact,
        "condition": condition,
        "version": RULE_VERSION,
        "title": title,
    }


def _kbis_rules() -> Dict[int, Rule]:
    from app.extraction.kbis.catalog import kbis_scoring_rules

    return {
        index: {
            "id": payload["id"],
            "referentiel": payload.get("referentiel", "extrait_kbis"),
            "question": payload.get("question", ""),
            "risk_type": payload["risk_type"],
            "severity": payload["severity"],
            "max_impact": payload["max_impact"],
            "condition": payload["condition"],
            "version": payload.get("version", RULE_VERSION),
            "title": payload["title"],
            "trigger": payload.get("trigger"),
        }
        for index, payload in kbis_scoring_rules().items()
    }


_DOC_DEFAULT_TYPE = {
    "extrait_kbis": "juridique",
    "comptes_sociaux": "financier",
    "bilan_comptable": "financier",
    "compte_resultat": "financier",
    "liasse_fiscale": "financier",
    "releve_bancaire": "financier",
    "statuts": "juridique",
    "attestation_assurance": "conformite",
    "autorisation_commerciale": "administratif",
    "type_inconnu": "administratif",
}

_PREFIX = {
    "juridique": "JUR",
    "financier": "FIN",
    "conformite": "COM",
    "administratif": "ADM",
    "reputation": "REP",
}

DEFAULT_MAX_IMPACT = 10


def default_risk_type(document_type: str) -> str:
    return _DOC_DEFAULT_TYPE.get(document_type or "", "administratif")


def _normalize_question(text: str) -> str:
    lowered = str(text).lower()
    accents = str.maketrans("éèêëàâäùûüôöîïç", "eeeeaaauuuooiic")
    lowered = lowered.translate(accents)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", lowered).split())


def _kbis_by_question(question: Optional[str]) -> Optional[Rule]:
    if not question:
        return None
    needle = _normalize_question(question)
    if not needle:
        return None
    best: Optional[Rule] = None
    best_overlap = 0
    for rule in _kbis_rules().values():
        title = _normalize_question(str(rule["question"]))
        if needle[:40] in title or title[:40] in needle:
            return dict(rule)
        overlap = len(set(needle.split()) & set(title.split()))
        if overlap >= 5 and overlap > best_overlap:
            best = dict(rule)
            best_overlap = overlap
    return best


def lookup_rule(
    document_type: str,
    question_index: int,
    question: Optional[str] = None,
) -> Rule:
    if document_type == "extrait_kbis":
        rules = _kbis_rules()
        if question_index in rules:
            return dict(rules[question_index])
    matched = _kbis_by_question(question)
    if matched:
        return matched
    risk_type = default_risk_type(document_type)
    prefix = _PREFIX[risk_type]
    title = (question or f"Règle {document_type or 'document'} Q{question_index}")[:120]
    return _rule(
        f"RULE-{prefix}-{question_index:03d}",
        risk_type,
        "moyenne",
        DEFAULT_MAX_IMPACT,
        title,
        question or title,
        "pénalité du calculateur > 0",
        document_type or "document",
    )


def rules_for_document(document_type: str, question_indexes) -> Dict[int, Rule]:
    return {int(idx): lookup_rule(document_type, int(idx)) for idx in question_indexes}
