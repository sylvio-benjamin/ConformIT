"""Compatibilité : l'API historique délègue au extracteur Kbis typé."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.extraction.kbis import evaluate_kbis_questions, extract_facts_kbis
from app.extraction.kbis.extract import expected_unknown_facts
from app.extraction.model import EVAL_INCONNU, FactSet


def extract_company_name(texte: str) -> Optional[str]:
    denomination = extract_facts_kbis(texte)["denomination"]
    return str(denomination.value) if denomination.present else None


def extract_kbis_facts(texte: str, as_of: Optional[date] = None, pages=None) -> FactSet:
    return extract_facts_kbis(texte, pages=pages, as_of=as_of)


def answers_from_facts(facts: FactSet, as_of: Optional[date] = None) -> Dict[int, Tuple[str, str]]:
    """Ne retourne que les questions tranchées. INCONNU n'est pas une réponse inventée."""
    answers: Dict[int, Tuple[str, str]] = {}
    for index, evaluation in evaluate_kbis_questions(facts, as_of=as_of).items():
        if evaluation.status == EVAL_INCONNU:
            continue
        answers[index] = (evaluation.answer, evaluation.rationale)
    return answers


def unresolved_questions(
    questions: Dict[int, str],
    answers: Dict[int, Tuple[str, str]],
) -> List[Tuple[int, str]]:
    return [(index, text) for index, text in sorted(questions.items()) if index not in answers]


def evaluations_to_meta(facts: FactSet) -> Dict[str, Any]:
    return facts.to_dict()
