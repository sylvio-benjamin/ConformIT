#!/usr/bin/env python3
"""
Import du catalogue ISO Open Data (métadonnées uniquement).

Ne télécharge jamais de PDF. Dry-run par défaut. Ne pas --apply en production
sans validation préalable (fixture puis staging).

Usage :
  python scripts/import_iso_catalog.py --source backend/tests/fixtures/iso_deliverables_sample.csv
  python scripts/import_iso_catalog.py --official --limit 20
  python scripts/import_iso_catalog.py --source fichier.csv --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def _read_source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def _download_official() -> str:
    import requests
    from app.services.iso_catalog import OFFICIAL_CSV

    response = requests.get(OFFICIAL_CSV, timeout=120)
    response.raise_for_status()
    return response.text


def main() -> int:
    parser = argparse.ArgumentParser(description="Importer le catalogue ISO (métadonnées ODC-By).")
    parser.add_argument("--source", default="", help="CSV officiel local (recommandé)")
    parser.add_argument(
        "--official",
        action="store_true",
        help="Télécharger le CSV officiel (~60 Mo). Pas de PDF.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limiter le nombre de lignes après parse")
    parser.add_argument("--apply", action="store_true", help="Écrire en base (sinon dry-run)")
    args = parser.parse_args()

    from app.services.iso_catalog import (
        LICENSE,
        OFFICIAL_PORTAL,
        catalog_stats,
        parse_official_csv,
        persist_records,
        upsert_records,
    )

    if args.official:
        print(f"Téléchargement CSV officiel (pas de PDF) : {OFFICIAL_PORTAL}")
        raw = _download_official()
    elif args.source:
        raw = _read_source(args.source)
    else:
        print("Fournir --source <csv> ou --official. Dry-run par défaut. Aucun PDF.")
        return 2

    records, errors = parse_official_csv(raw)
    if args.limit:
        records = records[: args.limit]

    store: dict = {}
    inserted, updated = upsert_records(store, records)
    stats = catalog_stats(store)

    print(f"Licence : {LICENSE}")
    print(f"Source : {OFFICIAL_PORTAL}")
    print(f"Lignes valides : {len(records)}")
    print(f"Erreurs : {len(errors)}")
    for err in errors[:20]:
        print(f"  {err}")
    if len(errors) > 20:
        print(f"  … {len(errors) - 20} autres")
    print(f"Mémoire upsert insert={inserted} update={updated} total={stats['total']} withdrawn={stats['withdrawn']}")

    if not args.apply:
        print("Dry-run. Relancer avec --apply uniquement après validation (jamais en prod à l'aveugle).")
        return 1 if errors and not records else 0

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        db_inserted, db_updated = persist_records(session, store.values())
        print(f"Base upsert insert={db_inserted} update={db_updated}")
    finally:
        session.close()
    return 1 if errors and not records else 0


if __name__ == "__main__":
    raise SystemExit(main())
