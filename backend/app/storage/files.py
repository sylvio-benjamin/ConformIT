"""Façade unique de stockage. Upload / download / delete passent uniquement par le backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.storage.backends import LocalBackend, MemoryBackend, S3Backend
from app.storage.keys import (
    NAMESPACES,
    PathTraversalError,
    candidate_keys,
    object_key,
    safe_filename,
    validate_object_key,
)


class StorageFacade:
    def __init__(self, backend, cache_root: Optional[Path] = None) -> None:
        self.backend = backend
        self._cache_root = Path(cache_root).resolve() if cache_root is not None else None

    def cache_root(self) -> Path:
        if self._cache_root is not None:
            return self._cache_root
        from app.config import STORAGE_CACHE, STORAGE_ROOT

        raw = STORAGE_CACHE or str(Path(STORAGE_ROOT) / ".cache")
        return Path(raw).resolve()

    def _cache_path(self, key: str) -> Path:
        parts = validate_object_key(key)
        root = self.cache_root()
        target = root.joinpath(*parts).resolve()
        if target != root and root not in target.parents:
            raise PathTraversalError("cache hors racine")
        return target

    def _local_file(self, key: str) -> Path:
        if isinstance(self.backend, LocalBackend):
            return self.backend.local_path(key)
        return self._cache_path(key)

    def resolve_key(self, namespace: str, name: str, organization_id: Optional[str] = None) -> Optional[str]:
        for key in candidate_keys(namespace, name, organization_id):
            if self.backend.exists(key):
                return key
        return None

    def write_bytes(
        self,
        namespace: str,
        name: str,
        data: bytes,
        organization_id: Optional[str] = None,
    ) -> str:
        key = object_key(namespace, name, organization_id)
        self.backend.put(key, data)
        if not isinstance(self.backend, LocalBackend):
            cache = self._cache_path(key)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(data)
        return key

    def get_bytes(self, namespace: str, name: str, organization_id: Optional[str] = None) -> bytes:
        key = self.resolve_key(namespace, name, organization_id)
        if not key:
            raise FileNotFoundError(f"{namespace}/{name}")
        return self.backend.get(key)

    def write_json(
        self,
        namespace: str,
        name: str,
        payload: Any,
        organization_id: Optional[str] = None,
    ) -> str:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        return self.write_bytes(namespace, name, text.encode("utf-8"), organization_id=organization_id)

    def read_json(self, namespace: str, name: str, organization_id: Optional[str] = None) -> Optional[Any]:
        if not self.exists(namespace, name, organization_id=organization_id):
            return None
        return json.loads(self.get_bytes(namespace, name, organization_id=organization_id).decode("utf-8"))

    def exists(self, namespace: str, name: str, organization_id: Optional[str] = None) -> bool:
        return self.resolve_key(namespace, name, organization_id) is not None

    def delete_file(self, namespace: str, name: str, organization_id: Optional[str] = None) -> bool:
        deleted = False
        for key in candidate_keys(namespace, name, organization_id):
            if self.backend.delete(key):
                deleted = True
            cache = self._cache_path(key)
            if cache.is_file():
                cache.unlink()
        return deleted

    def list_namespace(self, namespace: str, organization_id: Optional[str] = None) -> list[str]:
        if namespace not in NAMESPACES:
            raise PathTraversalError(f"namespace inconnu: {namespace}")
        org_key = object_key(namespace, "placeholder", organization_id) if organization_id else f"{namespace}/"
        prefix = org_key.rsplit("/", 1)[0] + "/" if organization_id else f"{namespace}/"
        names = [key.rsplit("/", 1)[-1] for key in self.backend.list_prefix(prefix)]
        return sorted(set(names))

    def file_path(self, namespace: str, name: str, organization_id: Optional[str] = None) -> Path:
        """Chemin local pour l’analyseur / ReportLab / FileResponse. Jamais une URL S3."""
        preferred = object_key(namespace, name, organization_id)
        resolved = self.resolve_key(namespace, name, organization_id)
        key = resolved or preferred
        path = self._local_file(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if resolved and not path.is_file():
            path.write_bytes(self.backend.get(resolved))
        return path

    def commit(self, namespace: str, name: str, organization_id: Optional[str] = None) -> str:
        """Après écriture locale (PDF/Excel), pousse l’objet vers le backend distant."""
        preferred = object_key(namespace, name, organization_id)
        path = self._local_file(preferred)
        if not path.is_file():
            resolved = self.resolve_key(namespace, name, organization_id)
            if not resolved:
                raise FileNotFoundError(f"{namespace}/{name}")
            path = self._local_file(resolved)
            preferred = resolved
        if not path.is_file():
            raise FileNotFoundError(f"{namespace}/{name}")
        self.backend.put(preferred, path.read_bytes())
        return preferred


def build_backend():
    from app.config import (
        S3_ACCESS_KEY,
        S3_BUCKET,
        S3_ENDPOINT,
        S3_PREFIX,
        S3_REGION,
        S3_SECRET_KEY,
        STORAGE_BACKEND,
    )

    name = (STORAGE_BACKEND or "local").strip().lower()
    if name in {"local", ""}:
        return LocalBackend()
    if name == "memory":
        return MemoryBackend()
    if name in {"s3", "r2"}:
        return S3Backend(
            bucket=S3_BUCKET,
            prefix=S3_PREFIX,
            endpoint=S3_ENDPOINT or None,
            region=S3_REGION,
            access_key=S3_ACCESS_KEY or None,
            secret_key=S3_SECRET_KEY or None,
        )
    raise RuntimeError(f"STORAGE_BACKEND inconnu: {name}")


_facade: Optional[StorageFacade] = None


def get_facade() -> StorageFacade:
    global _facade
    if _facade is None:
        _facade = StorageFacade(build_backend())
    return _facade


def reset_facade() -> None:
    global _facade
    _facade = None


def set_facade(facade: StorageFacade) -> None:
    global _facade
    _facade = facade


def write_bytes(namespace: str, name: str, data: bytes, organization_id: Optional[str] = None) -> str:
    return get_facade().write_bytes(namespace, name, data, organization_id=organization_id)


def get_bytes(namespace: str, name: str, organization_id: Optional[str] = None) -> bytes:
    return get_facade().get_bytes(namespace, name, organization_id=organization_id)


def write_json(namespace: str, name: str, payload: Any, organization_id: Optional[str] = None) -> str:
    return get_facade().write_json(namespace, name, payload, organization_id=organization_id)


def read_json(namespace: str, name: str, organization_id: Optional[str] = None) -> Optional[Any]:
    return get_facade().read_json(namespace, name, organization_id=organization_id)


def exists(namespace: str, name: str, organization_id: Optional[str] = None) -> bool:
    return get_facade().exists(namespace, name, organization_id=organization_id)


def delete_file(namespace: str, name: str, organization_id: Optional[str] = None) -> bool:
    return get_facade().delete_file(namespace, name, organization_id=organization_id)


def list_namespace(namespace: str, organization_id: Optional[str] = None) -> list[str]:
    return get_facade().list_namespace(namespace, organization_id=organization_id)


def file_path(namespace: str, name: str, organization_id: Optional[str] = None) -> Path:
    return get_facade().file_path(namespace, name, organization_id=organization_id)


def commit(namespace: str, name: str, organization_id: Optional[str] = None) -> str:
    return get_facade().commit(namespace, name, organization_id=organization_id)
