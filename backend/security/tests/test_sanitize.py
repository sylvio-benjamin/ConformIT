from security.validation.sanitize import escape_html, normalize_email


def test_escape_html() -> None:
    escaped = escape_html("<b>")
    assert "<" not in escaped
    assert "&lt;" in escaped


def test_normalize_email() -> None:
    assert normalize_email("  A@B.COM ") == "a@b.com"
