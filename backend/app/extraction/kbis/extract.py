"""Extracteur de faits Kbis. Ne répond à aucune question."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional

from app.extraction.kbis.patterns import EXPECTED_FACTS, FACT_PATTERNS, FOREIGN_COUNTRIES, FORME_LABELS
from app.extraction.model import (
    STATUS_ABSENT,
    STATUS_PRESENT,
    STATUS_UNKNOWN,
    Evidence,
    Fact,
    FactSet,
)
from app.extraction.normalize import (
    clean_spaces,
    first_match,
    fold,
    is_negated,
    locate_page,
    parse_amount,
    parse_date,
    snippet,
)


def _evidence(text: str, start: int, end: int, pattern: str, keywords: List[str], pages=None) -> Evidence:
    excerpt = snippet(text, start, end)
    return Evidence(
        source="pdf_text",
        snippet=excerpt,
        matched_pattern=pattern,
        page=locate_page(pages, excerpt),
        matched_keywords=keywords,
    )


def _unknown(name: str) -> Fact:
    return Fact(name=name, type=FACT_PATTERNS[name]["type"], status=STATUS_UNKNOWN)


def _extract_siren(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["siren"]
    if first_match(folded, spec["negations"]):
        match = first_match(folded, spec["negations"])
        return Fact(
            "siren",
            spec["type"],
            STATUS_ABSENT,
            None,
            _evidence(original, match.start(), match.end(), match.group(0), ["negation"], pages),
        )
    for label in spec["labels"]:
        pattern = label + r"[^\d]{0,40}" + spec["value"]
        match = re.search(pattern, folded, re.IGNORECASE)
        if not match:
            continue
        if is_negated(folded, match.start()):
            return Fact(
                "siren",
                spec["type"],
                STATUS_ABSENT,
                None,
                _evidence(original, match.start(), match.end(), label, ["siren", "negation"], pages),
            )
        digits = re.sub(r"\D", "", match.group(1))
        if len(digits) == 9:
            return Fact(
                "siren",
                spec["type"],
                STATUS_PRESENT,
                digits,
                _evidence(original, match.start(), match.end(), label, ["siren", "rcs"], pages),
            )
    return _unknown("siren")


def _extract_denomination(original: str, folded: str, pages=None) -> Fact:
    match = re.search(
        r"(?:d[eéè]nomination(?:\s+sociale)?|raison sociale)\s*[:\-]\s*(.+)",
        original,
        re.IGNORECASE,
    )
    if not match:
        return _unknown("denomination")
    if is_negated(folded, 0) and first_match(folded, [r"pas de denomination", r"sans denomination"]):
        return Fact("denomination", "texte", STATUS_ABSENT, None)
    name = clean_spaces(match.group(1).split("\n")[0])
    name = re.split(r"\b(forme juridique|capital social|si[eè]ge|rcs|siren)\b", name, maxsplit=1, flags=re.I)[0]
    name = name.strip(" :-")
    if 2 < len(name) < 160:
        return Fact(
            "denomination",
            "texte",
            STATUS_PRESENT,
            name,
            _evidence(original, match.start(), match.end(), "denomination", ["denomination"], pages),
        )
    return _unknown("denomination")


def _extract_labeled_text(name: str, original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS[name]
    for label in spec["labels"]:
        match = re.search(label + spec.get("value", r"[:\-]\s*(.+)"), folded, re.IGNORECASE)
        if not match:
            continue
        if is_negated(folded, match.start()):
            return Fact(name, spec["type"], STATUS_ABSENT, None, _evidence(original, match.start(), match.end(), label, [name], pages))
        value = clean_spaces(match.group(1).split("\n")[0])
        value = re.split(r"\b(forme juridique|capital social|siege|rcs|siren)\b", value, maxsplit=1)[0]
        value = value.strip(" :-")
        if 2 < len(value) < 160:
            return Fact(name, spec["type"], STATUS_PRESENT, value, _evidence(original, match.start(), match.end(), label, [name], pages))
    return _unknown(name)


def _extract_forme(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["forme_juridique"]
    labeled = None
    label_used = "forme juridique"
    for label in spec["labels"]:
        match = re.search(label + r".{0,80}", folded, re.IGNORECASE)
        if match:
            labeled = match.group(0)
            label_used = label
            start = match.start()
            break
    else:
        return _unknown("forme_juridique")
    for needle, code in FORME_LABELS:
        if re.search(rf"\b{re.escape(needle)}\b", labeled):
            return Fact(
                "forme_juridique",
                spec["type"],
                STATUS_PRESENT,
                code,
                _evidence(original, start, start + len(labeled), label_used, [code, "forme juridique"], pages),
            )
    return _unknown("forme_juridique")


def _extract_amount(name: str, original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS[name]
    for label in spec["labels"]:
        match = re.search(label + r"[^\d]{0,24}" + spec["value"], folded, re.IGNORECASE)
        if not match:
            continue
        if is_negated(folded, match.start()):
            return Fact(name, spec["type"], STATUS_ABSENT, None, _evidence(original, match.start(), match.end(), label, [name], pages))
        amount = parse_amount(match.group(1))
        if amount is not None:
            return Fact(name, spec["type"], STATUS_PRESENT, amount, _evidence(original, match.start(), match.end(), label, [name], pages))
    return _unknown(name)


def _extract_date(name: str, original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS[name]
    for label in spec["labels"]:
        match = re.search(label + r".{0,48}", folded, re.IGNORECASE)
        if not match:
            continue
        parsed = parse_date(match.group(0))
        if parsed:
            return Fact(
                name,
                spec["type"],
                STATUS_PRESENT,
                parsed.isoformat(),
                _evidence(original, match.start(), match.end(), label, [name], pages),
            )
    return _unknown(name)


def _extract_duree(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["duree_societe"]
    if first_match(folded, spec["indeterminee"]):
        match = first_match(folded, spec["indeterminee"])
        return Fact(
            "duree_societe",
            spec["type"],
            STATUS_PRESENT,
            "indéterminée",
            _evidence(original, match.start(), match.end(), match.group(0), ["duree", "indeterminee"], pages),
        )
    for label in spec["labels"]:
        match = re.search(label + r"[^\d]{0,40}" + spec["value"], folded, re.IGNORECASE)
        if match:
            return Fact(
                "duree_societe",
                spec["type"],
                STATUS_PRESENT,
                int(match.group(1)),
                _evidence(original, match.start(), match.end(), label, ["duree"], pages),
            )
    return _unknown("duree_societe")


def _extract_duree_nature(original: str, folded: str, pages=None, duree: Optional[Fact] = None) -> Fact:
    if duree and duree.present and duree.value == "indéterminée":
        return Fact(
            "duree_nature",
            "enum",
            STATUS_PRESENT,
            "indéterminée",
            duree.evidence,
        )
    if duree and duree.present and isinstance(duree.value, int):
        return Fact(
            "duree_nature",
            "enum",
            STATUS_PRESENT,
            "déterminée",
            duree.evidence,
        )
    if first_match(folded, FACT_PATTERNS["duree_societe"]["indeterminee"]):
        match = first_match(folded, FACT_PATTERNS["duree_societe"]["indeterminee"])
        return Fact(
            "duree_nature",
            "enum",
            STATUS_PRESENT,
            "indéterminée",
            _evidence(original, match.start(), match.end(), match.group(0), ["duree"], pages),
        )
    return _unknown("duree_nature")


def _extract_etat_activite(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["etat_activite"]
    for pattern in spec["inactif"]:
        match = re.search(pattern, folded, re.IGNORECASE)
        if match:
            return Fact(
                "etat_activite",
                spec["type"],
                STATUS_PRESENT,
                "inactif",
                _evidence(original, match.start(), match.end(), pattern, ["etat_activite"], pages),
            )
    for pattern in spec["actif"]:
        match = re.search(pattern, folded, re.IGNORECASE)
        if match:
            return Fact(
                "etat_activite",
                spec["type"],
                STATUS_PRESENT,
                "actif",
                _evidence(original, match.start(), match.end(), pattern, ["etat_activite"], pages),
            )
    return _unknown("etat_activite")


def _extract_mention_rcs(original: str, folded: str, pages=None) -> Fact:
    return _extract_flag("mention_rcs", original, folded, pages)


def _extract_dirigeants(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["dirigeants_count"]
    hits = []
    for label in spec["labels"]:
        hits.extend(re.finditer(label, folded, re.IGNORECASE))
    if not hits:
        return _unknown("dirigeants_count")
    # Une section dirigeants compte au moins 1 ; plusieurs labels distincts → estimation.
    count = max(1, len({match.group(0) for match in hits}))
    first = hits[0]
    return Fact(
        "dirigeants_count",
        spec["type"],
        STATUS_PRESENT,
        count,
        _evidence(original, first.start(), first.end(), first.group(0), ["dirigeant"], pages),
    )


def _extract_dirigeant_fonction(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["dirigeant_fonction"]
    match = first_match(folded, spec["labels"])
    if not match:
        return _unknown("dirigeant_fonction")
    return Fact(
        "dirigeant_fonction",
        spec["type"],
        STATUS_PRESENT,
        clean_spaces(match.group(0)),
        _evidence(original, match.start(), match.end(), match.group(0), ["fonction"], pages),
    )


def _extract_etablissement_principal(original: str, folded: str, pages=None) -> Fact:
    return _extract_adresse("etablissement_principal", original, folded, pages)


def _extract_cac(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["commissaire_comptes"]
    label_match = first_match(folded, spec["labels"])
    if not label_match:
        return _unknown("commissaire_comptes")
    window = folded[label_match.start() : label_match.start() + 160]
    if first_match(window, spec["negations"]) or is_negated(folded, label_match.start()):
        return Fact(
            "commissaire_comptes",
            spec["type"],
            STATUS_PRESENT,
            False,
            _evidence(original, label_match.start(), label_match.end(), "negation", ["commissaire aux comptes"], pages),
        )
    after = window[label_match.end() - label_match.start() :]
    if re.search(r"[a-z]{3,}", after):
        return Fact(
            "commissaire_comptes",
            spec["type"],
            STATUS_PRESENT,
            True,
            _evidence(original, label_match.start(), label_match.end() + 40, "commissaire aux comptes", ["commissaire aux comptes"], pages),
        )
    return _unknown("commissaire_comptes")


def _extract_etablissements(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["nombre_etablissements"]
    match = first_match(folded, [label + r"\s*[:\-]?\s*" + spec["value"] for label in spec["labels"]])
    if match:
        return Fact(
            "nombre_etablissements",
            spec["type"],
            STATUS_PRESENT,
            int(match.group(1)),
            _evidence(original, match.start(), match.end(), "nombre etablissements", ["etablissement"], pages),
        )
    secondaires = len(re.findall(spec["secondaire"], folded))
    if secondaires:
        return Fact(
            "nombre_etablissements",
            spec["type"],
            STATUS_PRESENT,
            1 + secondaires,
            Evidence(source="pdf_text", snippet="établissement secondaire", matched_pattern="secondaire", matched_keywords=["etablissement secondaire"]),
        )
    if re.search(spec["principal"], folded):
        return Fact(
            "nombre_etablissements",
            spec["type"],
            STATUS_PRESENT,
            1,
            Evidence(source="pdf_text", snippet="établissement principal", matched_pattern="principal", matched_keywords=["etablissement principal"]),
        )
    return _unknown("nombre_etablissements")


def _extract_nationalite(original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS["nationalite"]
    match = first_match(folded, [label + spec["value"] for label in spec["labels"]])
    if not match:
        return _unknown("nationalite")
    value = match.group(1)
    return Fact(
        "nationalite",
        spec["type"],
        STATUS_PRESENT,
        "Française" if value.startswith("franc") else value.capitalize(),
        _evidence(original, match.start(), match.end(), "nationalite", ["nationalite"], pages),
    )


def _extract_flag(name: str, original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS[name]
    match = first_match(folded, spec["labels"])
    if not match:
        return _unknown(name)
    return Fact(
        name,
        spec["type"],
        STATUS_PRESENT,
        True,
        _evidence(original, match.start(), match.end(), match.group(0), [name], pages),
    )


def _extract_adresse(name: str, original: str, folded: str, pages=None) -> Fact:
    spec = FACT_PATTERNS[name]
    match = first_match(folded, [label + r"\s*[:\-]?\s*(.{8,120})" for label in spec["labels"]])
    if not match:
        return _unknown(name)
    return Fact(
        name,
        spec["type"],
        STATUS_PRESENT,
        clean_spaces(match.group(1).split("\n")[0])[:160],
        _evidence(original, match.start(), match.end(), spec["labels"][0], [name], pages),
    )


def extract_facts_kbis(
    texte: str,
    pages: Optional[List[Dict[str, Any]]] = None,
    as_of: Optional[date] = None,
) -> FactSet:
    """Texte normalisé → faits typés. Aucune question, aucun score."""
    folded = fold(texte)
    duree = _extract_duree(texte, folded, pages)
    facts = [
        _extract_siren(texte, folded, pages),
        _extract_mention_rcs(texte, folded, pages),
        _extract_denomination(texte, folded, pages),
        _extract_forme(texte, folded, pages),
        _extract_amount("capital_social", texte, folded, pages),
        _extract_flag("capital_variable", texte, folded, pages),
        _extract_date("date_immatriculation", texte, folded, pages),
        _extract_date("date_debut_activite", texte, folded, pages),
        _extract_etat_activite(texte, folded, pages),
        duree,
        _extract_duree_nature(texte, folded, pages, duree),
        _extract_cac(texte, folded, pages),
        _extract_etablissements(texte, folded, pages),
        _extract_etablissement_principal(texte, folded, pages),
        _extract_nationalite(texte, folded, pages),
        _extract_adresse("adresse_siege", texte, folded, pages),
        _extract_flag("transfert_siege", texte, folded, pages),
        _extract_adresse("adresse_dirigeant", texte, folded, pages),
        _extract_dirigeants(texte, folded, pages),
        _extract_dirigeant_fonction(texte, folded, pages),
        _extract_flag("mention_procedure", texte, folded, pages),
    ]
    return FactSet(facts)


def expected_unknown_facts(facts: FactSet) -> List[str]:
    return [name for name in EXPECTED_FACTS if facts[name].status == STATUS_UNKNOWN]


def apply_fact_overrides(facts: FactSet, overrides: Dict[str, Any]) -> FactSet:
    """Fusionne un fallback ciblé. La valeur reste un fait typé, pas une phrase."""
    mapping = {
        "siren": ("identifiant", str),
        "forme_juridique": ("enum", str),
        "capital_social": ("montant", int),
    }
    for name, raw in (overrides or {}).items():
        if name not in mapping or raw in (None, "", "Non précisé", "Inconnu"):
            continue
        kind, caster = mapping[name]
        try:
            value = caster(raw) if kind != "montant" else int(re.sub(r"\D", "", str(raw)) or 0)
        except (TypeError, ValueError):
            continue
        if value in (None, "", 0):
            continue
        facts.replace(
            Fact(
                name=name,
                type=kind,
                status=STATUS_PRESENT,
                value=value if name != "forme_juridique" else str(value).upper(),
                evidence=Evidence(source="mistral_fallback", snippet=str(raw), matched_pattern=name),
            )
        )
    return facts
