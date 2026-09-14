#!/usr/bin/env python3
"""
Copie les fichiers du disque local vers le backend objet (cible go-live : Cloudflare R2).

Ne supprime jamais les fichiers locaux. Dry-run par défaut.

Usage:
  python scripts/migrate_local_storage.py
  python scripts/migrate_local_storage.py --apply
  python scripts/migrate_local_storage.py --organization-id <uuid> --apply

Après validation (deux instances + redémarrage), on pourra retirer le disque local.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrer le stockage local vers le backend objet.")
    parser.add_argument("--source", default="", help="Racine locale (défaut: STORAGE_ROOT)")
    parser.add_argument("--organization-id", default="", help="Préfixe orga pour les fichiers plats hérités")
    parser.add_argument("--apply", action="store_true", help="Écrire dans le backend (sinon dry-run)")
    parser.add_argument("--overwrite", action="store_true", help="Écraser les objets déjà présents")
    args = parser.parse_args()

    from app.config import STORAGE_BACKEND, STORAGE_ROOT
    from app.storage.files import build_backend
    from app.storage.migrate import apply_local_migration, plan_local_migration

    source = Path(args.source or STORAGE_ROOT).resolve()
    org = args.organization_id.strip() or None
    items = plan_local_migration(source, org)

    print(f"Source : {source}")
    print(f"Backend : {STORAGE_BACKEND}")
    print(f"Fichiers : {len(items)}")
    for item in items:
        print(f"  {item.relative} → {item.dest_key}")

    if not args.apply:
        print("Dry-run. Relancer avec --apply pour copier. Les fichiers locaux ne sont pas supprimés.")
        return 0

    copied = apply_local_migration(items, build_backend(), overwrite=args.overwrite)
    print(f"Copiés : {len(copied)}. Disque local inchangé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
