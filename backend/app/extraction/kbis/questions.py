"""Questions Kbis = conditions sur des faits. Pas de lecture du texte brut."""

from __future__ import annotations

from datetime import date
from typing import Callable, Dict, Optional

from app.extraction.kbis.catalog import FORMES_CATEGORIE, QUESTION_BY_INDEX, QUESTIONS, THRESHOLDS
from app.extraction.kbis.patterns import FOREIGN_COUNTRIES
from app.extraction.model import (
    EVAL_INCONNU,
    EVAL_NON,
    EVAL_NON_APPLICABLE,
    EVAL_OUI,
    EVAL_VALEUR,
    Evaluation,
    Fact,
    FactSet,
)
from app.extraction.normalize import fold


def _eval(index: int, status: str, answer: str, condition: str, rationale: str, facts: FactSet, *names: str) -> Evaluation:
    evidence = None
    for name in names:
        fact = facts.get(name)
        if fact and fact.evidence:
            evidence = fact.evidence
            break
    return Evaluation(
        question_index=index,
        status=status,
        answer=answer,
        condition=condition,
        rationale=rationale,
        fact_names=list(names),
        evidence=evidence,
    )


def _inconnu(index: int, condition: str, facts: FactSet, *names: str) -> Evaluation:
    return _eval(index, EVAL_INCONNU, "Inconnu", condition, "Fait insuffisant dans le document", facts, *names)


def _fact(facts: FactSet, name: str) -> Optional[Fact]:
    return facts.get(name)


def _presence(index: int, facts: FactSet, name: str, condition: str) -> Evaluation:
    fact = _fact(facts, name)
    if fact is None or fact.status == "unknown":
        return _inconnu(index, condition, facts, name)
    if fact.status == "absent" or fact.present is False and fact.value is False:
        if fact.status == "absent":
            return _eval(index, EVAL_NON, "Non", f"{name}.absent", "Information explicitement absente", facts, name)
        if fact.value is False:
            return _eval(index, EVAL_NON, "Non", f"{name} == false", "Fait présent à la valeur faux", facts, name)
    if fact.present:
        return _eval(index, EVAL_OUI, "Oui", f"{name}.present", f"{name}={fact.value}", facts, name)
    return _inconnu(index, condition, facts, name)


def _flag(index: int, facts: FactSet, name: str, condition: str) -> Evaluation:
    fact = _fact(facts, name)
    if fact is None or fact.status == "unknown":
        return _inconnu(index, condition, facts, name)
    if fact.status == "absent":
        return _eval(index, EVAL_NON, "Non", f"{name}.absent", "Mention explicitement absente", facts, name)
    if fact.present and fact.value is True:
        return _eval(index, EVAL_OUI, "Oui", f"{name} == true", "Mention positive", facts, name)
    if fact.present and fact.value is False:
        return _eval(index, EVAL_NON, "Non", f"{name} == false", "Mention négative explicite", facts, name)
    return _inconnu(index, condition, facts, name)


