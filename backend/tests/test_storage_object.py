from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.runtime_config import validate_storage_config
from app.services.analysis_jobs import job_to_dict
from app.storage import StorageFacade, object_key, reset_facade, set_facade, write_bytes
from app.storage.backends import FakeS3Client, LocalBackend, MemoryBackend, S3Backend
from app.storage.migrate import apply_local_migration, destination_key, plan_local_migration


def test_object_key_scopes_organization():
    assert object_key("uploads", "doc.pdf") == "uploads/doc.pdf"
    assert object_key("uploads", "doc.pdf", "org-a") == "uploads/org-a/doc.pdf"
    with pytest.raises(Exception):
        object_key("uploads", "../x")


def test_org_isolation_same_filename():
    store = {}
    facade = StorageFacade(MemoryBackend(store))
    facade.write_bytes("uploads", "doc.pdf", b"A", organization_id="org-a")
    facade.write_bytes("uploads", "doc.pdf", b"B", organization_id="org-b")
    assert facade.get_bytes("uploads", "doc.pdf", organization_id="org-a") == b"A"
    assert facade.get_bytes("uploads", "doc.pdf", organization_id="org-b") == b"B"
    assert facade.exists("uploads", "doc.pdf", organization_id="org-c") is False
    assert "uploads/org-a/doc.pdf" in store
    assert "uploads/org-b/doc.pdf" in store


def test_legacy_unscoped_file_still_readable_by_org():
    facade = StorageFacade(MemoryBackend())
    facade.write_bytes("uploads", "old.pdf", b"legacy")
    assert facade.get_bytes("uploads", "old.pdf", organization_id="org-a") == b"legacy"


def test_two_instances_share_memory_store(tmp_path):
    store = {}
    inst_a = StorageFacade(MemoryBackend(store), cache_root=tmp_path / "a")
    inst_b = StorageFacade(MemoryBackend(store), cache_root=tmp_path / "b")
    key = inst_a.write_bytes("audits", "acme.json", b'{"ok":1}', organization_id="org-1")
    assert key == "audits/org-1/acme.json"
    assert inst_b.exists("audits", "acme.json", organization_id="org-1")
    assert inst_b.get_bytes("audits", "acme.json", organization_id="org-1") == b'{"ok":1}'
    path_b = inst_b.file_path("audits", "acme.json", organization_id="org-1")
    assert path_b.read_bytes() == b'{"ok":1}'
    assert (tmp_path / "a") != (tmp_path / "b")
    assert not list((tmp_path / "b").rglob("*")) or path_b.is_file()


def test_restart_empty_cache_reads_shared_store(tmp_path):
    store = {}
    first = StorageFacade(MemoryBackend(store), cache_root=tmp_path / "cache-1")
    first.write_bytes("pdfs", "report.pdf", b"%PDF-1", organization_id="org-1")
    restarted = StorageFacade(MemoryBackend(store), cache_root=tmp_path / "cache-2")
    assert restarted.exists("pdfs", "report.pdf", organization_id="org-1")
    assert restarted.get_bytes("pdfs", "report.pdf", organization_id="org-1") == b"%PDF-1"
    local = restarted.file_path("pdfs", "report.pdf", organization_id="org-1")
    assert local.read_bytes() == b"%PDF-1"


def test_local_restart_same_root(tmp_path):
    root = tmp_path / "data"
    first = LocalBackend(root)
    first.put("uploads/org-1/doc.pdf", b"keep")
    restarted = LocalBackend(root)
    assert restarted.exists("uploads/org-1/doc.pdf")
    assert restarted.get("uploads/org-1/doc.pdf") == b"keep"


