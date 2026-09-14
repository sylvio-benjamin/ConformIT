from pathlib import Path

import pytest

from app.storage import PathTraversalError, exists, file_path, safe_filename, write_bytes


def test_safe_filename_rejects_traversal():
    with pytest.raises(PathTraversalError):
        safe_filename("../secret")
    with pytest.raises(PathTraversalError):
        safe_filename("a/b")
    with pytest.raises(PathTraversalError):
        safe_filename("/etc/passwd")
    assert safe_filename("acme-sa.json") == "acme-sa.json"


def test_file_path_stays_in_namespace(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.STORAGE_ROOT", str(tmp_path))
    target = file_path("audits", "ok.json")
    assert tmp_path.resolve() in target.resolve().parents
    with pytest.raises(PathTraversalError):
        file_path("audits", "..")


def test_write_and_exists(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.STORAGE_ROOT", str(tmp_path))
    key = write_bytes("uploads", "doc.pdf", b"%PDF")
    assert key == "uploads/doc.pdf"
    assert exists("uploads", "doc.pdf")
    assert Path(file_path("uploads", "doc.pdf")).read_bytes() == b"%PDF"
