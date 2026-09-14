# ConformIT

Plateforme SaaS d’analyse documentaire et de GRC (gouvernance, risque, conformité).

**Stack :** Next.js 16 → FastAPI → SQLAlchemy 2 → Neon PostgreSQL.

Auth et données runtime : FastAPI + Neon. Firebase est hors runtime et hors schéma. L’état des analyses est dans `analysis_jobs`.  
**Baseline Go-Live figée :** P0–P10 code-complete. R2 = stockage prod. `app.storage` seule API métier. `local` en dev. Suite = validation infra réelle uniquement — pas de nouveau lot applicatif.  
Hors `ENV=development` : `JWT_SECRET`, `ENCRYPTION_KEY` et `CORS_ORIGINS` explicites (pas de localhost). Fichiers via `app.storage` : **`local` en dev**, **Cloudflare R2 en production** (`STORAGE_BACKEND=r2`). Alembic seul pour le schéma.  
`scripts/migrate_firebase.py` est un outil one-shot **archivé**.  
Migration fichiers : `python scripts/migrate_local_storage.py` (dry-run) puis `--apply` — ne supprime pas le disque local.

## Documentation

| Document | Contenu |
|----------|---------|
| [PROJECT_AUDIT.md](./PROJECT_AUDIT.md) | Architecture actuelle, dette, risques |
| [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) | Matrice Firebase → Postgres et phases |
| [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) | Modèle Neon cible |
| [SECURITY.md](./SECURITY.md) | Auth, IDOR, secrets |
| [DECISIONS.md](./DECISIONS.md) | Journal des choix techniques |
| [.env.example](./.env.example) | Variables (aucun secret) |

## Démarrage

```bash
cp .env.example .env.local
# renseigner DATABASE_URL (Neon) et JWT_SECRET
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
npm install
npm run dev
```

Frontend : http://localhost:3000 — API : http://localhost:8000

## Tests

```bash
cd backend && pytest tests/ -q
npm run lint
```

## Statut refonte

| Lot | Statut |
|-----|--------|
| P0 Sécurité (secrets, JWT, IDOR) | [FAIT] (rotation GCP encore manuelle) |
| P1 Neon source unique | [FAIT] runtime |
| P2 Migration données Firebase | [FAIT] script (`--apply` users + GRC) |
| P3 Organisation + applicabilité | [FAIT] profil + moteur + kb_controls |
| P4 Analysis jobs + métadonnées documents | [FAIT] Alembic `0003_analysis_jobs` |
| P5 Preuves + traitements de risques | [FAIT] Alembic `0004_evidence` |
| P6 Audits GRC structurés | [FAIT] Alembic `0005_audits` |
| P7 Billing | Conservé, déconnecté (`BILLING_ENABLED=false`) |
