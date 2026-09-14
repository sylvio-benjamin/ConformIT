"""Backends de stockage. L’application ne parle qu’à la façade `app.storage`."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Protocol

from app.storage.keys import PathTraversalError, validate_object_key


class StorageBackend(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def list_prefix(self, prefix: str) -> list[str]: ...


def _join_under_root(root: Path, key: str) -> Path:
    parts = validate_object_key(key)
    target = root.joinpath(*parts).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise PathTraversalError("chemin hors racine")
    return target


class LocalBackend:
    """Disque partagé uniquement si toutes les instances voient le même `STORAGE_ROOT`."""

    is_local = True

    def __init__(self, root: Optional[Path] = None) -> None:
        self._root = Path(root).resolve() if root is not None else None

    def root(self) -> Path:
        if self._root is not None:
            return self._root
        from app.config import STORAGE_ROOT

        return Path(STORAGE_ROOT).resolve()

    def local_path(self, key: str) -> Path:
        return _join_under_root(self.root(), key)

    def put(self, key: str, data: bytes) -> None:
        path = self.local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        path = self.local_path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self.local_path(key).is_file()

    def delete(self, key: str) -> bool:
        path = self.local_path(key)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def list_prefix(self, prefix: str) -> list[str]:
        root = self.root()
        if prefix:
            base = _join_under_root(root, prefix.rstrip("/"))
        else:
            base = root
        if not base.exists():
            return []
        keys: list[str] = []
        for item in base.rglob("*"):
            if not item.is_file():
                continue
            rel = item.resolve().relative_to(root)
            keys.append(rel.as_posix())
        return sorted(keys)


class MemoryBackend:
    """Store partagé en mémoire — deux « instances » = deux façades, un seul dict."""

    is_local = False

    def __init__(self, store: Optional[Dict[str, bytes]] = None) -> None:
        self.store = store if store is not None else {}

    def put(self, key: str, data: bytes) -> None:
        validate_object_key(key)
        self.store[key] = data

    def get(self, key: str) -> bytes:
        validate_object_key(key)
        if key not in self.store:
            raise FileNotFoundError(key)
        return self.store[key]

    def exists(self, key: str) -> bool:
        validate_object_key(key)
        return key in self.store

    def delete(self, key: str) -> bool:
        validate_object_key(key)
        if key not in self.store:
            return False
        del self.store[key]
        return True

    def list_prefix(self, prefix: str) -> list[str]:
        return sorted(key for key in self.store if key.startswith(prefix))


class FakeS3Error(Exception):
    def __init__(self, code: str = "404") -> None:
        self.response = {"Error": {"Code": code}}
        super().__init__(code)


class FakeS3Client:
    """Client S3-compatible en mémoire pour les tests (pas AWS)."""

    def __init__(self, store: Optional[Dict[tuple, bytes]] = None) -> None:
        self.store = store if store is not None else {}

    def put_object(self, *, Bucket: str, Key: str, Body) -> dict:
        data = Body.read() if hasattr(Body, "read") else Body
        self.store[(Bucket, Key)] = data
        return {}

    def get_object(self, *, Bucket: str, Key: str) -> dict:
        if (Bucket, Key) not in self.store:
            raise FakeS3Error("NoSuchKey")
        return {"Body": _BytesBody(self.store[(Bucket, Key)])}

    def head_object(self, *, Bucket: str, Key: str) -> dict:
        if (Bucket, Key) not in self.store:
            raise FakeS3Error("404")
        return {}

    def delete_object(self, *, Bucket: str, Key: str) -> dict:
        self.store.pop((Bucket, Key), None)
        return {}

    def list_objects_v2(self, *, Bucket: str, Prefix: str = "") -> dict:
        contents = [
            {"Key": key}
            for (bucket, key) in self.store
            if bucket == Bucket and key.startswith(Prefix)
        ]
        return {"Contents": contents, "KeyCount": len(contents)}


class _BytesBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


def _is_missing_s3(exc: Exception) -> bool:
    response = getattr(exc, "response", None) or {}
    code = str((response.get("Error") or {}).get("Code", ""))
    return code in {"404", "NoSuchKey", "NotFound", "404 Not Found"}


class S3Backend:
    """S3 / R2. boto3 chargé seulement à la première connexion réelle."""

    is_local = False

    def __init__(
        self,
        *,
        bucket: str,
        client=None,
        prefix: str = "",
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip().strip("/")
        self.endpoint = endpoint
        self.region = region or "us-east-1"
        self.access_key = access_key
        self.secret_key = secret_key
        self._client = client

    def _full_key(self, key: str) -> str:
        validate_object_key(key)
        if self.prefix:
            return f"{self.prefix}/{key}"
        return key

    def _client_or_create(self):
        if self._client is not None:
            return self._client
        import boto3

        kwargs = {"region_name": self.region}
        if self.endpoint:
            kwargs["endpoint_url"] = self.endpoint
        if self.access_key:
            kwargs["aws_access_key_id"] = self.access_key
            kwargs["aws_secret_access_key"] = self.secret_key
        self._client = boto3.client("s3", **kwargs)
        return self._client

    def put(self, key: str, data: bytes) -> None:
        self._client_or_create().put_object(Bucket=self.bucket, Key=self._full_key(key), Body=data)

    def get(self, key: str) -> bytes:
        try:
            obj = self._client_or_create().get_object(Bucket=self.bucket, Key=self._full_key(key))
        except Exception as exc:
            if _is_missing_s3(exc):
                raise FileNotFoundError(key) from exc
            raise
        body = obj["Body"]
        return body.read() if hasattr(body, "read") else body

    def exists(self, key: str) -> bool:
        try:
            self._client_or_create().head_object(Bucket=self.bucket, Key=self._full_key(key))
            return True
        except Exception as exc:
            if _is_missing_s3(exc):
                return False
            raise

    def delete(self, key: str) -> bool:
        if not self.exists(key):
            return False
        self._client_or_create().delete_object(Bucket=self.bucket, Key=self._full_key(key))
        return True

    def list_prefix(self, prefix: str) -> list[str]:
        full = self._full_key(prefix) if prefix else (self.prefix + "/" if self.prefix else "")
        response = self._client_or_create().list_objects_v2(Bucket=self.bucket, Prefix=full)
        keys: list[str] = []
        strip = f"{self.prefix}/" if self.prefix else ""
        for item in response.get("Contents") or []:
            raw = item.get("Key") or ""
            if strip and raw.startswith(strip):
                raw = raw[len(strip):]
            if raw:
                keys.append(raw)
        return sorted(keys)
