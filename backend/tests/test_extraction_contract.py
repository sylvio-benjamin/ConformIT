import inspect

import pytest

from app.evaluation_layers import (
    BOUNDARIES,
    DEMONSTRATORS,
    EXTEND_RULE,
    EXTENSION_MAP,
    EXTENSION_TABLE,
    GUARANTEES,
    OBSERVATION_RULE,
    PARALLEL_AMBIGUITY_TESTS,
    PHILOSOPHICAL_TEST,
    PROOF_RULE,
    REVIEW_SIGNAL,
    ARCHITECTURE_STATUS,
    ENGINE_CENTER,
    ENGINE_CONSUMES,
    ENGINE_ROLE,
    EVOLUTION_POLICY,
    EXCEPTION_PATH,
    GUARDRAIL,
    KNOWLEDGE_OPTIONAL,
    KNOWLEDGE_PATH,
    REFERENCE_CONSTRAINT,
    REVIEW_CRITERION,
    SEPARATION_RULE,
    classify_change,
    evaluation_contract,
    refuse_scope_as_normative,
    route_need,
)
from app.extraction.comptes import extract as comptes_extract
from app.extraction.comptes import questions as comptes_questions
from app.extraction.kbis.extract import expected_unknown_facts
from app.extraction.kbis.patterns import AMBIGUOUS_FACTS, EXPECTED_FACTS
from app.extraction.contract import (
    INVARIANTS,
    PIPELINE,
    assert_evaluation_contract,
    assert_factset_contract,
    unknown_is_not_an_error,
)
from app.extraction.kbis import evaluate_kbis_questions, extract_facts_kbis
from app.extraction.kbis import extract as kbis_extract
from app.extraction.kbis import questions as kbis_questions
from app.extraction.model import EVAL_INCONNU, Evidence, Fact, FactSet
from app.extraction.registry import EXTRACTORS, extract_facts
from app.scoring import catalog as scoring_catalog
from app.scoring.engine import aggregate_from_rules, apply_deterministic_scoring


SAMPLE = """
Dénomination : ACME TECHNOLOGIES
Forme juridique : Société par actions simplifiée (SAS)
Capital social : 10 000 Euros
Immatriculation au RCS : 123 456 789
"""


def test_separation_and_boundaries_are_product_contract():
    contract = evaluation_contract()
    assert contract["separation_rule"] == SEPARATION_RULE
    assert contract["llm_is_semantic_authority"] is False
    assert contract["unknown_is_error"] is False
    assert contract["boundaries"]["mistral"] == "fallback d'extraction uniquement"
    assert contract["boundaries"]["scoring"] == "agrège les impacts"
    assert contract["boundaries"]["catalog"] == "décrit les référentiels, sans évaluer"
    assert contract["boundaries"] == BOUNDARIES


def test_extractor_registry_returns_typed_facts():
    facts = extract_facts("extrait_kbis", SAMPLE)
    assert_factset_contract(facts)
    assert facts["siren"].present is True
    assert facts["siren"].evidence.source == "pdf_text"
    assert facts["siren"].evidence.snippet


def test_factset_rejects_freeform_llm_phrase():
    with pytest.raises((ValueError, TypeError)):
        FactSet(
            [
                Fact(
                    name="siren",
                    type="texte",
                    status="present",
                    value="D'après le document, l'entreprise semble immatriculée au RCS de Paris.",
                    evidence=Evidence(source="mistral_fallback", snippet="phrase"),
                )
            ]
        )


def test_factset_rejects_plain_string():
    with pytest.raises(TypeError):
        FactSet(["l'entreprise est légalement enregistrée"])


