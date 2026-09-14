"""Normalisation et détection de négation autour d'un motif."""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple

NEGATION_RE = re.compile(
    r"\b(n['’]est pas|n['’]est plus|ne sont pas|ne possede pas|ne possede plus|"
    r"pas de|sans|aucun|aucune|neant|non designe|non nomme|non immatricul)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})")


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.lower()


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def snippet(text: str, start: int, end: int, radius: int = 70) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    excerpt = clean_spaces(text[left:right])
    if left > 0:
        excerpt = "…" + excerpt
    if right < len(text):
        excerpt = excerpt + "…"
    return excerpt


def is_negated(folded: str, match_start: int, window: int = 48) -> bool:
    prefix = folded[max(0, match_start - window) : match_start]
    return bool(NEGATION_RE.search(prefix))


def first_match(folded: str, patterns: List[str]) -> Optional[re.Match]:
    for pattern in patterns:
        match = re.search(pattern, folded, re.IGNORECASE)
        if match:
            return match
    return None


def parse_date(raw: str):
    match = DATE_RE.search(raw or "")
    if not match:
        return None
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if year < 100:
        year += 2000 if year < 50 else 1900
    from datetime import date
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_amount(raw: str) -> Optional[int]:
    value = (raw or "").replace("\u00a0", "").replace(" ", "")
    if not value:
        return None
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    try:
        return int(float(value))
    except ValueError:
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else None


def locate_page(pages: Optional[List[dict]], needle: str) -> Optional[int]:
    if not pages or not needle or len(needle) < 6:
        return None
    sample = needle[:48].lower()
    for page in pages:
        body = str(page.get("text") or "")
        if sample in body.lower():
            return page.get("number")
    return None
