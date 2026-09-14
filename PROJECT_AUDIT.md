# PROJECT_AUDIT — ConformIT (SAE 4.01)

**Date :** 13 septembre 2026 (dépôt fonctionnel gelé — phase infra uniquement)  
**Périmètre :** dépôt hors `.next/` et `node_modules/`  
**Verdict :** **MVP production-ready sur le plan applicatif.** Décision Go-Live actuelle : **NO-GO** tant que l’infra n’a pas de preuves.  
**« R2 READY dans le code » ≠ « R2 production PASS ».** **« Neon compatible » ≠ « Neon production démontré ».**

| Domaine | État |
|---------|------|
| Next.js / FastAPI / JWT | READY |
| Neon — intégration applicative | CODE READY |
| `app.storage` | R2 READY |
| R2 réel / Neon prod / hébergement / secrets / backup / CD | À provisionner — BLOCKED |
| Révocation clé Firebase/GCP | Action humaine |
| P0–P10 | **FROZEN** |

Phase : **Provisionner → Configurer → Déployer → Tester → Prouver → GO**. Pas de modification fonctionnelle du dépôt. Accès Cloudflare / Neon / GCP / hébergeur manquant = BLOCKED / ACTION HUMAINE, sans simulation.

**Aucun P11. Aucune réouverture P0–P10.** Redis, observabilité, jobs = post-MVP.

Inventaire runtime Firebase : [docs/architecture/FIREBASE_MIGRATION.md](./docs/architecture/FIREBASE_MIGRATION.md). Déploiement / R2 / Neon réels : `docs/architecture/DEPLOYMENT.md`, `STORAGE.md`, `DATABASE.md`.

---

## 1. Identité

| Champ | État |
|-------|------|
| Package | `sae_4.01` |
| UI | ConformIT |
| Type | SaaS scolaire : analyse de documents d’entreprise + GRC |
| Auth | FastAPI JWT, cookies `da_access` / `da_refresh` |
| Données | Neon PostgreSQL (source unique) |
| Alembic | `0007_iso_catalog` (head ; `0006` = drop Firebase ; `0007` = catalogue ISO métadonnées, pas un GO) |

**Chaîne visée :** Organisation → Contexte → Applicabilité → Référentiels → Documents → Analyse → Preuves → Conformité → Risques → Traitements → Audits → Reporting

**Ce qui tourne vraiment :** login JWT → profil orga → applicabilité → upload → `/analyser/` → job + findings → preuves proposées → traitements de risques → audits GRC → rapports. Billing / Stripe encore dans le repo, **sans effet** (`BILLING_ENABLED=false`).

---

## 2. Architecture actuelle

```
Navigateur (Next.js 16 / React 19)
    └─ cookies httpOnly (credentials: include)
         └─ FastAPI :8000
              ├─ get_current_user (JWT)
              ├─ isolation organization_id
              └─ Neon (SQLAlchemy + Alembic)
```

Plus de SDK Firebase dans `src/`. Plus de `firebase_key.json`. Identité = token, jamais `firebase_uid` query.

---

## 3. Lots livrés

| Lot | Contenu | Statut |
|-----|---------|--------|
| P0 | JWT, cookies, IDOR de base, secrets hors client | [FAIT] révocation GCP encore manuelle |
| P1 | Neon source unique runtime | [FAIT] |
| P2 | Script `migrate_firebase.py` (users + GRC) | [FAIT] |
| P3 | Profil orga, applicabilité, `kb_controls` | [FAIT] |
| P4 | `analysis_jobs` / findings, métadonnées documents | [FAIT] |
| P5 | `compliance_evidence`, `risk_treatments` | [FAIT] |
| P6 | `audits`, `audit_findings` | [FAIT] |
| P7 | Durcissement runtime (jobs SQL, webhook, IDOR, plus de clé maître) | [FAIT] code ; révocation GCP humaine |
| P8 | Drop `firebase_uid` + docs finales | [FAIT] |
| Billing | Stripe + quotas + `/abonnement` | Conservé, déconnecté |
| Firebase | Runtime + schéma | Décommissionnés |
| Sécurité externe | Clé Admin GCP | En attente (humain) |
| P9 | Production hardening | [FAIT] code |
| P10 | Object storage (S3/R2) | [FAIT] code-complete ; bucket réel = go-live |