def test_s3_fake_two_instances_and_commit(tmp_path):
    client = FakeS3Client()
    bucket = "docanalyse-test"
    inst_a = StorageFacade(S3Backend(bucket=bucket, client=client), cache_root=tmp_path / "s3-a")
    inst_b = StorageFacade(S3Backend(bucket=bucket, client=client), cache_root=tmp_path / "s3-b")
    inst_a.write_bytes("uploads", "x.pdf", b"hello", organization_id="org-1")
    assert inst_b.get_bytes("uploads", "x.pdf", organization_id="org-1") == b"hello"

    pdf_path = inst_a.file_path("pdfs", "out.pdf", organization_id="org-1")
    pdf_path.write_bytes(b"%PDF-out")
    committed = inst_a.commit("pdfs", "out.pdf", organization_id="org-1")
    assert committed == "pdfs/org-1/out.pdf"
    assert inst_b.exists("pdfs", "out.pdf", organization_id="org-1")
    assert inst_b.get_bytes("pdfs", "out.pdf", organization_id="org-1") == b"%PDF-out"


def test_s3_prefix_isolates_keys():
    store = {}
    client = FakeS3Client(store)
    backend = S3Backend(bucket="b", client=client, prefix="prod")
    backend.put("uploads/a.pdf", b"x")
    assert ("b", "prod/uploads/a.pdf") in store
    assert backend.get("uploads/a.pdf") == b"x"


def test_delete_only_touches_requested_org():
    facade = StorageFacade(MemoryBackend())
    facade.write_bytes("uploads", "doc.pdf", b"A", organization_id="org-a")
    facade.write_bytes("uploads", "doc.pdf", b"B", organization_id="org-b")
    assert facade.delete_file("uploads", "doc.pdf", organization_id="org-a")
    assert facade.exists("uploads", "doc.pdf", organization_id="org-b")
    assert not facade.exists("uploads", "doc.pdf", organization_id="org-a")


def test_job_to_dict_hides_storage_key():
    now = datetime.now(timezone.utc)
    payload = job_to_dict(SimpleNamespace(
        id=uuid4(),
        slug="acme",
        filename="acme.pdf",
        storage_key="uploads/org-a/acme.pdf",
        status="completed",
        error_message=None,
        result_summary={},
        analysis_id=None,
        started_at=now,
        finished_at=now,
        created_at=now,
    ))
    assert "storage_key" not in payload
    assert payload["filename"] == "acme.pdf"
    assert payload["slug"] == "acme"


def test_storage_config_s3_requires_secrets():
    validate_storage_config(storage_backend="local")
    with pytest.raises(RuntimeError, match="S3_BUCKET"):
        validate_storage_config(storage_backend="s3")
    with pytest.raises(RuntimeError, match="S3_ACCESS_KEY"):
        validate_storage_config(storage_backend="s3", s3_bucket="bucket")
    validate_storage_config(
        storage_backend="s3",
        s3_bucket="bucket",
        s3_access_key="ak",
        s3_secret_key="sk",
    )
    with pytest.raises(RuntimeError, match="S3_ENDPOINT"):
        validate_storage_config(
            storage_backend="r2",
            s3_bucket="docanalyse-prod",
            s3_access_key="ak",
            s3_secret_key="sk",
        )
    validate_storage_config(
        storage_backend="r2",
        s3_bucket="docanalyse-prod",
        s3_access_key="ak",
        s3_secret_key="sk",
        s3_endpoint="https://account.r2.cloudflarestorage.com",
    )


def test_migrate_plans_org_prefix_and_apply_keeps_source(tmp_path):
    source = tmp_path / "local"
    (source / "uploads").mkdir(parents=True)
    original = source / "uploads" / "legacy.pdf"
    original.write_bytes(b"keep-me")
    items = plan_local_migration(source, "org-a")
    assert len(items) == 1
    assert items[0].dest_key == "uploads/org-a/legacy.pdf"
    assert destination_key("uploads/org-a/already.pdf") == "uploads/org-a/already.pdf"

    backend = MemoryBackend()
    copied = apply_local_migration(items, backend)
    assert copied == ["uploads/org-a/legacy.pdf"]
    assert backend.get("uploads/org-a/legacy.pdf") == b"keep-me"
    assert original.is_file()
    assert original.read_bytes() == b"keep-me"


def test_module_facade_can_be_swapped(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.STORAGE_ROOT", str(tmp_path))
    reset_facade()
    set_facade(StorageFacade(MemoryBackend()))
    key = write_bytes("uploads", "z.pdf", b"zz", organization_id="org-z")
    assert key == "uploads/org-z/z.pdf"
