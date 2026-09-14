from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.rate_limit import SlidingWindowLimiter, enforce


def test_sliding_window_blocks_after_limit():
    limiter = SlidingWindowLimiter()
    assert limiter.allow("k", 2, 60) is True
    assert limiter.allow("k", 2, 60) is True
    assert limiter.allow("k", 2, 60) is False


def test_enforce_raises_429():
    enforce("unique-test-key", 1, 60, detail="stop")
    with pytest.raises(HTTPException) as exc:
        enforce("unique-test-key", 1, 60, detail="stop")
    assert exc.value.status_code == 429


def test_analyse_limit_keys_include_org():
    from app.core import rate_limit as module

    calls = []

    def _capture(key, limit, window, *, detail):
        calls.append(key)

    monkey_user = SimpleNamespace(id="u1", organization_id="o1")
    request = SimpleNamespace(headers={}, client=SimpleNamespace(host="1.2.3.4"))
    original = module.enforce
    module.enforce = _capture
    try:
        module.enforce_analyse(request, monkey_user)
    finally:
        module.enforce = original
    assert any(key.startswith("analyse:ip:") for key in calls)
    assert "analyse:user:u1" in calls
    assert "analyse:org:o1" in calls
