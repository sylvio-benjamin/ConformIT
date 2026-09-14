from app.scoring.config import niveau_from_score
from app.scoring.engine import (
    aggregate_from_rules,
    apply_deterministic_scoring,
    attach_breakdown_if_missing,
    normalize_type_score,
    renormalize_weights,
    weighted_global,
)


def test_normalize_type_score():
    assert normalize_type_score(0, 54) == 0
    assert normalize_type_score(54, 54) == 100
    assert normalize_type_score(27, 54) == 50
    assert normalize_type_score(200, 54) == 100


def test_weighted_global_spec_example():
    by_type = {
        "juridique": {"score": 78, "weight": 30},
        "financier": {"score": 42, "weight": 25},
        "conformite": {"score": 91, "weight": 20},
        "administratif": {"score": 35, "weight": 15},
        "reputation": {"score": 20, "weight": 10},
    }
    assert weighted_global(by_type) == 59.35
    label_fr, label_en = niveau_from_score(59.35)
    assert label_fr == "Élevé"
    assert label_en == "High"


def test_renormalize_conformite_and_administratif():
    result = renormalize_weights({"conformite", "administratif"})
    assert result["conformite"] == 57.14
    assert result["administratif"] == 42.86
    assert abs(sum(result.values()) - 100) < 0.02


def test_kbis_single_juridique_finding_does_not_fill_other_types():
    details = [
        {"question_index": 1, "score": 40, "reponse": "Non", "justification": "RCS absent"},
        {"question_index": 2, "score": 0, "reponse": "Oui", "justification": "SIREN"},
        {"question_index": 6, "score": 0, "reponse": "Oui", "justification": "ancienneté"},
        {"question_index": 16, "score": 0, "reponse": "Inconnu", "justification": "pas d'historique", "evaluation_status": "INCONNU"},
        {"question_index": 19, "score": 0, "reponse": "Oui", "justification": "capital"},
        {"question_index": 29, "score": 0, "reponse": "Oui", "justification": "CAC"},
    ]
    breakdown = apply_deterministic_scoring(details, "extrait_kbis")
    assert details[0]["rule_id"] == "RULE-JUR-001"
    assert breakdown["by_type"]["juridique"]["brut"] == 40
    assert breakdown["by_type"]["juridique"]["cap"] > 40
    assert breakdown["by_type"]["financier"]["score"] == 0
    assert abs(sum(breakdown["weights"].values()) - 100) < 0.02
    assert breakdown["by_type"]["juridique"]["rules"][0]["rule_id"] == "RULE-JUR-001"


def test_attestation_renormalizes_single_family():
    details = [
        {"question_index": i, "score": 10 if i in (1, 3) else 0, "reponse": "Non", "justification": "manquant"}
        for i in range(1, 11)
    ]
    breakdown = apply_deterministic_scoring(details, "attestation_assurance")
    assert list(breakdown["weights"].keys()) == ["conformite"]
    assert breakdown["weights"]["conformite"] == 100
    assert breakdown["by_type"]["conformite"]["cap"] == 100
    assert breakdown["by_type"]["conformite"]["brut"] == 20
    assert breakdown["score_global"] == 20
    assert breakdown["niveau_risque_label"] == "Faible"


def test_zero_findings_is_faible():
    details = [{"question_index": 1, "score": 0, "reponse": "Oui", "justification": "ok"}]
    breakdown = apply_deterministic_scoring(details, "comptes_sociaux")
    assert breakdown["score_global"] == 0
    assert breakdown["niveau_risque"] == "Low"
    assert breakdown["niveau_risque_label"] == "Faible"


def test_trace_fields_on_details():
    details = [{"question_index": 1, "score": 40, "reponse": "Non", "justification": "RCS 123456789"}]
    pages = [{"number": 3, "text": "justification RCS 123456789 extraite du document"}]
    breakdown = apply_deterministic_scoring(details, "extrait_kbis", pages=pages)
    assert details[0]["risk_type"] == "juridique"
    assert details[0]["triggered"] is True
    assert details[0]["rule_version"] == "1.0"
    assert details[0]["rule_condition"]
    assert details[0]["evidence"]["page"] == 3
    assert details[0]["evidence"]["snippet"]
    assert details[0]["evidence"]["method"] == "regle_deterministe"
    assert breakdown["llm_in_decision_loop"] is False
    assert breakdown["formula"]["S_global"] == "sum(S_r * W_r) / 100"
    rule = breakdown["by_type"]["juridique"]["rules"][0]
    assert rule["page"] == 3
    assert rule["snippet"]
    assert rule["condition"]


