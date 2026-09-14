"""Copie contrôlée local → backend objet. Ne supprime jamais les fichiers source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from app.storage.keys import NAMESPACES, PathTraversalError, object_key


@dataclass(frozen=True)
class MigrationItem:
    local_path: Path
    relative: str
    dest_key: str


def _is_cache_dir(path: Path, root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return rel.parts[:1] == (".cache",)


def destination_key(relative: str, organization_id: Optional[str] = None) -> str:
    parts = [part for part in Path(relative).as_posix().split("/") if part]
    if not parts or parts[0] not in NAMESPACES:
        raise PathTraversalError(f"chemin hors namespace: {relative}")
    namespace = parts[0]
    rest = parts[1:]
    if len(rest) >= 2:
        return object_key(namespace, rest[-1], rest[0])
    if len(rest) == 1:
        return object_key(namespace, rest[0], organization_id)
    raise PathTraversalError(f"fichier sans nom: {relative}")


def plan_local_migration(root: Path, organization_id: Optional[str] = None) -> list[MigrationItem]:
    root = Path(root).resolve()
    items: list[MigrationItem] = []
    if not root.exists():
        return items
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_cache_dir(path, root):
            continue
        relative = path.relative_to(root).as_posix()
        try:
            dest = destination_key(relative, organization_id)
        except PathTraversalError:
            continue
        items.append(MigrationItem(local_path=path, relative=relative, dest_key=dest))
    return items


def apply_local_migration(
    items: Iterable[MigrationItem],
    backend,
    *,
    overwrite: bool = False,
) -> list[str]:
    copied: list[str] = []
    for item in items:
        if backend.exists(item.dest_key) and not overwrite:
            continue
        backend.put(item.dest_key, item.local_path.read_bytes())
        copied.append(item.dest_key)
    return copied
