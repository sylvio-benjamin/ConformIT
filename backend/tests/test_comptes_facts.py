import inspect

from app.extraction.comptes import evaluate_comptes_questions, extract_facts_comptes, impacts_from_evaluations
from app.extraction.comptes import questions as comptes_questions
from app.extraction.comptes.extract import expected_unknown_facts
from app.extraction.comptes.patterns import AMBIGUOUS_FACTS, EXPECTED_FACTS
from app.extraction.model import EVAL_INCONNU, EVAL_OUI
from app.extraction.registry import EXTRACTORS, extract_facts
from app.scoring.engine import apply_deterministic_scoring


COMPTES_TEXTE = """
BILAN
Actif circulant 200000
Dettes à court terme 100000
Capitaux propres 300000
Dettes financières 50000
Total passif 450000
Disponibilités 80000
Créances clients 40000
Dettes fournisseurs 20000
COMPTE DE RESULTAT
Chiffre d'affaires 400000
Achats 200000
Résultat net 25000
Charges financières 2000
Résultat d'exploitation 40000
"""


def test_comptes_extractor_is_registered():
    assert "comptes_sociaux" in EXTRACTORS
    facts = extract_facts("comptes_sociaux", COMPTES_TEXTE)
    assert facts["chiffre_affaires"].present is True
    assert facts["capitaux_propres"].value == 300000


def test_q6_q13_are_q5_for_accounts_no_mistral_no_penalty():
    """N-1 absent = limite du document, pas une anomalie à faire deviner."""
    facts = extract_facts_comptes(COMPTES_TEXTE)
    evaluations = evaluate_comptes_questions(facts)
    assert evaluations[6].status == EVAL_INCONNU
    assert evaluations[13].status == EVAL_INCONNU
    assert impacts_from_evaluations(evaluations)[6] == 0
    assert impacts_from_evaluations(evaluations)[13] == 0
    assert "chiffre_affaires_n1" not in expected_unknown_facts(facts)


def test_attendu_is_not_necessary_for_n1_series():
    facts = extract_facts_comptes(COMPTES_TEXTE)
    assert "capitaux_propres_n1" in AMBIGUOUS_FACTS
    assert "chiffre_affaires_n1" in AMBIGUOUS_FACTS
    assert "capitaux_propres_n1" not in EXPECTED_FACTS
    assert "capitaux_propres_n1" not in expected_unknown_facts(facts)
    evaluations = evaluate_comptes_questions(facts)
    assert evaluations[6].status == EVAL_INCONNU
    assert evaluations[13].status == EVAL_INCONNU


def test_demonstrated_facts_produce_conditions():
    evaluations = evaluate_comptes_questions(extract_facts_comptes(COMPTES_TEXTE))
    assert evaluations[1].status == EVAL_OUI
    assert evaluations[4].status == EVAL_OUI
    assert evaluations[11].status == EVAL_OUI


def test_unknown_comptes_questions_have_no_penalty():
    evaluations = evaluate_comptes_questions(extract_facts_comptes(COMPTES_TEXTE))
    scores = impacts_from_evaluations(evaluations)
    assert scores[6] == 0
    assert scores[13] == 0
    details = [
        {
            "question_index": 6,
            "question": "Les capitaux propres ont-ils augmenté sur les 3 derniers exercices ?",
            "reponse": evaluations[6].answer,
            "justification": evaluations[6].rationale,
            "evaluation_status": "INCONNU",
            "score": 10,
        }
    ]
    breakdown = apply_deterministic_scoring(details, "comptes_sociaux")
    assert details[0]["triggered"] is False
    assert details[0]["impact"] == 0
    assert breakdown["score_global"] == 0


def test_comptes_questions_do_not_import_mistral():
    source = inspect.getsource(comptes_questions)
    assert "mistral" not in source.lower()
    assert "appel_" not in source
