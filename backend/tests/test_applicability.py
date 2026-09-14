from app.services.applicability import evaluate_profile, match_condition


def test_empty_condition_always_matches():
    assert match_condition({}, {}) is True
    assert match_condition({"sector": "it"}, {}) is True


def test_boolean_and_list_conditions():
    assert match_condition({"processes_personal_data": True}, {"processes_personal_data": True})
    assert not match_condition({"processes_personal_data": False}, {"processes_personal_data": True})
    assert match_condition({"country": "FR"}, {"country": ["FR", "BE"]})
    assert not match_condition({"country": "US"}, {"country": ["FR", "BE"]})


def test_iso31000_always_applicable():
    decisions = evaluate_profile({"country": "US", "processes_personal_data": False})
    iso = next(item for item in decisions if item["framework_code"] == "iso31000")
    assert iso["applicable"] is True
    assert iso["source_rule"] == "ISO31000_BASE"


def test_rgpd_when_personal_data_or_eea():
    with_pii = evaluate_profile({"processes_personal_data": True, "country": "US"})
    rgpd = next(item for item in with_pii if item["framework_code"] == "rgpd")
    assert rgpd["applicable"] is True

    france = evaluate_profile({"processes_personal_data": False, "country": "FR"})
    rgpd_fr = next(item for item in france if item["framework_code"] == "rgpd")
    assert rgpd_fr["applicable"] is True

    us = evaluate_profile({"processes_personal_data": False, "country": "US"})
    rgpd_us = next(item for item in us if item["framework_code"] == "rgpd")
    assert rgpd_us["applicable"] is False


def test_sox_only_if_listed():
    decisions = evaluate_profile({"listed_company": False})
    sox = next(item for item in decisions if item["framework_code"] == "sox")
    assert sox["applicable"] is False

    listed = evaluate_profile({"listed_company": True})
    sox_listed = next(item for item in listed if item["framework_code"] == "sox")
    assert sox_listed["applicable"] is True


def test_or_aggregation_keeps_matching_rule():
    decisions = evaluate_profile({
        "criticality": "low",
        "hosting": "cloud",
    })
    iso27005 = next(item for item in decisions if item["framework_code"] == "iso27005")
    assert iso27005["applicable"] is True
    assert iso27005["source_rule"] == "ISO27005_CLOUD"
