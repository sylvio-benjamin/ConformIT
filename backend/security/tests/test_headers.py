from security.headers.security_headers import security_header_map


def test_headers_contain_csp() -> None:
    headers = security_header_map(True)
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in headers
