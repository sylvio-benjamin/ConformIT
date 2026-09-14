"""Cycle de vie des jobs d'analyse + extraction de findings.

Le pipeline /analyser/ reste la source des scores. Ce module journalise
l'exécution et structure les questions/réponses déjà calculées.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

ALLOWED_TRANSITIONS = {
    "queued": {"running", "cancelled", "failed"},
    "running": {"completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


def transition(current: str, target: str) -> str:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(f"Transition interdite: {current} → {target}")
    return target


def _severity_from_score(score: Optional[int]) -> str:
    if score is None:
        return "info"
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def extract_findings(details: Optional[Iterable[Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not details:
        return findings
    for item in details:
        if not isinstance(item, dict):
            continue
        justification = item.get("justification") or ""
        if item.get("extraction_failed") or str(justification).startswith("Erreur :") or "Rate limit exceeded" in str(justification):
            continue
        question = item.get("question") or item.get("titre") or "Question"
        answer = item.get("reponse") or item.get("answer") or ""
        raw_score = item.get("score")
        try:
            score = int(raw_score) if raw_score is not None and raw_score != "" else None
        except (TypeError, ValueError):
            score = None
        evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        findings.append({
            "title": str(question)[:255],
            "detail": justification or str(answer),
            "severity": item.get("rule_severity") or _severity_from_score(score),
            "score": score,
            "rule_id": item.get("rule_id"),
            "risk_type": item.get("risk_type"),
            "source_question": str(question)[:255],
            "rule_version": item.get("rule_version"),
            "rule_condition": item.get("rule_condition"),
            "evidence": {
                "reponse": answer,
                "justification": justification,
                "page": evidence.get("page") or item.get("page"),
                "snippet": evidence.get("snippet"),
                "method": evidence.get("method") or "regle_deterministe",
            },
        })
    return findings


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def job_to_dict(job) -> Dict[str, Any]:
    return {
        "id": str(job.id),
        "slug": job.slug,
        "filename": job.filename,
        "status": job.status,
        "error_message": job.error_message,
        "result_summary": job.result_summary or {},
        "analysis_id": str(job.analysis_id) if job.analysis_id else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
