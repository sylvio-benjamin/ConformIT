"""Scoring déterministe, agnostique du référentiel.

Le moteur ne sait pas s'il traite un Kbis, ISO 27001 ou le RGPD.
Il reçoit des règles déjà interprétées (famille, impact, plafond, preuve)
et applique toujours : B_r → S_r → pondération → S_global.

Le catalogue de questions (lookup_rule) est en amont. Pas dans le calcul.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set

from app.scoring.catalog import lookup_rule
from app.scoring.config import (
    RISK_TYPE_LABELS,
    couleur_from_score,
    niveau_from_score,
    weights,
)

LAYERS = (
    "extraction",
    "rules",
    "findings",
    "family_scores",
    "weights",
    "global_score",
    "level",
)


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _snippet(body: str, needle: str, radius: int = 80) -> str:
    index = body.lower().find(needle.lower())
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(body), index + len(needle) + radius)
    excerpt = body[start:end].strip()
    if start > 0:
        excerpt = "…" + excerpt
    if end < len(body):
        excerpt = excerpt + "…"
    return excerpt


def locate_evidence(
    *candidates: Any,
    pages: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Remonte un fait jusqu'au texte et à la page, sans interpréter le risque."""
    found = {"page": None, "snippet": None, "method": "regle_deterministe"}
    if not pages:
        return found
    needles = []
    for raw in candidates:
        text = str(raw or "").strip()
        if len(text) >= 8:
            needles.append(text[:80])
    for needle in needles:
        for page in pages:
            body = str(page.get("text") or "")
            if needle.lower() in body.lower():
                found["page"] = page.get("number")
                found["snippet"] = _snippet(body, needle)
                return found
    return found


def normalize_type_score(brut: float, cap: float) -> float:
    """S_r = min(100, B_r / Cap_r * 100)."""
    if cap <= 0:
        return 0.0
    return round(min(100.0, (float(brut) / float(cap)) * 100.0), 2)


def renormalize_weights(applicable: Set[str], source: Optional[Dict[str, int]] = None) -> Dict[str, float]:
    """Retire les familles hors référentiel du document, puis renormalise à 100."""
    source = source or weights()
    relevant = {key: source[key] for key in applicable if key in source}
    total = sum(relevant.values()) or 100
    return {key: round(value * 100 / total, 2) for key, value in relevant.items()}


def weighted_global(by_type: Dict[str, Dict[str, Any]]) -> float:
    """S_global = Σ (S_r × W_r) / 100."""
    return round(sum(row["score"] * row["weight"] for row in by_type.values()) / 100.0, 2)


def is_extraction_error(text: Any) -> bool:
    value = str(text or "")
    return (
        value.startswith("Erreur :")
        or "Rate limit exceeded" in value
        or "Erreur API Mistral" in value
        or "Erreur API Groq" in value
    )


def _scorable(item: Dict[str, Any]) -> bool:
    return bool(item.get("risk_type")) and not item.get("extraction_failed")


