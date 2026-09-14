"""Extracteur de faits comptes. Ne répond à aucune question."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.extraction.comptes.patterns import AMOUNT_LABELS, AMBIGUOUS_FACTS, EXPECTED_FACTS
from app.extraction.model import STATUS_PRESENT, STATUS_UNKNOWN, Evidence, Fact, FactSet
from app.extraction.normalize import fold, locate_page, snippet

AMOUNT_AFTER_LABEL = re.compile(r"\s*[:\-]?\s*(\d(?:[\s\u00a0]?\d){2,})")


def _evidence_for(name: str, texte: str, pages=None) -> Evidence:
    labels = AMOUNT_LABELS.get(name, (name,))
    lowered = fold(texte)
    for label in labels:
        index = lowered.find(fold(label))
        if index >= 0:
            excerpt = snippet(texte, index, index + len(label))
            return Evidence(
                source="pdf_text",
                snippet=excerpt,
                matched_pattern=label,
                page=locate_page(pages, excerpt),
                matched_keywords=[label],
            )
    return Evidence(source="pdf_text", snippet="", matched_pattern=name, matched_keywords=[name])


def _read_amount(texte: str, labels: tuple) -> Optional[int]:
    folded = fold(texte)
    for label in labels:
        match = re.search(re.escape(fold(label)) + AMOUNT_AFTER_LABEL.pattern, folded)
        if not match:
            continue
        digits = re.sub(r"\D", "", match.group(1))
        if len(digits) >= 3:
            return int(digits)
    return None


def _amount(name: str, texte: str, pages=None) -> Fact:
    value = _read_amount(texte, AMOUNT_LABELS.get(name, (name,)))
    if value is None:
        return Fact(name, "montant", STATUS_UNKNOWN)
    return Fact(name, "montant", STATUS_PRESENT, value, _evidence_for(name, texte, pages))


def _ratio(name: str, numerateur: Optional[Fact], denominateur: Optional[Fact]) -> Fact:
    if not numerateur or not denominateur or not numerateur.present or not denominateur.present:
        return Fact(name, "ratio", STATUS_UNKNOWN)
    if denominateur.value in (0, 0.0):
        return Fact(name, "ratio", STATUS_UNKNOWN)
    evidence = numerateur.evidence or denominateur.evidence
    return Fact(name, "ratio", STATUS_PRESENT, float(numerateur.value) / float(denominateur.value), evidence)


def extract_facts_comptes(texte: str, pages: Optional[List[Dict[str, Any]]] = None, **_: Any) -> FactSet:
    amounts = [_amount(name, texte, pages) for name in AMOUNT_LABELS]
    by_name = {fact.name: fact for fact in amounts}
    if not by_name["actif_circulant"].present:
        parts = [by_name[key] for key in ("disponibilites", "creances_clients", "stocks") if by_name[key].present]
        if parts:
            total = sum(int(part.value) for part in parts)
            by_name["actif_circulant"] = Fact(
                "actif_circulant",
                "montant",
                STATUS_PRESENT,
                total,
                parts[0].evidence,
            )
    derived = [
        _ratio("ratio_liquidite", by_name.get("actif_circulant"), by_name.get("dettes_court_terme")),
        _ratio("ratio_endettement", by_name.get("dettes_financieres"), by_name.get("capitaux_propres")),
        _ratio("ratio_autonomie", by_name.get("capitaux_propres"), by_name.get("total_passif")),
    ]
    return FactSet(list(by_name.values()) + derived)


def expected_unknown_facts(facts: FactSet) -> List[str]:
    return [name for name in EXPECTED_FACTS if facts.get(name) and facts[name].status == STATUS_UNKNOWN]


def ambiguous_unknown_facts(facts: FactSet) -> List[str]:
    return [name for name in AMBIGUOUS_FACTS if not facts.get(name) or facts[name].status == STATUS_UNKNOWN]