def test_adding_iso27001_does_not_change_aggregate_from_rules():
    import inspect
    source = inspect.getsource(aggregate_from_rules)
    assert "iso27001" not in source.lower()
    assert "kbis" not in source.lower()
    assert "rgpd" not in source.lower()
    assert "31000" not in source
    future_iso = [
        {
            "risk_type": "conformite",
            "impact": 15,
            "max_impact": 30,
            "triggered": True,
            "rule_id": "RULE-27001-001",
            "rule_referentiel": "iso27001",
        }
    ]
    breakdown = aggregate_from_rules(future_iso)
    assert breakdown["referential_agnostic"] is True
    assert breakdown["by_type"]["conformite"]["score"] == 50.0


def test_engine_is_referential_agnostic():
    findings = [
        {"risk_type": "conformite", "impact": 20, "max_impact": 40, "triggered": True, "rule_id": "RULE-COM-001"},
        {"risk_type": "juridique", "impact": 10, "max_impact": 20, "triggered": True, "rule_id": "RULE-JUR-001"},
    ]
    kbis_like = aggregate_from_rules([{**item, "rule_referentiel": "extrait_kbis"} for item in findings])
    iso_like = aggregate_from_rules([{**item, "rule_id": item["rule_id"].replace("COM", "27001"), "rule_referentiel": "iso27001"} for item in findings])
    assert kbis_like["score_global"] == iso_like["score_global"]
    assert kbis_like["by_type"]["conformite"]["score"] == iso_like["by_type"]["conformite"]["score"]
    assert kbis_like["referential_agnostic"] is True


def test_extraction_error_does_not_score():
    details = [
        {
            "question_index": 1,
            "question": "L'entreprise est-elle immatriculée au Registre du commerce et des sociétés (RCS) ?",
            "score": 40,
            "reponse": "Non",
            "justification": 'Erreur : Erreur API Mistral: HTTP 429: {"message":"Rate limit exceeded"}',
        },
        {
            "question_index": 19,
            "question": "Le capital social est-il supérieur à un seuil défini ?",
            "score": 6,
            "reponse": "Non",
            "justification": "Erreur : Erreur API Mistral: HTTP 429: Rate limit exceeded",
        },
    ]
    breakdown = apply_deterministic_scoring(details, "type_inconnu")
    assert details[0]["extraction_failed"] is True
    assert details[0]["triggered"] is False
    assert details[0]["rule_id"] == "RULE-JUR-001"
    assert details[1]["rule_id"] == "RULE-FIN-001"
    assert breakdown["score_global"] == 0
    assert breakdown["extraction_incomplete"] is True
    assert breakdown["extraction_failed_count"] == 2
    assert breakdown["by_type"] == {}


def test_kbis_questions_use_kbis_catalog_when_type_unknown():
    details = [
        {
            "question_index": 1,
            "question": "L'entreprise est-elle immatriculée au Registre du commerce et des sociétés (RCS) ?",
            "score": 40,
            "reponse": "Non",
            "justification": "Pas de numéro RCS",
        }
    ]
    breakdown = apply_deterministic_scoring(details, "type_inconnu")
    assert details[0]["rule_id"] == "RULE-JUR-001"
    assert details[0]["risk_type"] == "juridique"
    assert details[0]["max_impact"] == 40
    assert breakdown["by_type"]["juridique"]["brut"] == 40


def test_attach_recomputes_stale_rate_limit_score():
    payload = {
        "document_type_key": "type_inconnu",
        "score_global": 92.73,
        "score_breakdown": {
            "score_global": 92.73,
            "niveau_risque_label": "Critique",
            "by_type": {
                "administratif": {
                    "rules": [
                        {
                            "triggered": True,
                            "finding": "Erreur : Erreur API Mistral: HTTP 429: Rate limit exceeded",
                        }
                    ]
                }
            },
        },
        "details": [
            {
                "question_index": 1,
                "question": "L'entreprise est-elle immatriculée au Registre du commerce et des sociétés (RCS) ?",
                "score": 40,
                "reponse": "Non",
                "justification": "Erreur : Erreur API Mistral: HTTP 429: Rate limit exceeded",
            }
        ],
    }
    enriched = attach_breakdown_if_missing(payload)
    assert enriched["score_global"] == 0
    assert enriched["niveau_risque_label"] == "Faible"
    assert enriched["score_breakdown"]["extraction_incomplete"] is True


def test_attach_breakdown_if_missing():
    payload = {
        "document_type_key": "extrait_kbis",
        "details": [
            {"question_index": 1, "score": 40, "reponse": "Non", "justification": "RCS absent"},
        ],
    }
    enriched = attach_breakdown_if_missing(payload)
    assert enriched["score_breakdown"]["engine"] == "deterministic_v1"
    assert "score_global" in enriched
    assert attach_breakdown_if_missing(enriched)["score_breakdown"] is enriched["score_breakdown"]