def aggregate_from_rules(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Agrège des règles déjà interprétées. Aucune connaissance du référentiel."""
    all_weights = weights()
    applicable = {item.get("risk_type") for item in details if _scorable(item)}
    renormalized = renormalize_weights(applicable, all_weights)
    by_type: Dict[str, Dict[str, Any]] = {}
    for risk in applicable:
        rules = [item for item in details if item.get("risk_type") == risk and not item.get("extraction_failed")]
        brut = sum(_to_int(item.get("impact")) for item in rules if item.get("triggered"))
        cap = sum(_to_int(item.get("max_impact")) for item in rules) or 1
        score = 0.0 if brut <= 0 else normalize_type_score(brut, cap)
        weight = renormalized.get(risk, 0)
        by_type[risk] = {
            "risk_type": risk,
            "label": RISK_TYPE_LABELS.get(risk, risk),
            "score": score,
            "brut": brut,
            "cap": cap,
            "weight": weight,
            "weight_source": all_weights.get(risk, 0),
            "contribution": round(score * weight / 100.0, 2),
            "formula": f"min(100, {brut}/{cap}*100) = {score}",
            "rules": [
                {
                    "rule_id": item.get("rule_id"),
                    "version": item.get("rule_version"),
                    "referentiel": item.get("rule_referentiel"),
                    "question": item.get("question") or item.get("rule_title"),
                    "condition": item.get("rule_condition"),
                    "title": item.get("rule_title"),
                    "impact": item.get("impact"),
                    "max_impact": item.get("max_impact"),
                    "triggered": item.get("triggered"),
                    "finding": item.get("justification") or item.get("reponse"),
                    "fact": item.get("reponse"),
                    "page": (item.get("evidence") or {}).get("page"),
                    "snippet": (item.get("evidence") or {}).get("snippet"),
                }
                for item in rules
                if item.get("triggered")
            ],
        }

    global_score = weighted_global(by_type)
    label_fr, label_en = niveau_from_score(global_score)
    return {
        "engine": "deterministic_v1",
        "referential_agnostic": True,
        "layers": list(LAYERS),
        "formula": {
            "B_r": "sum(I_i)",
            "S_r": "min(100, B_r / Cap_r * 100)",
            "S_global": "sum(S_r * W_r) / 100",
        },
        "score_global": global_score,
        "niveau_risque": label_en,
        "niveau_risque_label": label_fr,
        "risk_color": couleur_from_score(global_score),
        "weights": renormalized,
        "weights_source": all_weights,
        "by_type": by_type,
        "explainable": True,
        "llm_in_decision_loop": False,
        "extraction_incomplete": any(item.get("extraction_failed") for item in details),
        "extraction_failed_count": sum(1 for item in details if item.get("extraction_failed")),
    }


def apply_deterministic_scoring(
    details: List[Dict[str, Any]],
    document_type: str,
    pages: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Lie les questions du référentiel, puis délègue au moteur agnostique."""
    for index, item in enumerate(details, start=1):
        q_index = _to_int(item.get("question_index") or item.get("numero") or index)
        rule = lookup_rule(document_type, q_index, question=item.get("question"))
        justification = str(item.get("justification") or "")
        extraction_failed = bool(item.get("extraction_failed") or is_extraction_error(justification))
        unknown = str(item.get("evaluation_status") or "") == "INCONNU" or str(
            item.get("reponse") or ""
        ) in {"Inconnu", "INCONNU"}
        item["extraction_failed"] = extraction_failed
        item["evaluation_status"] = "INCONNU" if unknown else item.get("evaluation_status")
        impact = 0 if extraction_failed or unknown else _to_int(
            item.get("score") if item.get("impact") is None else item.get("impact")
        )
        triggered = impact > 0 and not extraction_failed and not unknown
        evidence = locate_evidence(
            item.get("justification"),
            item.get("reponse"),
            f"{item.get('reponse') or ''} {item.get('justification') or ''}",
            pages=pages,
        )
        if item.get("page") is not None:
            evidence["page"] = item.get("page")
        prior = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        item["question_index"] = q_index
        item["rule_id"] = rule["id"]
        item["rule_version"] = rule["version"]
        item["rule_referentiel"] = rule["referentiel"]
        item["rule_condition"] = rule["condition"]
        item["risk_type"] = rule["risk_type"]
        item["rule_title"] = rule["title"]
        item["rule_severity"] = rule["severity"]
        item["max_impact"] = rule["max_impact"]
        item["impact"] = impact
        item["triggered"] = triggered
        item["evidence"] = {
            **prior,
            "reponse": item.get("reponse"),
            "justification": item.get("justification"),
            "page": evidence.get("page") or prior.get("page"),
            "snippet": evidence.get("snippet") or prior.get("snippet"),
            "method": "regle_deterministe",
        }
    return aggregate_from_rules(details)


def _stale_extraction_breakdown(data: Dict[str, Any]) -> bool:
    details = data.get("details") or []
    if not any(
        item.get("extraction_failed") or is_extraction_error(item.get("justification"))
        for item in details
        if isinstance(item, dict)
    ):
        return False
    breakdown = data.get("score_breakdown") or {}
    if float(breakdown.get("score_global") or 0) > 0 and all(
        isinstance(item, dict)
        and (item.get("extraction_failed") or is_extraction_error(item.get("justification")))
        for item in details
    ):
        return True
    for family in (breakdown.get("by_type") or {}).values():
        for rule in family.get("rules") or []:
            if is_extraction_error(rule.get("finding")):
                return True
    return False


def attach_breakdown_if_missing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recalcule le breakdown à la lecture si une ancienne analyse n'en a pas."""
    if not isinstance(data, dict):
        return data
    details = data.get("details")
    if not isinstance(details, list) or not details:
        return data
    if data.get("score_breakdown") and not _stale_extraction_breakdown(data):
        return data
    document_type = (
        data.get("document_type_key")
        or data.get("type_document_key")
        or ""
    )
    breakdown = apply_deterministic_scoring(details, str(document_type))
    data["score_breakdown"] = breakdown
    data["score_global"] = breakdown["score_global"]
    data["niveau_risque_label"] = breakdown["niveau_risque_label"]
    data["niveau_risque"] = breakdown["niveau_risque"]
    data["risk_color"] = breakdown["risk_color"]
    data["score_total"] = min(max(int(round(breakdown["score_global"])), 0), 100)
    if isinstance(data.get("resultats"), dict):
        data["resultats"]["score_breakdown"] = breakdown
        data["resultats"]["score_total"] = data["score_total"]
        data["resultats"]["niveau_risque"] = breakdown["niveau_risque"]
        data["resultats"]["niveau_risque_label"] = breakdown["niveau_risque_label"]
    return data