def test_extend_by_knowledge_not_intelligence():
    contract = evaluation_contract()
    assert contract["extend_rule"] == EXTEND_RULE
    assert contract["extension_map"]["scoring"] == "aucune modification"
    assert contract["extension_map"]["document"] == "nouvel EXTRACTOR"
    assert contract["extension_map"] == EXTENSION_MAP
    assert "intelligence" not in contract["extension_map"].values()
    assert contract["attendu_neq_necessaire"] is True
    assert contract["p0_p10_closed"] is True
    assert contract["fact_states"]["undeterminable"] == "INCONNU"
    assert contract["proof_rule"] == PROOF_RULE
    assert contract["extension_table"]["Nouveau calcul de score"] == "exception architecturale"
    assert contract["extension_table"] == EXTENSION_TABLE
    assert contract["aggregate_from_rules_stable"] is True
    assert PARALLEL_AMBIGUITY_TESTS["extrait_kbis"] == ("Q16",)
    assert PARALLEL_AMBIGUITY_TESTS["comptes_sociaux"] == ("Q6", "Q13")
    assert contract["observation_rule"] == OBSERVATION_RULE
    assert contract["guarantees"] == GUARANTEES
    assert contract["demonstrators"] == list(DEMONSTRATORS)
    assert "signal architectural" in REVIEW_SIGNAL
    assert contract["review_criterion"] == REVIEW_CRITERION
    assert contract["is_architecture_constraint"] is True
    assert contract["architecture_status"] == ARCHITECTURE_STATUS == "FROZEN"
    assert contract["architecture_frozen"] is True
    assert contract["guardrail"] == GUARDRAIL == "Connaissance ou moteur ?"
    assert contract["reference_constraint"] == list(REFERENCE_CONSTRAINT)
    assert contract["evolution_policy"] == EVOLUTION_POLICY
    assert contract["knowledge_path"] == list(KNOWLEDGE_PATH)
    assert contract["knowledge_optional"] == list(KNOWLEDGE_OPTIONAL)
    assert contract["exception_path"] == list(EXCEPTION_PATH)
    assert contract["engine_center"] == ENGINE_CENTER
    assert contract["engine_role"] == ENGINE_ROLE
    assert contract["engine_consumes"] == list(ENGINE_CONSUMES)
    assert contract["rule_provenance_irrelevant"] is True
    assert contract["inconnu_is_valid_output"] is True
    assert contract["inconnu_is_not_a_constat"] is True
    assert contract["constat_requires_evidence"] is True
    assert contract["selector_reduces_structural_unknown"] is True
    assert contract["selector_preserves_documentary_unknown"] is True
    assert contract["extension_table"]["Nouveau type de document sélectionnable"] == "type_hint"


def test_review_classifies_knowledge_vs_engine():
    assert classify_change("EXTRACTOR") == "normale"
    assert classify_change("FactSet") == "normale"
    assert classify_change("condition") == "normale"
    assert classify_change("RULE-*") == "normale"
    assert classify_change("applicabilité") == "normale"
    assert classify_change("type_hint") == "normale"
    assert classify_change("aggregate_from_rules") == "exception"
    assert classify_change("exception architecturale") == "exception"
    with pytest.raises(ValueError):
        classify_change("nouveau moteur")


def test_route_need_is_frozen_guardrail():
    knowledge = route_need(structured_knowledge=True)
    assert knowledge["path"] == "connaissance"
    assert knowledge["engine_change"] is False
    assert knowledge["extensions"] == list(KNOWLEDGE_PATH)
    assert knowledge["optional"] == ["applicabilité"]
    exception = route_need(structured_knowledge=False)
    assert exception["path"] == "exception"
    assert exception["engine_change"] is True
    assert exception["requires"] == ["justification", "tests"]


def test_comptes_is_additive_second_demonstrator():
    assert DEMONSTRATORS == ("extrait_kbis", "comptes_sociaux")
    engine = inspect.getsource(aggregate_from_rules)
    assert "comptes" not in engine.lower()
    assert "extrait_kbis" not in engine.lower()
    for module in (comptes_extract, comptes_questions):
        source = inspect.getsource(module)
        assert "aggregate_from_rules" not in source
        assert "mistral" not in source.lower()


