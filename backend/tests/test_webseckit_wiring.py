from app.core.permissions import assert_same_organization, roles_for_user
from security.authorization.rbac import has_permission, require_permission
from security.uploads.file_upload import validate_upload


class _User:
    def __init__(self, *, admin=False, org=None):
        self.is_platform_admin = admin
        self.organization_id = org
        self.id = "user-1"


def test_validate_upload_accepts_pdf():
    payload = b"%PDF-1.4 minimal"
    result = validate_upload(payload, "kbis.pdf", "application/pdf")
    assert result["ok"] is True
    assert result["extension"] == ".pdf"


def test_validate_upload_accepts_csv():
    payload = b"nom;siren\nACME;123456789\n"
    result = validate_upload(payload, "comptes.csv", "text/csv")
    assert result["ok"] is True
    assert result["mime"] == "text/csv"


def test_validate_upload_rejects_traversal_and_fake_pdf():
    # Le basename est extrait : "../evil.pdf" → "evil.pdf" (path traversal neutralisé)
    assert validate_upload(b"%PDF-1.4", "../evil.pdf")["ok"] is True
    assert validate_upload(b"%PDF-1.4", "/tmp/evil.pdf")["ok"] is True
    assert validate_upload(b"not a pdf", "doc.pdf")["ok"] is False
    assert validate_upload(b"%PDF-1.4", "doc.exe")["ok"] is False
    assert validate_upload(b"%PDF-1.4", "doc.pdf\x00.exe")["ok"] is False


def test_rbac_roles_and_upload_permission():
    assert has_permission(["user"], "files:upload") is True
    assert has_permission(["guest"], "files:upload") is False
    require_permission(["admin"], "admin:access")
    assert roles_for_user(_User(admin=True)) == ["admin"]
    assert roles_for_user(_User(admin=False)) == ["user"]


def test_assert_same_organization_uses_ownership_bridge():
    import uuid
    org = uuid.uuid4()
    user = _User(org=org)
    assert_same_organization(user, org)
