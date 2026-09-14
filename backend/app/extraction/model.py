"""Vocabulaire contrôlé : un fait n'est pas une phrase d'IA."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional

STATUS_PRESENT = "present"
STATUS_ABSENT = "absent"
STATUS_UNKNOWN = "unknown"

EVAL_OUI = "OUI"
EVAL_NON = "NON"
EVAL_INCONNU = "INCONNU"
EVAL_NON_APPLICABLE = "NON_APPLICABLE"
EVAL_VALEUR = "VALEUR"


@dataclass
class Evidence:
    source: str = "pdf_text"
    snippet: str = ""
    matched_pattern: str = ""
    page: Optional[int] = None
    matched_keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Fact:
    name: str
    type: str
    status: str = STATUS_UNKNOWN
    value: Any = None
    evidence: Optional[Evidence] = None

    @property
    def present(self) -> bool:
        return self.status == STATUS_PRESENT and self.value not in (None, "")

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "fact": self.name,
            "type": self.type,
            "status": self.status,
            "value": self.value,
        }
        if self.evidence:
            payload.update(self.evidence.to_dict())
        return payload


@dataclass
class Evaluation:
    question_index: int
    status: str
    answer: str
    condition: str
    rationale: str
    fact_names: List[str] = field(default_factory=list)
    evidence: Optional[Evidence] = None

    @property
    def resolved(self) -> bool:
        return self.status != EVAL_INCONNU

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "question_index": self.question_index,
            "status": self.status,
            "answer": self.answer,
            "condition": self.condition,
            "rationale": self.rationale,
            "fact_names": self.fact_names,
        }
        if self.evidence:
            payload["evidence"] = self.evidence.to_dict()
        return payload


class FactSet:
    """Faits typés d'un référentiel. Pas de texte libre généré."""

    def __init__(self, facts: Iterable[Fact]):
        from app.extraction.contract import assert_fact_contract

        self._facts = {}
        for fact in facts:
            if not isinstance(fact, Fact):
                raise TypeError("FactSet n'accepte que des Fact typés")
            assert_fact_contract(fact)
            self._facts[fact.name] = fact

    def __getitem__(self, name: str) -> Fact:
        return self._facts[name]

    def get(self, name: str, default: Optional[Fact] = None) -> Optional[Fact]:
        return self._facts.get(name, default)

    def __contains__(self, name: str) -> bool:
        return name in self._facts

    def names(self) -> List[str]:
        return list(self._facts)

    def replace(self, fact: Fact) -> None:
        from app.extraction.contract import assert_fact_contract

        if not isinstance(fact, Fact):
            raise TypeError("FactSet n'accepte que des Fact typés")
        assert_fact_contract(fact)
        self._facts[fact.name] = fact

    def to_dict(self) -> Dict[str, Any]:
        return {name: fact.to_dict() for name, fact in self._facts.items()}

    def plain_values(self) -> Dict[str, Any]:
        return {name: fact.value for name, fact in self._facts.items()}