def _immatriculee_rcs(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    siren = _fact(facts, "siren")
    mention = _fact(facts, "mention_rcs")
    if siren and siren.status == "absent":
        return _eval(index, EVAL_NON, "Non", "siren.absent", "Immatriculation explicitement absente", facts, "siren")
    if (siren and siren.present) or (mention and mention.present):
        return _eval(index, EVAL_OUI, "Oui", "siren.present or mention_rcs.present", "Immatriculation RCS identifiable", facts, "siren", "mention_rcs")
    return _inconnu(index, "immatriculation.unknown", facts, "siren", "mention_rcs")


def _anciennete(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    immat = _fact(facts, "date_immatriculation")
    if not immat or not immat.present:
        return _inconnu(index, "date_immatriculation.unknown", facts, "date_immatriculation")
    today = as_of or date.today()
    parsed = date.fromisoformat(str(immat.value))
    years = max(0, (today - parsed).days // 365)
    seuil = THRESHOLDS["anciennete_ans"]
    if years >= seuil:
        return _eval(index, EVAL_OUI, "Oui", f"anciennete >= {seuil}", f"Immatriculée depuis {years} an(s)", facts, "date_immatriculation")
    return _eval(index, EVAL_NON, "Non", f"anciennete < {seuil}", f"Immatriculée depuis {years} an(s)", facts, "date_immatriculation")


def _en_activite(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    etat = _fact(facts, "etat_activite")
    if not etat or not etat.present:
        return _inconnu(index, "etat_activite.unknown", facts, "etat_activite")
    if etat.value == "actif":
        return _eval(index, EVAL_OUI, "Oui", "etat_activite == actif", "En activité", facts, "etat_activite")
    return _eval(index, EVAL_NON, "Non", f"etat_activite == {etat.value}", f"État : {etat.value}", facts, "etat_activite")


def _debut_posterieur(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    immat = _fact(facts, "date_immatriculation")
    debut = _fact(facts, "date_debut_activite")
    if not immat or not immat.present or not debut or not debut.present:
        return _inconnu(index, "dates.unknown", facts, "date_immatriculation", "date_debut_activite")
    later = date.fromisoformat(str(debut.value)) > date.fromisoformat(str(immat.value))
    if later:
        return _eval(index, EVAL_OUI, "Oui", "date_debut > date_immatriculation", "Début postérieur à l'immatriculation", facts, "date_immatriculation", "date_debut_activite")
    return _eval(index, EVAL_NON, "Non", "date_debut <= date_immatriculation", "Début non postérieur à l'immatriculation", facts, "date_immatriculation", "date_debut_activite")


def _dates_proches(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    immat = _fact(facts, "date_immatriculation")
    debut = _fact(facts, "date_debut_activite")
    if not immat or not immat.present or not debut or not debut.present:
        return _inconnu(index, "dates.unknown", facts, "date_immatriculation", "date_debut_activite")
    delta = abs((date.fromisoformat(str(debut.value)) - date.fromisoformat(str(immat.value))).days)
    seuil = THRESHOLDS["dates_proches_jours"]
    if delta <= seuil:
        return _eval(index, EVAL_OUI, "Oui", f"écart dates <= {seuil}j", f"Écart {delta} jour(s)", facts, "date_immatriculation", "date_debut_activite")
    return _eval(index, EVAL_NON, "Non", f"écart dates > {seuil}j", f"Écart {delta} jour(s)", facts, "date_immatriculation", "date_debut_activite")


def _siege_france(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    adresse = _fact(facts, "adresse_siege")
    if not adresse or not adresse.present:
        return _inconnu(index, "adresse_siege.unknown", facts, "adresse_siege")
    folded = fold(str(adresse.value))
    if any(country in folded for country in FOREIGN_COUNTRIES):
        return _eval(index, EVAL_NON, "Non", "adresse_siege hors France", str(adresse.value), facts, "adresse_siege")
    import re
    if "france" in folded or re.search(r"\b\d{5}\b", folded):
        return _eval(index, EVAL_OUI, "Oui", "adresse_siege en France", str(adresse.value), facts, "adresse_siege")
    return _inconnu(index, "adresse_siege.ambiguous", facts, "adresse_siege")


def _count_gt(name: str, threshold_key: str, inclusive_one: bool = False):
    def _inner(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
        fact = _fact(facts, name)
        if not fact or not fact.present:
            return _inconnu(index, f"{name}.unknown", facts, name)
        seuil = THRESHOLDS[threshold_key]
        count = int(fact.value)
        if count > seuil:
            return _eval(index, EVAL_OUI, "Oui", f"{name} > {seuil}", f"{count}", facts, name)
        return _eval(index, EVAL_NON, "Non", f"{name} <= {seuil}", f"{count}", facts, name)
    return _inner


def _capital_seuil(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    capital = _fact(facts, "capital_social")
    if not capital or not capital.present:
        return _inconnu(index, "capital_social.unknown", facts, "capital_social")
    seuil = THRESHOLDS["capital_min"]
    if int(capital.value) > seuil:
        return _eval(index, EVAL_OUI, "Oui", f"capital > {seuil}", f"{capital.value} €", facts, "capital_social")
    return _eval(index, EVAL_NON, "Non", f"capital <= {seuil}", f"{capital.value} €", facts, "capital_social")


def _forme_categorie(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    forme = _fact(facts, "forme_juridique")
    if not forme or not forme.present:
        return _inconnu(index, "forme_juridique.unknown", facts, "forme_juridique")
    if str(forme.value) in FORMES_CATEGORIE:
        return _eval(index, EVAL_OUI, "Oui", "forme in FORMES_CATEGORIE", str(forme.value), facts, "forme_juridique")
    return _eval(index, EVAL_NON, "Non", "forme hors FORMES_CATEGORIE", str(forme.value), facts, "forme_juridique")


def _dirigeants_min(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    count = _fact(facts, "dirigeants_count")
    if not count or not count.present:
        return _inconnu(index, "dirigeants_count.unknown", facts, "dirigeants_count")
    if int(count.value) >= 1:
        return _eval(index, EVAL_OUI, "Oui", "dirigeants_count >= 1", f"{count.value} dirigeant(s)", facts, "dirigeants_count")
    return _eval(index, EVAL_NON, "Non", "dirigeants_count == 0", "Aucun dirigeant", facts, "dirigeants_count")


def _nationalite_etrangere(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    nationalite = _fact(facts, "nationalite")
    if not nationalite or not nationalite.present:
        return _inconnu(index, "nationalite.unknown", facts, "nationalite")
    folded = fold(str(nationalite.value))
    if folded.startswith("franc"):
        return _eval(index, EVAL_NON, "Non", "nationalite == Française", "Nationalité française", facts, "nationalite")
    return _eval(index, EVAL_OUI, "Oui", "nationalite != Française", f"Nationalité {nationalite.value}", facts, "nationalite")


def _duree_valeur(index: int, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    nature = _fact(facts, "duree_nature")
    if not nature or not nature.present:
        return _inconnu(index, "duree_nature.unknown", facts, "duree_nature")
    return _eval(index, EVAL_VALEUR, str(nature.value), "duree_nature", str(nature.value), facts, "duree_nature")


CALCULATORS: Dict[str, Callable] = {
    "immatriculee_rcs": _immatriculee_rcs,
    "today - date_immatriculation > anciennete_ans": _anciennete,
    "etat_activite == actif": _en_activite,
    "date_debut_activite > date_immatriculation": _debut_posterieur,
    "écart dates <= dates_proches_jours": _dates_proches,
    "adresse_siege en France": _siege_france,
    "count(etablissements) > etablissements_multi": _count_gt("nombre_etablissements", "etablissements_multi"),
    "nombre_etablissements > 1": _count_gt("nombre_etablissements", "etablissements_multi"),
    "nombre_etablissements > etablissements_seuil": _count_gt("nombre_etablissements", "etablissements_seuil"),
    "capital_social > capital_min": _capital_seuil,
    "forme_juridique in FORMES_CATEGORIE": _forme_categorie,
    "dirigeants_count >= 1": _dirigeants_min,
    "dirigeants_count > dirigeants_seuil": _count_gt("dirigeants_count", "dirigeants_seuil"),
    "nationalite != Française": _nationalite_etrangere,
    "duree_nature": _duree_valeur,
}


def _evaluate_spec(spec: Dict, facts: FactSet, as_of: Optional[date]) -> Evaluation:
    index = spec["index"]
    kind = spec["type"]
    names = tuple(spec["required_facts"])
    if kind == "presence":
        if spec["id"] in {"Q16", "Q20", "Q30"} or spec["calculation"].endswith(".present") and "transfert" in spec["calculation"]:
            return _presence(index, facts, names[0], spec["calculation"])
        if spec["id"] == "Q29":
            return _flag(index, facts, "commissaire_comptes", spec["calculation"])
        return _presence(index, facts, names[0], spec["calculation"])
    if kind == "value":
        return _duree_valeur(index, facts, as_of)
    calculator = CALCULATORS.get(spec["calculation"])
    if calculator is None:
        return _inconnu(index, spec["calculation"], facts, *names)
    return calculator(index, facts, as_of)


def evaluate_kbis_questions(facts: FactSet, as_of: Optional[date] = None) -> Dict[int, Evaluation]:
    """QUESTION → CONDITION → FAITS → RÉPONSE. Le scoring n'entre pas ici."""
    return {spec["index"]: _evaluate_spec(spec, facts, as_of) for spec in QUESTIONS}


def impacts_from_evaluations(evaluations: Dict[int, Evaluation]) -> Dict[int, int]:
    """INCONNU et N/A → 0. Seul le trigger déclaré produit un impact."""
    impacts: Dict[int, int] = {}
    for index, evaluation in evaluations.items():
        spec = QUESTION_BY_INDEX.get(index) or {}
        rule = spec.get("rule") or {}
        if evaluation.status in {EVAL_INCONNU, EVAL_NON_APPLICABLE} or not rule:
            impacts[index] = 0
            continue
        trigger = rule.get("trigger")
        if trigger == "NON" and evaluation.status == EVAL_NON:
            impacts[index] = int(rule["max_impact"])
        elif trigger == "OUI" and evaluation.status == EVAL_OUI:
            impacts[index] = int(rule["max_impact"])
        else:
            impacts[index] = 0
    return impacts
