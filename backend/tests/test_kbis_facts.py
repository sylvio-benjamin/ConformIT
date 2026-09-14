from datetime import date

from app.extraction.kbis import evaluate_kbis_questions, expected_unknown_facts, extract_facts_kbis
from app.extraction.kbis.catalog import CONDITIONAL_IDS, QUESTIONS, SOLID_IDS, questions_json
from app.extraction.kbis.patterns import AMBIGUOUS_FACTS
from app.extraction.kbis.questions import impacts_from_evaluations
from app.extraction.kbis_facts import answers_from_facts, extract_kbis_facts, unresolved_questions
from app.extraction.mistral_fallback import parse_json_object
from app.extraction.model import EVAL_INCONNU, EVAL_NON, EVAL_OUI
from app.scoring.catalog import lookup_rule
from app.scoring.engine import aggregate_from_rules, apply_deterministic_scoring


KBIS_TEXTE = """
GREFFE DU TRIBUNAL DE COMMERCE DE PARIS
Extrait Kbis
Dénomination : ACME TECHNOLOGIES
Forme juridique : Société par actions simplifiée (SAS)
Capital social : 10 000,00 Euros
Adresse du siège : 10 rue de la Paix 75002 Paris
Immatriculation au RCS : 123 456 789 R.C.S. Paris
Date d'immatriculation : 15/03/2018
Date de début d'activité : 01/04/2018
Durée de la personne morale : 99 ans
Commissaire aux comptes titulaire : CABINET DUPONT
Nombre d'établissements : 1
Établissement principal : 10 rue de la Paix 75002 Paris
Dirigeant : Jean MARTIN, nationalité française, demeurant 12 avenue Victor Hugo 75116 Paris
Président
"""


def test_catalog_has_thirty_questions_with_contract():
    assert len(QUESTIONS) == 30
    assert questions_json()["16"].startswith("Une modification récente")
    assert questions_json()["30"].startswith("Une mention de radiation")
    for spec in QUESTIONS:
        assert spec["required_facts"]
        assert spec["type"] in {"presence", "calculated", "value"}
        assert spec["calculation"]
    assert "Q16" in CONDITIONAL_IDS
    assert "Q01" in SOLID_IDS


def test_extract_kbis_facts_are_typed():
    facts = extract_facts_kbis(KBIS_TEXTE)
    assert facts["siren"].present is True
    assert facts["siren"].value == "123456789"
    assert facts["mention_rcs"].present is True
    assert facts["denomination"].value == "ACME TECHNOLOGIES"
    assert facts["forme_juridique"].value == "SAS"
    assert facts["capital_social"].value == 10000
    assert facts["date_immatriculation"].value == "2018-03-15"
    assert facts["date_debut_activite"].value == "2018-04-01"
    assert facts["duree_societe"].value == 99
    assert facts["duree_nature"].value == "déterminée"
    assert facts["commissaire_comptes"].value is True
    assert facts["nombre_etablissements"].value == 1
    assert facts["etablissement_principal"].present is True
    assert facts["nationalite"].value == "Française"
    assert facts["dirigeants_count"].present is True
    assert facts["dirigeant_fonction"].present is True
    assert expected_unknown_facts(facts) == []


def test_word_found_is_not_an_answer():
    texte = "Ce document mentionne une SAS dans un article de presse, sans forme juridique."
    facts = extract_facts_kbis(texte)
    assert facts["forme_juridique"].present is False
    assert evaluate_kbis_questions(facts)[4].status == EVAL_INCONNU


def test_negation_does_not_register_siren():
    texte = "La société n'est pas immatriculée au RCS et ne possède pas de SIREN."
    facts = extract_facts_kbis(texte)
    assert facts["siren"].status == "absent"
    assert evaluate_kbis_questions(facts)[2].status == EVAL_NON


