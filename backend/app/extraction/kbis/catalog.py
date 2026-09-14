"""Catalogue Kbis : questions factuelles. Connaissance, pas moteur.

Chaque question déclare ses faits requis. Absence de preuve → INCONNU, pas NON.
Q16, Q27, Q28, Q30 sont conditionnelles : pas d'historique / pas de nationalité /
pas de mention → INCONNU.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

THRESHOLDS = {
    "anciennete_ans": 3,
    "dates_proches_jours": 366,
    "capital_min": 10000,
    "etablissements_multi": 1,
    "etablissements_seuil": 2,
    "dirigeants_seuil": 1,
}

FORMES_CATEGORIE = ("SAS", "SASU", "SARL", "SA", "EURL", "SNC")

# Q16 / Q27 / Q28 / Q30 : jamais d'invention si le fait n'est pas dans le document.
CONDITIONAL_IDS = ("Q16", "Q17", "Q22", "Q23", "Q27", "Q28", "Q30")
SOLID_IDS = tuple(
    f"Q{i:02d}" for i in (
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 21, 24, 25, 26, 29,
    )
)


def _q(
    index: int,
    question: str,
    required_facts: Tuple[str, ...],
    *,
    kind: str,
    calculation: str,
    priority: str = "solid",
    rule: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "id": f"Q{index:02d}",
        "index": index,
        "question": question,
        "required_facts": list(required_facts),
        "type": kind,
        "calculation": calculation,
        "priority": priority,
    }
    if rule:
        payload["rule"] = rule
    return payload


def _rule(
    rule_id: str,
    risk_type: str,
    severity: str,
    max_impact: int,
    title: str,
    condition: str,
    trigger: str,
) -> Dict[str, Any]:
    return {
        "id": rule_id,
        "risk_type": risk_type,
        "severity": severity,
        "max_impact": max_impact,
        "title": title,
        "condition": condition,
        "trigger": trigger,
        "referentiel": "extrait_kbis",
    }


QUESTIONS: Tuple[Dict[str, Any], ...] = (
    _q(1, "L'entreprise est-elle immatriculée au Registre du commerce et des sociétés (RCS) ?",
       ("siren", "mention_rcs"), kind="calculated", calculation="immatriculee_rcs",
       rule=_rule("RULE-JUR-001", "juridique", "élevée", 40, "Immatriculation RCS",
                  "information obligatoire absente (pas de RCS)", "NON")),
    _q(2, "Le numéro SIREN de l'entreprise est-il présent et identifiable ?",
       ("siren",), kind="presence", calculation="siren.present",
       rule=_rule("RULE-JUR-004", "juridique", "élevée", 20, "SIREN identifiable",
                  "SIREN absent ou non identifiable", "NON")),
    _q(3, "La dénomination sociale de l'entreprise est-elle clairement identifiable ?",
       ("denomination",), kind="presence", calculation="denomination.present"),
    _q(4, "La forme juridique de l'entreprise est-elle identifiable ?",
       ("forme_juridique",), kind="presence", calculation="forme_juridique.present"),
    _q(5, "La date d'immatriculation de l'entreprise est-elle indiquée ?",
       ("date_immatriculation",), kind="presence", calculation="date_immatriculation.present"),
    _q(6, "L'entreprise est-elle immatriculée depuis plus de 3 ans ?",
       ("date_immatriculation",), kind="calculated",
       calculation="today - date_immatriculation > anciennete_ans",
       rule=_rule("RULE-ADM-002", "administratif", "moyenne", 2, "Ancienneté d'immatriculation",
                  "immatriculation inférieure à 3 ans", "NON")),
    _q(7, "L'entreprise est-elle actuellement en activité selon les informations du document ?",
       ("etat_activite",), kind="calculated", calculation="etat_activite == actif",
       priority="solid",
       rule=_rule("RULE-JUR-005", "juridique", "élevée", 20, "Entreprise en activité",
                  "activité non démontrée ou cessation/radiation", "NON")),
    _q(8, "Une date de début d'activité est-elle renseignée ?",
       ("date_debut_activite",), kind="presence", calculation="date_debut_activite.present"),
    _q(9, "La date de début d'activité est-elle postérieure à la date d'immatriculation ?",
       ("date_debut_activite", "date_immatriculation"), kind="calculated",
       calculation="date_debut_activite > date_immatriculation",
       rule=_rule("RULE-ADM-005", "administratif", "moyenne", 6, "Ordre des dates",
                  "début d'activité antérieur à l'immatriculation", "NON")),
    _q(10, "La date de début d'activité est-elle proche de la date d'immatriculation selon le seuil métier défini ?",
       ("date_debut_activite", "date_immatriculation"), kind="calculated",
       calculation="écart dates <= dates_proches_jours",
       rule=_rule("RULE-ADM-004", "administratif", "faible", 10, "Cohérence des dates",
                  "écart entre immatriculation et début d'activité", "NON")),
    _q(11, "L'adresse du siège social est-elle renseignée ?",
       ("adresse_siege",), kind="presence", calculation="adresse_siege.present"),
    _q(12, "Le siège social est-il situé en France ?",
       ("adresse_siege",), kind="calculated", calculation="adresse_siege en France",
       rule=_rule("RULE-ADM-006", "administratif", "moyenne", 8, "Siège en France",
                  "siège social hors de France", "NON")),
    _q(13, "Plusieurs établissements sont-ils enregistrés ?",
       ("nombre_etablissements",), kind="calculated",
       calculation="count(etablissements) > etablissements_multi",
       rule=_rule("RULE-ADM-003", "administratif", "faible", 4, "Multi-établissements",
                  "établissement unique", "NON")),
    _q(14, "L'entreprise possède-t-elle au moins un établissement distinct de son siège social ?",
       ("nombre_etablissements",), kind="calculated",
       calculation="nombre_etablissements > 1"),
    _q(15, "Le nombre d'établissements enregistrés est-il supérieur à un seuil défini ?",
       ("nombre_etablissements",), kind="calculated",
       calculation="nombre_etablissements > etablissements_seuil"),
    _q(16, "Une modification récente de l'adresse du siège est-elle identifiable dans les informations disponibles ?",
       ("transfert_siege",), kind="presence", calculation="transfert_siege.present",
       priority="conditional",
       rule=_rule("RULE-ADM-001", "administratif", "moyenne", 10, "Modification du siège",
                  "transfert ou changement d'adresse identifiable", "OUI")),
    _q(17, "L'établissement principal est-il identifiable ?",
       ("etablissement_principal",), kind="presence",
       calculation="etablissement_principal.present", priority="conditional"),
    _q(18, "Le capital social est-il renseigné ?",
       ("capital_social",), kind="presence", calculation="capital_social.present"),
    _q(19, "Le capital social est-il supérieur à un seuil défini ?",
       ("capital_social",), kind="calculated", calculation="capital_social > capital_min",
       rule=_rule("RULE-FIN-001", "financier", "élevée", 6, "Capital social",
                  "capital social inférieur au seuil", "NON")),
    _q(20, "Le capital social est-il variable ?",
       ("capital_variable",), kind="presence", calculation="capital_variable.present"),
    _q(21, "La forme juridique appartient-elle à une catégorie juridique déterminée ?",
       ("forme_juridique",), kind="calculated", calculation="forme_juridique in FORMES_CATEGORIE",
       rule=_rule("RULE-JUR-002", "juridique", "moyenne", 4, "Catégorie juridique",
                  "forme hors catégorie retenue", "NON")),
    _q(22, "La durée de la société est-elle renseignée ?",
       ("duree_societe",), kind="presence", calculation="duree_societe.present",
       priority="conditional"),
    _q(23, "La société est-elle constituée pour une durée déterminée ou indéterminée, lorsque cette information est disponible ?",
       ("duree_nature",), kind="value", calculation="duree_nature",
       priority="conditional"),
    _q(24, "Au moins un dirigeant ou représentant légal est-il identifié ?",
       ("dirigeants_count",), kind="calculated", calculation="dirigeants_count >= 1"),
    _q(25, "La fonction de chaque dirigeant ou représentant légal est-elle identifiable ?",
       ("dirigeant_fonction",), kind="presence", calculation="dirigeant_fonction.present"),
    _q(26, "Le nombre de dirigeants ou représentants mentionnés est-il supérieur à un seuil défini ?",
       ("dirigeants_count",), kind="calculated",
       calculation="dirigeants_count > dirigeants_seuil"),
    _q(27, "La nationalité d'au moins un dirigeant est-elle renseignée ?",
       ("nationalite",), kind="presence", calculation="nationalite.present",
       priority="conditional"),
    _q(28, "Un dirigeant de nationalité étrangère est-il identifiable lorsque la nationalité est explicitement disponible ?",
       ("nationalite",), kind="calculated", calculation="nationalite != Française",
       priority="conditional",
       rule=_rule("RULE-REP-001", "reputation", "moyenne", 1, "Nationalité des dirigeants",
                  "dirigeant de nationalité étrangère", "OUI")),
    _q(29, "Un commissaire aux comptes est-il mentionné dans le document ?",
       ("commissaire_comptes",), kind="presence", calculation="commissaire_comptes == true",
       rule=_rule("RULE-COM-001", "conformite", "élevée", 10, "Commissaire aux comptes",
                  "absence de commissaire aux comptes", "NON")),
    _q(30, "Une mention de radiation, dissolution ou procédure collective est-elle identifiée ?",
       ("mention_procedure",), kind="presence", calculation="mention_procedure.present",
       priority="conditional",
       rule=_rule("RULE-JUR-006", "juridique", "élevée", 30, "Mention de procédure",
                  "radiation, dissolution ou procédure collective identifiable", "OUI")),
)

QUESTION_BY_INDEX = {item["index"]: item for item in QUESTIONS}
QUESTION_BY_ID = {item["id"]: item for item in QUESTIONS}


def questions_json() -> Dict[str, str]:
    return {str(item["index"]): item["question"] for item in QUESTIONS}


def kbis_scoring_rules() -> Dict[int, Dict[str, Any]]:
    rules: Dict[int, Dict[str, Any]] = {}
    for item in QUESTIONS:
        rule = item.get("rule")
        if not rule:
            continue
        rules[item["index"]] = {
            **rule,
            "question": item["question"],
            "version": "1.0",
        }
    return rules
