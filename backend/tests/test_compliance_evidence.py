from app.services.compliance_evidence import (
    REVIEW_STATUSES,
    TREATMENT_STRATEGIES,
    should_propose,
)


def test_should_propose_medium_and_above():
    assert should_propose("medium") is True
    assert should_propose("high") is True
    assert should_propose("critical") is True
    assert should_propose("low") is False
    assert should_propose("info") is False
    assert should_propose(None) is False


def test_review_and_strategy_vocabularies():
    assert REVIEW_STATUSES == {"accepted", "rejected"}
    assert TREATMENT_STRATEGIES == {"mitigate", "accept", "transfer", "avoid"}