def test_questions_use_facts_not_text():
    facts = extract_facts_kbis(KBIS_TEXTE)
    evaluations = evaluate_kbis_questions(facts, as_of=date(2026, 9, 13))
    assert evaluations[1].status == EVAL_OUI
    assert evaluations[2].status == EVAL_OUI
    assert evaluations[3].status == EVAL_OUI
    assert evaluations[4].status == EVAL_OUI
    assert evaluations[6].status == EVAL_OUI
    assert evaluations[13].status == EVAL_NON
    assert evaluations[16].status == EVAL_INCONNU
    assert evaluations[28].status == EVAL_NON
    assert evaluations[30].status == EVAL_INCONNU


def test_absent_history_is_unknown_not_non():
    facts = extract_facts_kbis(KBIS_TEXTE)
    assert "transfert_siege" in AMBIGUOUS_FACTS
    assert facts["transfert_siege"].status == "unknown"
    assert evaluate_kbis_questions(facts)[16].status == EVAL_INCONNU
    assert impacts_from_evaluations(evaluate_kbis_questions(facts))[16] == 0


def test_answers_skip_unknown_instead_of_inventing():
    facts = extract_kbis_facts(KBIS_TEXTE, as_of=date(2026, 9, 13))
    answers = answers_from_facts(facts, as_of=date(2026, 9, 13))
    questions = {i: f"Q{i}" for i in range(1, 31)}
    missing = unresolved_questions(questions, answers)
    assert (16, "Q16") in missing
    assert answers[2][0] == "Oui"
    assert answers[6][0] == "Oui"


def test_unknown_does_not_trigger_scoring():
    details = [
        {
            "question_index": 16,
            "question": "Une modification récente de l'adresse du siège est-elle identifiable dans les informations disponibles ?",
            "reponse": "Inconnu",
            "justification": "Fait insuffisant dans le document",
            "evaluation_status": "INCONNU",
            "score": 10,
        }
    ]
    breakdown = apply_deterministic_scoring(details, "extrait_kbis")
    assert details[0]["triggered"] is False
    assert details[0]["impact"] == 0
    assert breakdown["by_type"]["administratif"]["brut"] == 0


def test_scoring_rules_follow_catalog_indices():
    rule = lookup_rule("extrait_kbis", 1)
    assert rule["id"] == "RULE-JUR-001"
    assert lookup_rule("extrait_kbis", 16)["id"] == "RULE-ADM-001"
    assert lookup_rule("extrait_kbis", 30)["id"] == "RULE-JUR-006"


def test_facts_then_scoring_does_not_treat_regex_as_api_error():
    facts = extract_kbis_facts(KBIS_TEXTE, as_of=date(2026, 9, 13))
    evaluations = evaluate_kbis_questions(facts, as_of=date(2026, 9, 13))
    scores = impacts_from_evaluations(evaluations)
    details = [
        {
            "question_index": index,
            "question": f"Q{index}",
            "reponse": evaluation.answer,
            "justification": evaluation.rationale,
            "evaluation_status": evaluation.status,
            "score": scores.get(index, 0),
        }
        for index, evaluation in evaluations.items()
    ]
    breakdown = apply_deterministic_scoring(details, "extrait_kbis")
    assert breakdown["extraction_incomplete"] is False
    assert breakdown["llm_in_decision_loop"] is False
    assert "juridique" in breakdown["by_type"] or breakdown["score_global"] == 0


def test_missing_cac_stays_unknown():
    texte = """
    Extrait Kbis
    Dénomination : ACME
    Forme juridique : SAS
    Capital social : 50000 Euros
    Immatriculation au RCS : 111 222 333
    Date d'immatriculation : 01/01/2020
    """
    evaluations = evaluate_kbis_questions(extract_facts_kbis(texte), as_of=date(2026, 9, 13))
    assert evaluations[29].status == EVAL_INCONNU
    assert impacts_from_evaluations(evaluations)[29] == 0


def test_parse_json_object_strips_fences():
    parsed = parse_json_object('```json\n{"2": "Oui", "nom_entreprise": "ACME"}\n```')
    assert parsed["2"] == "Oui"
    assert parsed["nom_entreprise"] == "ACME"


def test_aggregate_from_rules_still_referential_agnostic():
    import inspect
    source = inspect.getsource(aggregate_from_rules)
    assert "kbis" not in source.lower()
    assert "mistral" not in source.lower()
    assert "ocr" not in source.lower()
