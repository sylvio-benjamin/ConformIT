from pathlib import Path

from app.config import BILLING_ENABLED
from app.services.plan_service import PlanService


def test_billing_disabled_by_default():
    assert BILLING_ENABLED is False


def test_billing_does_not_gate_analysis_or_exports():
    assert PlanService.can_perform_analysis("anyone") == (True, None)
    assert PlanService.has_feature("anyone", "pdf") is True
    assert PlanService.has_feature("anyone", "excel") is True
    assert PlanService.increment_analysis_count("anyone") is True


def test_checkout_is_not_mounted_when_billing_disabled():
    assert BILLING_ENABLED is False
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert "if BILLING_ENABLED:" in source
    assert "app.include_router(stripe_router)" in source
