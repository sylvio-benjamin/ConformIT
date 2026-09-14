import pytest

from security.injection.path_safety import assert_safe_relative_path


def test_path_traversal_rejected() -> None:
    with pytest.raises(ValueError):
        assert_safe_relative_path("../etc/passwd")
    assert assert_safe_relative_path("docs/a.txt") == "docs/a.txt"
