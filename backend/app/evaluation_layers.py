"""Contrat d'architecture produit (figé).

Le catalogue sait.
L'applicabilité décide du périmètre.
L'évaluation constate.
Le scoring mesure.

Contrainte de référence : Connaissance ou moteur ?
Oui → EXTRACTOR → FactSet → condition → RULE-* → applicabilité si nécessaire.
Non → exception architecturale → justification → tests.
aggregate_from_rules() reste invariant et agnostique.
INCONNU reste une sortie valide, jamais un constat artificiel.

Niveau C = nouvelle source de RULE-*, pas un nouveau moteur.
scope.en n'est jamais une question, une exigence, une RULE-* ou un score.

P0–P10 restent gelés.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

ARCHITECTURE_RULE = (
    "Le catalogue sait. L'applicabilité décide du périmètre. "
    "L'évaluation constate. Le scoring mesure."
)

EVOLUTION_RULE = (
    "Nouveau référentiel ≠ nouveau moteur. "
    "Nouveau référentiel = nouvelles sources de règles pour le moteur existant."
)

EXTEND_RULE = (
    "On n'améliore pas le moteur en ajoutant de l'intelligence ; "
    "on l'étend en ajoutant des connaissances structurées."
)

EXTENSION_MAP = {
    "document": "nouvel EXTRACTOR",
    "question": "nouvelle condition sur le FactSet",
    "cas_metier": "nouvelle RULE-*",
    "referentiel": "nouvelles questions/règles",
    "applicabilite": "nouvelles règles d'applicabilité",
    "type_document": "type_hint utilisateur",
    "scoring": "aucune modification",
}

PROOF_RULE = "Un document ne doit produire que ce que ses preuves permettent de produire."

OBSERVATION_RULE = (
    "Un document ne produit pas une vérité complète ; "
    "il produit un ensemble de constats justifiables par ses preuves."
)

GUARANTEES = {
    "no_invention": "absence de preuve ≠ réponse supposée",
    "no_artificial_penalty": "INCONNU n'est pas une anomalie implicite",
    "no_engine_drift": "les nouveaux domaines enrichissent les connaissances, pas le calculateur",
    "inconnu_is_valid": "INCONNU reste une sortie valide",
    "inconnu_not_constat": "INCONNU ne doit pas être artificiellement transformé en constat",
    "constat_requires_evidence": "tout constat doit rester justifiable par une preuve du document",
}

DEMONSTRATORS = ("extrait_kbis", "comptes_sociaux")

REVIEW_SIGNAL = (
    "Modifier aggregate_from_rules pour un référentiel, un document "
    "ou un cas métier est un signal architectural."
)

REVIEW_CRITERION = (
    "Le nouveau besoin peut-il être exprimé par de nouvelles connaissances "
    "structurées sans modifier aggregate_from_rules() ?"
)

ARCHITECTURE_STATUS = "FROZEN"

GUARDRAIL = "Connaissance ou moteur ?"

REFERENCE_CONSTRAINT = (
    "Connaissance ou moteur ?",
    "Oui → EXTRACTOR → FactSet → condition → RULE-* → applicabilité si nécessaire",
    "Non → exception architecturale → justification → tests",
    "aggregate_from_rules() reste invariant et agnostique",
    "La provenance d'un RULE-* est sans effet sur le calcul ; seules famille + impact comptent",
    "INCONNU reste une sortie valide et ne doit pas être artificiellement transformé en constat",
    "Tout constat doit rester justifiable par une preuve du document",
)

EVOLUTION_POLICY = (
    "enrichir les connaissances avant d'envisager de toucher au moteur"
)

KNOWLEDGE_PATH = (
    "EXTRACTOR",
    "FactSet",
    "condition",
    "RULE-*",
)

KNOWLEDGE_OPTIONAL = ("applicabilité",)

EXCEPTION_PATH = ("justification", "tests")

ENGINE_CENTER = "aggregate_from_rules"
ENGINE_ROLE = "moteur générique invariant et agnostique"
ENGINE_CONSUMES = ("famille", "impact")
RULE_PROVENANCE_IRRELEVANT = True
INCONNU_IS_VALID_OUTPUT = True
INCONNU_IS_NOT_A_CONSTAT = True
CONSTAT_REQUIRES_EVIDENCE = True
TYPE_CONTEXT_RULE = (
    "Le type de document est un contexte explicite fourni en amont, "
    "pas une déduction du moteur."
)
SELECTOR_REDUCES_STRUCTURAL_UNKNOWN = True
SELECTOR_PRESERVES_DOCUMENTARY_UNKNOWN = True

NORMAL_EXTENSIONS = frozenset({
    "EXTRACTOR",
    "FactSet",
    "FactSet typé",
    "condition",
    "RULE-*",
    "questions + règles",
    "applicabilité",
    "type_hint",
})

ARCHITECTURAL_EXCEPTIONS = frozenset({
    "exception architecturale",
    "aggregate_from_rules",
    "moteur de scoring",
})


def classify_change(extension: str) -> str:
    """Contrainte de revue : normale ou exception à justifier et tester."""
    if extension == "aucune modification":
        return "aucune"
    if extension in ARCHITECTURAL_EXCEPTIONS:
        return "exception"
    if extension in NORMAL_EXTENSIONS or extension in EXTENSION_MAP.values():
        return "normale"
    raise ValueError(f"Extension hors contrat : {extension}")


def route_need(*, structured_knowledge: bool) -> Dict[str, Any]:
    """Garde-fou figé : connaissance structurée, ou exception justifiée et testée."""
    if structured_knowledge:
        return {
            "path": "connaissance",
            "extensions": list(KNOWLEDGE_PATH),
            "optional": list(KNOWLEDGE_OPTIONAL),
            "engine_change": False,
            "requires": (),
        }
    return {
        "path": "exception",
        "extensions": (),
        "engine_change": True,
        "requires": list(EXCEPTION_PATH),
    }

EXTENSION_TABLE = {
    "Nouveau type de document": "EXTRACTOR",
    "Nouveau fait": "FactSet typé",
    "Nouvelle question": "condition",
    "Nouveau cas métier": "RULE-*",
    "Nouveau référentiel": "questions + règles",
    "Nouveau périmètre organisationnel": "applicabilité",
    "Nouveau type de document sélectionnable": "type_hint",
    "Nouveau calcul de score": "exception architecturale",
}

PARALLEL_AMBIGUITY_TESTS = {
    "extrait_kbis": ("Q16",),
    "comptes_sociaux": ("Q6", "Q13"),
}

PHILOSOPHICAL_TEST = {
    "id": "Q16",
    "name": "modification_siege",
    "absent_proof": "INCONNU",
    "invent": False,
    "llm_guess": False,
    "penalty_without_proof": False,
}

EVOLUTION_QUESTION = (
    "Est-ce que j'ajoute une connaissance, ou est-ce que je suis en train de modifier le moteur ?"
)

ATTENDU_NEQ_NECESSAIRE = True

FACT_STATES = {
    "demonstrated": "present",
    "explicitly_absent": "absent",
    "undeterminable": "INCONNU",
    "not_applicable": "NON_APPLICABLE",
}

LEVEL_A = "catalog"
LEVEL_B = "applicability"
LEVEL_C = "normative_content"

SCOPE_EN_FORBIDDEN = frozenset({"question", "exigence", "rule", "finding", "score"})

SEPARATION_RULE = "Extraire ≠ évaluer ≠ scorer."

BOUNDARIES = {
    "extractor": "extrait des faits typés et leurs preuves",
    "question": "interprète les faits via une condition",
    "rule": "transforme le résultat en finding/impact",
    "scoring": "agrège les impacts",
    "mistral": "fallback d'extraction uniquement",
    "ocr": "mécanisme d'extraction en amont, si nécessaire",
    "applicability": "définit le périmètre, sans calculer le risque",
    "catalog": "décrit les référentiels, sans évaluer",
}

INVARIANTS = (
    "aggregate_from_rules est agnostique au référentiel",
    "même mécanique de scoring pour tout référentiel",
    "Niveau C apporte des RULE-* ; pas de moteur parallèle",
    "scope.en est strictement informatif",
    "P0-P10 fermés : pas de modification du moteur de calcul",
    "l'extension porte sur référentiels, questions, conditions et règles",
    "ajouter ISO 27001 ne modifie pas aggregate_from_rules",
    "Extraire ≠ évaluer ≠ scorer",
    "un mot trouvé n'est jamais directement une réponse",
    "INCONNU n'est pas une erreur : le document ne permet pas de conclure",
    "l'IA n'est pas une autorité sémantique : fallback d'extraction seulement",
    "on étend par des connaissances structurées, pas par plus d'intelligence",
    "les cas ambigus restent ambigus",
    "un document ne produit que ce que ses preuves permettent de produire",
    "aucun nouveau document, question ou norme ne modifie aggregate_from_rules",
    "Connaissance ou moteur ?",
    "aggregate_from_rules reste invariant et agnostique",
    "la provenance d'un RULE-* est sans effet sur le calcul",
    "le moteur ne consomme que famille + impact",
    "INCONNU reste une sortie valide et ne doit pas être artificiellement transformé en constat",
    "tout constat doit rester justifiable par une preuve du document",
    "enrichir les connaissances avant d'envisager de toucher au moteur",
    "le type de document est un contexte explicite, pas une déduction du moteur",
    "le sélecteur réduit l'inconnu structurel, pas l'inconnu documentaire",
)

LEVEL_C_STATUS = "BLOCKED_LICENSE"

LAYERS = (
    "iso_catalog",
    "applicability",
    "questions_rules",
    "findings",
    "risk_scoring",
    "weighted_global_score",
)

# Référentiels documentaires déjà évaluables (calculateurs existants).
# Ce ne sont PAS des exigences ISO Niveau C.
OPERATIONAL_REFERENTIALS = {
    "extrait_kbis": "Questions documentaires Kbis",
    "attestation_assurance": "Questions documentaires attestation",
    "comptes_sociaux": "Questions documentaires comptes sociaux",
    "statuts": "Questions documentaires statuts",
}

# Champs catalogue exposables. scope_en volontairement absent.
PUBLIC_CATALOG_FIELDS = frozenset({
    "iso_id",
    "reference",
    "title_en",
    "title_fr",
    "edition",
    "publication_date",
    "ics_codes",
    "owner_committee",
    "current_stage",
    "withdrawn",
    "framework_code",
    "official_source",
    "metadata_source",
})


def refuse_scope_as_normative(_scope_en: Any) -> None:
    """Interdit de transformer le résumé Open Data en exigences ou règles."""
    raise ValueError(
        "scope.en n'est pas un contenu normatif : identification seulement, "
        "jamais une question, une RULE-* ou une exigence Niveau C"
    )


def public_deliverable(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row.get(key) for key in PUBLIC_CATALOG_FIELDS if key in row}


def evaluation_contract(decisions: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    applicable = [
        item.get("framework_code")
        for item in (decisions or [])
        if item.get("applicable")
    ]
    return {
        "layers": list(LAYERS),
        "level_a": LEVEL_A,
        "level_b": LEVEL_B,
        "level_c": LEVEL_C,
        "level_c_status": LEVEL_C_STATUS,
        "architecture_rule": ARCHITECTURE_RULE,
        "evolution_rule": EVOLUTION_RULE,
        "extend_rule": EXTEND_RULE,
        "proof_rule": PROOF_RULE,
        "observation_rule": OBSERVATION_RULE,
        "guarantees": dict(GUARANTEES),
        "demonstrators": list(DEMONSTRATORS),
        "review_signal": REVIEW_SIGNAL,
        "architecture_status": ARCHITECTURE_STATUS,
        "guardrail": GUARDRAIL,
        "reference_constraint": list(REFERENCE_CONSTRAINT),
        "evolution_policy": EVOLUTION_POLICY,
        "review_criterion": REVIEW_CRITERION,
        "is_architecture_constraint": True,
        "architecture_frozen": True,
        "knowledge_path": list(KNOWLEDGE_PATH),
        "knowledge_optional": list(KNOWLEDGE_OPTIONAL),
        "exception_path": list(EXCEPTION_PATH),
        "engine_center": ENGINE_CENTER,
        "engine_role": ENGINE_ROLE,
        "engine_consumes": list(ENGINE_CONSUMES),
        "rule_provenance_irrelevant": RULE_PROVENANCE_IRRELEVANT,
        "inconnu_is_valid_output": INCONNU_IS_VALID_OUTPUT,
        "inconnu_is_not_a_constat": INCONNU_IS_NOT_A_CONSTAT,
        "constat_requires_evidence": CONSTAT_REQUIRES_EVIDENCE,
        "type_context_rule": TYPE_CONTEXT_RULE,
        "selector_reduces_structural_unknown": SELECTOR_REDUCES_STRUCTURAL_UNKNOWN,
        "selector_preserves_documentary_unknown": SELECTOR_PRESERVES_DOCUMENTARY_UNKNOWN,
        "extension_map": dict(EXTENSION_MAP),
        "extension_table": dict(EXTENSION_TABLE),
        "parallel_ambiguity_tests": dict(PARALLEL_AMBIGUITY_TESTS),
        "aggregate_from_rules_stable": True,
        "philosophical_test": dict(PHILOSOPHICAL_TEST),
        "evolution_question": EVOLUTION_QUESTION,
        "attendu_neq_necessaire": ATTENDU_NEQ_NECESSAIRE,
        "fact_states": dict(FACT_STATES),
        "engine_change_requires_justification": True,
        "p0_p10_closed": True,
        "separation_rule": SEPARATION_RULE,
        "boundaries": dict(BOUNDARIES),
        "invariants": list(INVARIANTS),
        "llm_is_semantic_authority": False,
        "unknown_is_error": False,
        "catalog_computes_score": False,
        "applicability_computes_risk": False,
        "scoring_is_referential_agnostic": True,
        "level_c_is_new_rule_source": True,
        "scope_en_is_normative": False,
        "scope_en_forbidden": sorted(SCOPE_EN_FORBIDDEN),
        "operational_referentials": dict(OPERATIONAL_REFERENTIALS),
        "applicable_frameworks": applicable,
        "note": (
            "A = quelles normes existent. "
            "B = lesquelles sont pertinentes et pourquoi. "
            "C = questions/exigences licenciées, bloqué. "
            "L'évaluation actuelle utilise les questions documentaires existantes."
        ),
    }


def explain_layers(decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    yes = [item for item in decisions if item.get("applicable")]
    no = [item for item in decisions if not item.get("applicable")]
    return {
        "applicable": [
            {
                "framework_code": item.get("framework_code"),
                "applicable": True,
                "reasons": item.get("reasons") or [item.get("reason")],
            }
            for item in yes
        ],
        "not_applicable": [
            {
                "framework_code": item.get("framework_code"),
                "applicable": False,
                "reasons": item.get("reasons") or ["Aucun critère d'applicabilité détecté"],
            }
            for item in no
        ],
    }
