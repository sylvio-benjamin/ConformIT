import inspect

import pytest

from app.extraction.coherence import (
    DocumentTypeMismatch,
    USES_MISTRAL,
    assert_no_mistral,
    check_coherence,
)
from app.extraction.document_types import (
    SELECTABLE_IDS,
    SELECTOR_PRESERVES_DOCUMENTARY_UNKNOWN,
    SELECTOR_REDUCES_STRUCTURAL_UNKNOWN,
    TYPE_CONTEXT_RULE,
    is_selectable,
    public_catalog,
)
from app.extraction.kbis import evaluate_kbis_questions, extract_facts_kbis
from app.extraction.kbis.patterns import AMBIGUOUS_FACTS
from app.extraction.model import EVAL_INCONNU
from app.scoring.engine import aggregate_from_rules


KBIS = """
Extrait Kbis
Registre du Commerce et des Sociétés
Dénomination : ACME TECHNOLOGIES
Forme juridique : Société par actions simplifiée (SAS)
Capital social : 10 000 Euros
Immatriculation au RCS : 123 456 789
Greffe de Nanterre
"""

COMPTES = """
Comptes annuels
Chiffre d'affaires : 1 250 000
Capitaux propres : 400 000
"""

ASSURANCE = """
Attestation d'assurance
Compagnie d'assurance : AXA
Numéro de police : POL-991
"""

NOVEL = """
Il était une fois une entreprise imaginaire dans un roman
sans aucun indice administratif ni comptable.
""" * 5


def test_catalog_matches_product_selector():
    ids = [item["id"] for item in public_catalog()]
    assert ids == [
        "extrait_kbis",
        "comptes_sociaux",
        "bilan_comptable",
        "compte_resultat",
        "liasse_fiscale",
        "releve_bancaire",
        "statuts",
        "attestation_assurance",
    ]
    assert is_selectable("extrait_kbis") is True
    assert is_selectable("iso_27001") is False
    assert is_selectable("type_inconnu") is False


def test_kbis_hint_is_coherent_without_guessing():
    verdict = check_coherence("extrait_kbis", KBIS)
    assert verdict["coherent"] is True
    assert verdict["uses_mistral"] is False
    assert verdict["preserves_documentary_unknown"] is True


def test_wrong_type_is_blocked():
    verdict = check_coherence("extrait_kbis", ASSURANCE)
    assert verdict["coherent"] is False
    assert "Kbis" in verdict["message"]
    with pytest.raises(DocumentTypeMismatch):
        if not verdict["coherent"]:
            raise DocumentTypeMismatch("extrait_kbis", verdict["message"])


def test_no_structural_marker_is_blocked():
    verdict = check_coherence("extrait_kbis", NOVEL)
    assert verdict["coherent"] is False
    assert "Kbis" in verdict["message"]


def test_comptes_hint_uses_comptes_knowledge():
    assert check_coherence("comptes_sociaux", COMPTES)["coherent"] is True
    assert check_coherence("comptes_sociaux", KBIS)["coherent"] is False


def test_selector_does_not_erase_documentary_unknown():
    facts = extract_facts_kbis(KBIS)
    assert "transfert_siege" in AMBIGUOUS_FACTS
    assert facts.get("transfert_siege") is None or not facts["transfert_siege"].present
    unknown = evaluate_kbis_questions(facts)[5]
    assert unknown.status == EVAL_INCONNU
    assert SELECTOR_PRESERVES_DOCUMENTARY_UNKNOWN is True
    assert SELECTOR_REDUCES_STRUCTURAL_UNKNOWN is True


def test_coherence_does_not_use_mistral():
    assert USES_MISTRAL is False
    assert_no_mistral()
    source = inspect.getsource(inspect.getmodule(check_coherence))
    assert "mistral_client" not in source
    assert "appel_mistral" not in source
    assert "contexte explicite" in TYPE_CONTEXT_RULE


def test_engine_still_ignores_document_type():
    findings = [
        {"risk_type": "juridique", "impact": 4, "max_impact": 40, "triggered": True, "rule_id": "RULE-JUR-002"},
    ]
    kbis = aggregate_from_rules([{**item, "rule_referentiel": "extrait_kbis"} for item in findings])
    comptes = aggregate_from_rules([{**item, "rule_referentiel": "comptes_sociaux"} for item in findings])
    assert kbis["score_global"] == comptes["score_global"]
    engine = inspect.getsource(aggregate_from_rules)
    assert "document_type" not in engine
    assert "type_hint" not in engine
    assert SELECTABLE_IDS
