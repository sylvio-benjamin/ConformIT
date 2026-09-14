"""Un seul appel Mistral pour les faits que les règles n'ont pas lus.

Jamais dans la boucle de décision : le scoring reste déterministe.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from app.groq_client import appel_api_securise_async

logger = logging.getLogger(__name__)


def parse_json_object(text: str) -> Dict[str, object]:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


async def fill_unresolved_with_mistral(
    texte: str,
    missing: List[Tuple[int, str]],
    nom_demande: bool = False,
) -> Tuple[Dict[int, Tuple[str, str]], Optional[str]]:
    """Remplit uniquement les questions encore vides. Un appel, pas N."""
    if not missing and not nom_demande:
        return {}, None

    lines = "\n".join(f"{index}. {question}" for index, question in missing)
    nom_line = '- "nom_entreprise": raison sociale\n' if nom_demande else ""
    prompt = f"""Extrais UNIQUEMENT les informations demandées depuis ce document.
Réponds UNIQUEMENT par un objet JSON, sans texte autour.
Clés attendues :
{nom_line}{chr(10).join(f'- "{index}": réponse courte' for index, _ in missing)}

Règles :
- Base-toi uniquement sur le document
- Si l'information est absente, réponds "Non précisé"
- Questions oui/non : réponds "Oui" ou "Non"
- Capital : un nombre entier en euros
- Forme juridique : SAS, SARL, SA, EURL, EI, SASU, SCI, SNC, ou Inconnu

Questions :
{lines}

Document :
{texte[:6000]}
"""
    logger.info("Mistral fallback : %s question(s) non résolues par les règles", len(missing))
    reponse, erreur = await appel_api_securise_async(
        prompt,
        max_retries=2,
        temperature=0.1,
        max_tokens=400,
    )
    if erreur:
        failed = {index: ("Indisponible", f"Erreur : {erreur}") for index, _ in missing}
        return failed, None

    parsed = parse_json_object(reponse)
    filled: Dict[int, Tuple[str, str]] = {}
    for index, _question in missing:
        value = parsed.get(str(index), parsed.get(index))
        if value is None or str(value).strip() == "":
            filled[index] = ("Non précisé", "Information absente après extraction")
        else:
            filled[index] = (str(value).strip(), "Fait relu par extracteur de fallback")
    nom = parsed.get("nom_entreprise")
    nom_str = str(nom).strip() if nom else None
    return filled, nom_str


async def extract_missing_facts_mistral(texte: str, missing: List[str]) -> Dict[str, object]:
    """Fallback ciblé : un fait manquant, pas « réponds aux 11 questions »."""
    if not missing:
        return {}
    prompt = f"""Extrais UNIQUEMENT ces faits s'ils figurent dans le document.
Réponds UNIQUEMENT par un objet JSON.
Clés : {", ".join(missing)}
Si un fait est absent, omets-le.
siren = 9 chiffres. forme_juridique = SAS|SARL|SA|EURL|EI|SASU|SCI|SNC. capital_social = entier euros.

Document :
{texte[:4000]}
"""
    logger.info("Mistral fallback ciblé : %s", ", ".join(missing))
    reponse, erreur = await appel_api_securise_async(
        prompt,
        max_retries=2,
        temperature=0.1,
        max_tokens=200,
    )
    if erreur:
        logger.warning("Fallback faits impossible : %s", erreur)
        return {}
    parsed = parse_json_object(reponse)
    return {key: parsed[key] for key in missing if key in parsed}