---

## 4. Backend

- FastAPI + Uvicorn, SQLAlchemy 2, Alembic `0001`–`0006`
- Auth : `app/core/security.py`, `get_current_user`, `require_admin`, `assert_same_organization`
- Pipeline `/analyser/` inchangé (scores) ; journalisé par jobs best-effort
- GRC : risks, controls, incidents, kris, compliance, reports, evidence, treatments, audits
- Billing : `stripe_routes`, `plan_service`, `quotas` — no-op métier si `BILLING_ENABLED=false`
- `init_db()` n’altère plus le schéma ; Alembic seul (`0001`–`0006`)

---

## 5. Frontend

- Routes conservées : `/employe`, `/grc` (renommage section 18 plus tard)
- `authClient` + `credentials: 'include'`
- Plus de `firebase` npm
- Upload / exports : plus de gate quota / plan
- GRC : conformité (profil + preuves), risques (traitements), rapports (audits)

---

## 6. Sécurité — restes

| Sujet | Gravité | Action |
|-------|---------|--------|
| Ancienne clé Firebase Admin | Haute | Révoquer dans GCP (humain) puis auditer CI/hébergeurs |
| Export RTDB à la racine | PII | Ne pas committer |

---

## 7. Dette produit (pas bloquant)

- UI `/employe` `/grc` à renommer plus tard
- Suppression admin utilisateur : toast seulement
- `compliance_audits` hérités (blob) vs `audits` P6 : deux modèles
- Pas de texte ISO en base (volontaire)
- Fichiers : `app.storage` — **local en dev**, **R2 en production** ; ne pas supprimer le disque avant validation R2
- Billing non formalisé (volontaire)

---

## 8. Décision

P0–P10 **figés, code-complete**. **Aucun P11. Aucune réouverture de P9/P10.** La checklist ci-dessous est d’**exploitation Go-Live**, pas un backlog applicatif.

Le métier parle uniquement à `app.storage`. **Dev = `local` (défaut). Go-live = Cloudflare R2** (`STORAGE_BACKEND=r2`, variables `S3_*`).  
`FileResponse` sert un cache local (conforme) : en multi-instance réel, B doit pouvoir télécharger après le `commit` de A **sans** le disque de A. FakeS3 le couvre ; le bucket R2 réel est la dernière validation P10.

**Checklist Go-Live** (ops uniquement — aucune case n’ouvre un lot applicatif)

- [ ] Bucket R2 privé
- [ ] Credentials dédiés + permissions minimales
- [ ] Secrets injectés par le gestionnaire de secrets
- [ ] Dry-run migration
- [ ] Migration `--apply`
- [ ] A → R2 → B sans cache partagé
- [ ] Redémarrage + récupération
- [ ] Isolation organisationnelle réelle
- [ ] Backup/restauration vérifiés
- [ ] Retrait du disque local après validation
- [ ] Révocation clé Firebase Admin GCP
- [ ] Audit CI/CD + hébergeurs

**Durcissements post-MVP** (non bloquants, hors Go-Live) : rate limiting Redis, observabilité, jobs async distribués.

`scripts/migrate_firebase.py` reste un outil one-shot archivé. UI non réécrite.

---

## 9. Risques production (pas Firebase)

| Sujet | Gravité | Pourquoi |
|-------|---------|----------|
| CORS / JWT / ENCRYPTION hors dev | [FAIT] P9 | Fail-fast ; localhost seulement en development |
| Chemins fichiers | [FAIT] P9 | `app.storage` + anti-traversal |
| Stockage objet multi-instance | [FAIT] P10 code | Cible go-live = **R2** ; instance B sans cache de A |
| Rate limit login / analyse | [FAIT] P9 | Mémoire **par process** ; Redis = post-MVP, non bloquant |
| `init_db()` DDL | [FAIT] P9 | Alembic seul |
| `/health` PostgreSQL | [FAIT] P9 | `/health/live` vs `/health/ready` |
| Stripe si billing off | [FAIT] P9 | Routes non montées ; org JWT si réactivation |
