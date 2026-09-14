"""Questions comptes = conditions sur des faits. Pas de LLM."""

from __future__ import annotations

from typing import Dict, Optional

from app.extraction.model import EVAL_INCONNU, EVAL_NON, EVAL_OUI, Evaluation, Fact, FactSet

# Impacts si la condition est fausse. INCONNU n'utilise pas cette table.
IMPACT_IF_NON = {
    1: 10, 2: 10, 3: 6, 4: 10, 5: 6, 6: 6, 7: 10, 8: 6, 9: 6, 10: 6,
    11: 10, 12: 6, 13: 0, 14: 6, 15: 6,
}


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


def _compare(index: int, fact: Optional[Fact], predicate, condition: str, facts: FactSet, *names: str) -> Evaluation:
    if not fact or not fact.present:
        return _inconnu(index, condition, facts, *names)
    if predicate(fact.value):
        return _eval(index, EVAL_OUI, "Oui", condition, f"{fact.name}={fact.value}", facts, *names)
    return _eval(index, EVAL_NON, "Non", condition, f"{fact.name}={fact.value}", facts, *names)


def evaluate_comptes_questions(facts: FactSet, **_: object) -> Dict[int, Evaluation]:
    ac = facts.get("actif_circulant")
    dct = facts.get("dettes_court_terme")
    cp = facts.get("capitaux_propres")
    cp_n1 = facts.get("capitaux_propres_n1")
    ca = facts.get("chiffre_affaires")
    ca_n1 = facts.get("chiffre_affaires_n1")
    achats = facts.get("achats")
    clients = facts.get("creances_clients")
    fournisseurs = facts.get("dettes_fournisseurs")
    dispo = facts.get("disponibilites")
    df = facts.get("dettes_financieres")
    rn = facts.get("resultat_net")
    cf = facts.get("charges_financieres")
    rexp = facts.get("resultat_exploitation")
    liquidite = facts.get("ratio_liquidite")
    endettement = facts.get("ratio_endettement")
    autonomie = facts.get("ratio_autonomie")

    frng_ok = None
    if ac and ac.present and cp and cp.present and df and df.present:
        frng_ok = (int(cp.value) + int(df.value)) - int(ac.value) > 0
    bfr_jours = None
    if ac and ac.present and dct and dct.present and ca and ca.present and ca.value:
        bfr_jours = ((int(ac.value) - int(dct.value)) / int(ca.value)) * 365
    treso = None
    if dispo and dispo.present and dct and dct.present:
        treso = int(dispo.value) - int(dct.value)
    clients_jours = None
    if clients and clients.present and ca and ca.present and ca.value:
        clients_jours = (int(clients.value) / int(ca.value)) * 365
    fourn_jours = None
    if fournisseurs and fournisseurs.present and achats and achats.present and achats.value:
        fourn_jours = (int(fournisseurs.value) / int(achats.value)) * 365
    marge_pct = None
    if ca and ca.present and achats and achats.present and ca.value:
        marge_pct = ((int(ca.value) - int(achats.value)) / int(ca.value)) * 100
    charges_pct = None
    if cf and cf.present and rexp and rexp.present and rexp.value:
        charges_pct = (int(cf.value) / int(rexp.value)) * 100
    couverture = None
    if rexp and rexp.present and cf and cf.present and cf.value:
        couverture = int(rexp.value) / int(cf.value)

    def from_bool(index: int, value: Optional[bool], condition: str, *names: str) -> Evaluation:
        if value is None:
            return _inconnu(index, condition, facts, *names)
        if value:
            return _eval(index, EVAL_OUI, "Oui", condition, condition, facts, *names)
        return _eval(index, EVAL_NON, "Non", condition, condition, facts, *names)

    return {
        1: _compare(1, liquidite, lambda v: v >= 1, "ratio_liquidite >= 1", facts, "ratio_liquidite"),
        2: from_bool(2, frng_ok, "FRNG > 0", "capitaux_propres", "dettes_financieres", "actif_circulant"),
        3: from_bool(3, None if bfr_jours is None else bfr_jours <= 90, "BFR <= 90j", "actif_circulant", "chiffre_affaires"),
        4: _compare(4, cp, lambda v: v > 0, "capitaux_propres > 0", facts, "capitaux_propres"),
        5: _compare(5, endettement, lambda v: v < 1, "ratio_endettement < 1", facts, "ratio_endettement"),
        6: _inconnu(6, "capitaux_propres_n1.unknown", facts, "capitaux_propres_n1")
        if not (cp and cp.present and cp_n1 and cp_n1.present)
        else from_bool(6, int(cp.value) >= int(cp_n1.value), "CP N >= CP N-1", "capitaux_propres", "capitaux_propres_n1"),
        7: from_bool(7, None if treso is None else treso > 0, "tresorerie_nette > 0", "disponibilites", "dettes_court_terme"),
        8: _compare(8, autonomie, lambda v: v >= 0.20, "autonomie >= 20%", facts, "ratio_autonomie"),
        9: from_bool(9, None if clients_jours is None else clients_jours <= 90, "créances <= 90j", "creances_clients", "chiffre_affaires"),
        10: from_bool(10, None if fourn_jours is None else fourn_jours <= 90, "fournisseurs <= 90j", "dettes_fournisseurs", "achats"),
        11: _compare(11, rn, lambda v: v > 0, "resultat_net > 0", facts, "resultat_net"),
        12: from_bool(12, None if marge_pct is None else marge_pct >= 30, "marge_brute >= 30%", "chiffre_affaires", "achats"),
        13: _inconnu(13, "chiffre_affaires_n1.unknown", facts, "chiffre_affaires_n1")
        if not (ca and ca.present and ca_n1 and ca_n1.present)
        else from_bool(13, int(ca.value) > int(ca_n1.value), "CA N > CA N-1", "chiffre_affaires", "chiffre_affaires_n1"),
        14: from_bool(14, None if charges_pct is None else charges_pct <= 10, "charges financières <= 10%", "charges_financieres", "resultat_exploitation"),
        15: from_bool(15, None if couverture is None else couverture >= 3, "couverture dettes >= 3", "resultat_exploitation", "charges_financieres"),
    }


def impacts_from_evaluations(evaluations: Dict[int, Evaluation]) -> Dict[int, int]:
    """INCONNU = 0. Pas de pénalité artificielle."""
    scores = {}
    for index, evaluation in evaluations.items():
        if evaluation.status == EVAL_NON:
            scores[index] = IMPACT_IF_NON.get(index, 0)
        else:
            scores[index] = 0
    return scores