def test_same_impacts_same_score_across_demonstrators():
    findings = [
        {"risk_type": "financier", "impact": 10, "max_impact": 20, "triggered": True, "rule_id": "RULE-FIN-001"},
        {"risk_type": "juridique", "impact": 4, "max_impact": 40, "triggered": True, "rule_id": "RULE-JUR-002"},
    ]
    kbis = aggregate_from_rules([{**item, "rule_referentiel": "extrait_kbis"} for item in findings])
    comptes = aggregate_from_rules([{**item, "rule_referentiel": "comptes_sociaux"} for item in findings])
    iso = aggregate_from_rules([{**item, "rule_id": "RULE-27001-001", "rule_referentiel": "iso27001"} for item in findings])
    assert kbis["score_global"] == comptes["score_global"] == iso["score_global"]


def test_q16_is_the_philosophical_test_absent_proof_stays_unknown():
    assert PHILOSOPHICAL_TEST["id"] == "Q16"
    assert PHILOSOPHICAL_TEST["invent"] is False
    assert PHILOSOPHICAL_TEST["llm_guess"] is False
    assert PHILOSOPHICAL_TEST["penalty_without_proof"] is False
    facts = extract_facts_kbis(SAMPLE)
    assert "transfert_siege" in AMBIGUOUS_FACTS
    assert "transfert_siege" not in EXPECTED_FACTS
    assert "transfert_siege" not in expected_unknown_facts(facts)
    unknown = evaluate_kbis_questions(facts)[16]
    assert unknown.status == EVAL_INCONNU
    assert unknown.answer not in {"Oui", "Non"}


def test_unknown_is_business_information_not_error():
    evaluations = evaluate_kbis_questions(extract_facts_kbis(SAMPLE))
    assert evaluations[16].status == EVAL_INCONNU
    assert unknown_is_not_an_error(evaluations[16]) is True
    assert_evaluation_contract(evaluations[16])


def test_inconnu_is_not_converted_to_oui_or_non():
    evaluations = evaluate_kbis_questions(extract_facts_kbis(SAMPLE))
    unknown = evaluations[16]
    assert unknown.answer not in {"Oui", "Non", "OUI", "NON"}
    details = [
        {
            "question_index": 16,
            "question": "Une modification récente de l'adresse du siège est-elle identifiable dans les informations disponibles ?",
            "reponse": unknown.answer,
            "justification": unknown.rationale,
            "evaluation_status": "INCONNU",
            "score": 10,
        }
    ]
    breakdown = apply_deterministic_scoring(details, "extrait_kbis")
    assert details[0]["triggered"] is False
    assert details[0]["impact"] == 0
    assert details[0]["extraction_failed"] is False
    assert breakdown["by_type"]["administratif"]["brut"] == 0


def test_questions_must_not_import_mistral():
    source = inspect.getsource(kbis_questions)
    assert "mistral" not in source.lower()
    assert "appel_" not in source
    assert "openai" not in source.lower()


def test_rules_must_not_import_mistral():
    source = inspect.getsource(scoring_catalog)
    assert "mistral" not in source.lower()
    assert "import ocr" not in source
    assert "extraction.ocr" not in source


def test_extractor_does_not_import_scoring():
    source = inspect.getsource(kbis_extract)
    assert "aggregate_from_rules" not in source
    assert "scoring" not in source


def test_scoring_must_not_know_a_referential():
    source = inspect.getsource(aggregate_from_rules)
    assert "extract_facts" not in source
    assert "mistral" not in source.lower()
    assert "kbis" not in source.lower()
    assert "iso27001" not in source.lower()
    assert "rgpd" not in source.lower()
    assert "scope.en" not in source


def test_scope_en_never_becomes_a_requirement():
    with pytest.raises(ValueError, match="pas un contenu normatif"):
        refuse_scope_as_normative("This document specifies requirements for ISMS.")


def test_pipeline_ends_in_aggregate():
    assert PIPELINE[0] == "pdf"
    assert PIPELINE[-1] == "aggregate_from_rules"
    assert "Un mot trouvé n'est jamais directement une réponse" in INVARIANTS
    assert "INCONNU n'est pas une erreur : le document ne permet pas de conclure" in INVARIANTS


def test_future_referential_is_only_a_registry_entry():
    assert "extrait_kbis" in EXTRACTORS
    assert "comptes_sociaux" in EXTRACTORS
    assert "iso_27001" not in EXTRACTORS
