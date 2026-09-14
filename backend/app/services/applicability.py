"""Moteur d'applicabilité : profil orga × règles globales → frameworks applicables.

Aucun texte ISO intégral : codes, titres, raisons courtes uniquement.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "code": "ISO31000_BASE",
        "framework_code": "iso31000",
        "condition": {},
        "reason": "Socle de gestion des risques pour toute organisation",
    },
    {
        "code": "RGPD_PII",
        "framework_code": "rgpd",
        "condition": {"processes_personal_data": True},
        "reason": "Traitement de données personnelles",
    },
    {
        "code": "RGPD_EEA",
        "framework_code": "rgpd",
        "condition": {"country": ["FR", "BE", "DE", "ES", "IT", "NL", "PT", "LU", "IE", "AT"]},
        "reason": "Établissement dans l'Espace économique européen",
    },
    {
        "code": "ISO27005_CRIT",
        "framework_code": "iso27005",
        "condition": {"criticality": ["high", "critical"]},
        "reason": "Criticité élevée des activités",
    },
    {
        "code": "ISO27005_CLOUD",
        "framework_code": "iso27005",
        "condition": {"hosting": ["cloud", "hybrid"]},
        "reason": "Hébergement cloud / hybride",
    },
    {
        "code": "COBIT_IT",
        "framework_code": "cobit",
        "condition": {"sector": ["it", "finance", "banque", "assurance"]},
        "reason": "Secteur fortement dépendant du SI",
    },
    {
        "code": "SOX_LISTED",
        "framework_code": "sox",
        "condition": {"listed_company": True},
        "reason": "Société cotée (contrôles financiers)",
    },
    {
        "code": "COSO_ETI",
        "framework_code": "coso_erm",
        "condition": {"size": ["ETI", "GE"]},
        "reason": "Taille justifiant un ERM formalisé",
    },
]

DEFAULT_KB_CONTROLS: List[Dict[str, str]] = [
    {
        "code": "KB-RGPD-01",
        "title": "Registre des traitements",
        "description": "Tenir un registre des activités de traitement.",
        "framework_code": "rgpd",
        "control_type": "administrative",
    },
    {
        "code": "KB-RGPD-02",
        "title": "Base légale documentée",
        "description": "Identifier et documenter la base légale de chaque traitement.",
        "framework_code": "rgpd",
        "control_type": "administrative",
    },
    {
        "code": "KB-27005-01",
        "title": "Inventaire des actifs informationnels",
        "description": "Identifier les actifs et leur criticité.",
        "framework_code": "iso27005",
        "control_type": "preventive",
    },
    {
        "code": "KB-31000-01",
        "title": "Politique de gestion des risques",
        "description": "Définir le cadre, les rôles et l'appétence au risque.",
        "framework_code": "iso31000",
        "control_type": "administrative",
    },
]


def _profile_value(profile: Dict[str, Any], key: str) -> Any:
    value = profile.get(key)
    if isinstance(value, str):
        return value.strip()
    return value


def match_condition(profile: Dict[str, Any], condition: Optional[Dict[str, Any]]) -> bool:
    if not condition:
        return True
    for key, expected in condition.items():
        actual = _profile_value(profile, key)
        if isinstance(expected, bool):
            if bool(actual) is not expected:
                return False
        elif isinstance(expected, list):
            if actual is None:
                return False
            if str(actual).lower() not in {str(item).lower() for item in expected}:
                return False
        else:
            if actual is None or str(actual).lower() != str(expected).lower():
                return False
    return True


def evaluate_profile(
    profile: Optional[Dict[str, Any]],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Agrège les règles (OU) par framework. Une règle matchée rend le framework applicable."""
    profile = profile or {}
    active_rules = rules if rules is not None else DEFAULT_RULES
    by_framework: Dict[str, Dict[str, Any]] = {}

    for rule in active_rules:
        framework = rule["framework_code"]
        matched = match_condition(profile, rule.get("condition") or {})
        current = by_framework.get(framework)
        if matched:
            by_framework[framework] = {
                "framework_code": framework,
                "applicable": True,
                "reason": rule.get("reason"),
                "confidence": 0.85,
                "source_rule": rule.get("code"),
            }
        elif current is None:
            by_framework[framework] = {
                "framework_code": framework,
                "applicable": False,
                "reason": "Aucune règle d'applicabilité satisfaite",
                "confidence": 0.5,
                "source_rule": None,
            }

    return sorted(by_framework.values(), key=lambda item: item["framework_code"])


def evaluate_profile_detailed(
    profile: Optional[Dict[str, Any]],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Même moteur, avec toutes les raisons matchées (auditables). Ne remplace pas evaluate_profile."""
    profile = profile or {}
    active_rules = rules if rules is not None else DEFAULT_RULES
    by_framework: Dict[str, Dict[str, Any]] = {}
    for rule in active_rules:
        framework = rule["framework_code"]
        bucket = by_framework.setdefault(framework, {
            "framework_code": framework,
            "applicable": False,
            "reasons": [],
            "source_rules": [],
        })
        if match_condition(profile, rule.get("condition") or {}):
            bucket["applicable"] = True
            bucket["reasons"].append(rule.get("reason"))
            bucket["source_rules"].append(rule.get("code"))
    for item in by_framework.values():
        if not item["applicable"]:
            item["reasons"] = ["Aucun critère d'applicabilité détecté"]
    return sorted(by_framework.values(), key=lambda item: item["framework_code"])


def profile_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {
            "sector": None,
            "size": None,
            "country": "FR",
            "criticality": "medium",
            "processes_personal_data": False,
            "hosting": "cloud",
            "listed_company": False,
            "notes": None,
        }
    return {
        "sector": row.sector,
        "size": row.size,
        "country": row.country,
        "criticality": row.criticality,
        "processes_personal_data": bool(row.processes_personal_data),
        "hosting": row.hosting,
        "listed_company": bool(row.listed_company),
        "notes": row.notes,
    }
