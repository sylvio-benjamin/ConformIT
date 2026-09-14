"""Pondérations et seuils configurables du scoring déterministe."""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

# Types de risque et poids métier (somme = 100).
DEFAULT_WEIGHTS: Dict[str, int] = {
    "juridique": 30,
    "financier": 25,
    "conformite": 20,
    "administratif": 15,
    "reputation": 10,
}

RISK_TYPE_LABELS: Dict[str, str] = {
    "juridique": "Juridique",
    "financier": "Financier",
    "conformite": "Conformité",
    "administratif": "Administratif",
    "reputation": "Réputation",
}

# Seuils exclusifs à droite : [0, 25) Faible, [25, 50) Modéré, [50, 75) Élevé, [75, 101) Critique
DEFAULT_THRESHOLDS: List[Tuple[int, str, str]] = [
    (25, "Faible", "Low"),
    (50, "Modéré", "Medium"),
    (75, "Élevé", "High"),
    (101, "Critique", "Critical"),
]


def weights() -> Dict[str, int]:
    raw = os.getenv("RISK_WEIGHTS")
    if not raw:
        return dict(DEFAULT_WEIGHTS)
    parsed: Dict[str, int] = {}
    for part in raw.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        parsed[key.strip()] = int(value.strip())
    if sum(parsed.values()) != 100:
        return dict(DEFAULT_WEIGHTS)
    return parsed


def thresholds() -> List[Tuple[int, str, str]]:
    raw = os.getenv("RISK_LEVEL_THRESHOLDS")
    if not raw:
        return list(DEFAULT_THRESHOLDS)
    # Format: 25:Faible:Low,50:Modéré:Medium,75:Élevé:High,101:Critique:Critical
    parsed: List[Tuple[int, str, str]] = []
    for part in raw.split(","):
        bits = part.split(":")
        if len(bits) != 3:
            return list(DEFAULT_THRESHOLDS)
        parsed.append((int(bits[0]), bits[1], bits[2]))
    return parsed or list(DEFAULT_THRESHOLDS)


def niveau_from_score(score: float) -> Tuple[str, str]:
    value = float(score)
    for limit, label_fr, label_en in thresholds():
        if value < limit:
            return label_fr, label_en
    return "Critique", "Critical"


def couleur_from_score(score: float) -> str:
    value = float(score)
    if value < 25:
        return "green"
    if value < 50:
        return "orange"
    if value < 75:
        return "orange-dark"
    return "red"
