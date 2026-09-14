"""Point d'extension des référentiels.

Chaque extracteur a sa connaissance métier.
Tous respectent le même contrat de sortie : FactSet → questions → RULE-*.
Le moteur de scoring ne change pas.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.extraction.contract import assert_evaluation_contract, assert_factset_contract
from app.extraction.comptes import evaluate_comptes_questions, extract_facts_comptes
from app.extraction.kbis import evaluate_kbis_questions, extract_facts_kbis
from app.extraction.model import Evaluation, FactSet

Extractor = Callable[..., FactSet]
Evaluator = Callable[..., Dict[int, Evaluation]]

# Nouveau référentiel = nouvel extracteur + questions/règles.
# Pas un nouveau moteur. iso_27001 reste [BLOCKED — LICENCE].
EXTRACTORS: Dict[str, Extractor] = {
    "extrait_kbis": extract_facts_kbis,
    "comptes_sociaux": extract_facts_comptes,
    # "iso_27001": extract_facts_iso_27001,
}

EVALUATORS: Dict[str, Evaluator] = {
    "extrait_kbis": evaluate_kbis_questions,
    "comptes_sociaux": evaluate_comptes_questions,
}


def extract_facts(document_type: str, texte: str, **kwargs: Any) -> Optional[FactSet]:
    extractor = EXTRACTORS.get(document_type)
    if not extractor:
        return None
    facts = extractor(texte, **kwargs)
    assert_factset_contract(facts)
    return facts


def evaluate_facts(document_type: str, facts: FactSet, **kwargs: Any) -> Optional[Dict[int, Evaluation]]:
    evaluator = EVALUATORS.get(document_type)
    if not evaluator:
        return None
    evaluations = evaluator(facts, **kwargs)
    for evaluation in evaluations.values():
        assert_evaluation_contract(evaluation)
    return evaluations
