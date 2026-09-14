"""Clés objet et anti-traversal. Jamais d’URL signée ni de secret navigateur."""

from __future__ import annotations

from typing import Optional

NAMESPACES = frozenset({"uploads", "audits", "pdfs", "excels"})


class PathTraversalError(ValueError):
    pass


def safe_filename(name: str) -> str:
    if not name or name in {".", ".."}:
        raise PathTraversalError("nom de fichier vide")
    if name.startswith("/") or name.startswith("\\") or ":" in name[:2]:
        raise PathTraversalError("chemin absolu interdit")
    if any(sep in name for sep in ("/", "\\", "\x00")):
        raise PathTraversalError("séparateur interdit")
    if ".." in name:
        raise PathTraversalError("traversal interdit")
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in "._-")
    if not cleaned or cleaned in {".", ".."}:
        raise PathTraversalError("nom de fichier invalide")
    return cleaned


def safe_org_id(organization_id: Optional[str]) -> Optional[str]:
    if organization_id is None:
        return None
    value = str(organization_id).strip()
    if not value:
        return None
    return safe_filename(value)


def object_key(namespace: str, name: str, organization_id: Optional[str] = None) -> str:
    if namespace not in NAMESPACES:
        raise PathTraversalError(f"namespace inconnu: {namespace}")
    filename = safe_filename(name)
    org = safe_org_id(organization_id)
    if org:
        return f"{namespace}/{org}/{filename}"
    return f"{namespace}/{filename}"


def candidate_keys(namespace: str, name: str, organization_id: Optional[str] = None) -> list[str]:
    """Clé orga d’abord, puis clé plate héritée (fichiers pré-P10)."""
    keys: list[str] = []
    if safe_org_id(organization_id):
        keys.append(object_key(namespace, name, organization_id))
    keys.append(object_key(namespace, name, None))
    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def validate_object_key(key: str) -> list[str]:
    if not key or key.startswith("/") or "\\" in key or "\x00" in key:
        raise PathTraversalError("clé objet invalide")
    parts = [part for part in key.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise PathTraversalError("clé objet invalide")
    if parts[0] not in NAMESPACES:
        raise PathTraversalError(f"namespace inconnu: {parts[0]}")
    return [safe_filename(part) for part in parts]
