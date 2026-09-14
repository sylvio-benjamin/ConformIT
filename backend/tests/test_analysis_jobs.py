import pytest

from app.services.analysis_jobs import extract_findings, transition


def test_allowed_transitions():
    assert transition("queued", "running") == "running"
    assert transition("running", "completed") == "completed"
    assert transition("running", "failed") == "failed"
    assert transition("running", "cancelled") == "cancelled"
    assert transition("queued", "cancelled") == "cancelled"


def test_forbidden_transition():
    with pytest.raises(ValueError):
        transition("completed", "running")
    with pytest.raises(ValueError):
        transition("failed", "completed")


def test_extract_findings_from_details():
    findings = extract_findings([
        {"question": "Dirigeant identifié ?", "reponse": "Oui", "score": 20, "justification": "OK"},
        {"question": "Litiges", "reponse": "Plusieurs", "score": 85, "justification": "Risque élevé"},
        "ignore-me",
    ])
    assert len(findings) == 2
    assert findings[0]["severity"] == "low"
    assert findings[1]["severity"] == "critical"
    assert findings[1]["title"] == "Litiges"
    assert findings[1]["evidence"]["reponse"] == "Plusieurs"


def test_extract_findings_copies_rule_trace():
    findings = extract_findings([
        {
            "question": "RCS présent ?",
            "reponse": "Non",
            "score": 40,
            "justification": "Absent",
            "rule_id": "RULE-JUR-001",
            "risk_type": "juridique",
            "rule_severity": "élevée",
            "rule_version": "1.0",
            "rule_condition": "information obligatoire absente",
            "evidence": {"page": 3, "snippet": "RCS 123456789", "method": "regle_deterministe"},
        },
    ])
    assert findings[0]["rule_id"] == "RULE-JUR-001"
    assert findings[0]["risk_type"] == "juridique"
    assert findings[0]["severity"] == "élevée"
    assert findings[0]["rule_version"] == "1.0"
    assert findings[0]["evidence"]["page"] == 3
    assert findings[0]["evidence"]["snippet"] == "RCS 123456789"


def test_extract_findings_skips_extraction_errors():
    findings = extract_findings([
        {"question": "RCS ?", "reponse": "Non", "score": 40, "justification": "Erreur : Erreur API Mistral: HTTP 429"},
        {"question": "OK", "reponse": "Oui", "score": 0, "justification": "Présent", "extraction_failed": False},
    ])
    assert len(findings) == 1
    assert findings[0]["title"] == "OK"


def test_extract_findings_empty():
    assert extract_findings(None) == []
    assert extract_findings([]) == []
