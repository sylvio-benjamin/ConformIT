# DATABASE_ARCHITECTURE — Neon PostgreSQL

**Moteur :** Neon PostgreSQL  
**Accès :** FastAPI → SQLAlchemy 2 uniquement. Jamais depuis le frontend.  
**URLs :** `DATABASE_URL` (pooler) + `DIRECT_DATABASE_URL` (Alembic / migrations).  
**Alembic :** `0001` → `0007_iso_catalog`. Sur Neon : `cd backend && .venv/bin/alembic upgrade head`. `0007` n’est pas un feu vert Go-Live.

---

## Principes

1. **Multi-tenant :** toute donnée métier a un `organization_id` (sauf Knowledge Base globale).
2. **Identité serveur :** l’utilisateur vient du JWT, jamais d’un id client.
3. **Knowledge Base globale :** frameworks / exigences / contrôles catalogue **sans** `organization_id`.
4. **Fichiers :** métadonnées en SQL, binaires via `app.storage` (**local en dev**, **Cloudflare R2 en go-live**). Clés `{namespace}/{organization_id}/{fichier}`.
5. **Pas de texte ISO protégé en intégral** — identifiants, titres, mappings, extraits licenciés uniquement.
6. Toute table : PK, `created_at`, FK, index sur `organization_id` / `user_id` / `status` quand pertinent.

---

## Ce qui existe déjà (à conserver et étendre)

| Table | Rôle | Action |
|-------|------|--------|
| `organizations` | Tenant | Étendre (profil, pays, criticité) |
| `users` | Compte | `password_hash`, `is_platform_admin`, `email_verified` ; plus de `firebase_uid` |
| `roles`, `permissions`, `role_permissions` | RBAC | Remplir seed ; plus tard `user_roles` + `organization_members` |
| `analyses`, `companies`, `documents`, `counters` | Pipeline actuel | Garder ; documents gagneront `storage_key` |
| `risks`, `risk_categories`, `risk_assessments`, `risk_scores` | Registre | Brancher l’UI |
| `controls`, `action_plans` | GRC | Brancher l’UI |
| `incidents`, `kris` | GRC | Brancher l’UI |
| `compliance_frameworks`, `compliance_requirements`, `compliance_assessments`, `compliance_gaps` | Conformité | Distinguer KB globale vs décisions orga |
| `quotas`, `api_keys`, `collaborators` | Billing / équipe | Auth via session, plus via UID Firebase |
| `reports`, `audit_logs` | Reporting / trace | Protéger les exports |

---

## Nouvelles tables P0 (identité)

### `auth_sessions`

| Colonne | Type | Notes |
|---------|------|--------|
| id | UUID PK | |
| user_id | UUID FK users | index |
| jti | VARCHAR unique | id du JWT |
| expires_at | TIMESTAMPTZ | |
| revoked_at | TIMESTAMPTZ nullable | logout |
| user_agent | TEXT | |
| ip_address | VARCHAR(64) | |
| created_at | TIMESTAMPTZ | |

### `password_reset_tokens`

| Colonne | Type | Notes |
|---------|------|--------|
| id | UUID PK | |
| user_id | UUID FK | |
| token_hash | VARCHAR unique | |
| expires_at | TIMESTAMPTZ | |
| used_at | TIMESTAMPTZ nullable | |
| created_at | TIMESTAMPTZ | |

### Évolution `users`

| Colonne | Changement |
|---------|------------|
| firebase_uid | **supprimée** (P8 / Alembic `0006`) |
| password_hash | VARCHAR nullable (comptes migrés sans mdp) |
| is_platform_admin | BOOLEAN default false |
| email_verified | BOOLEAN default false |

---

## Tables cibles (P3–P7, à créer progressivement)

Ne pas tout créer d’un coup. Ordre :

### P3 — Organization + Applicability

Livré : `organization_profiles`, `applicability_rules` (globales), `applicability_decisions`, `kb_controls`.  
Catalogue ISO Niveau A : `iso_deliverables` (Alembic `0007`, **sans** `organization_id`, **sans** texte de norme).  
Plus tard : `organization_members`, activités / systèmes / contextes.

### P3/P5 — Knowledge Base (globale)

- `frameworks`, `standards`, `standard_versions`
- `requirements`, `controls` (catalogue — distinct des `controls` orga existants : à renommer plus tard `org_controls` vs `kb_controls`)
- `control_mappings`, `requirement_mappings`

**Collision de nom :** `controls` existe déjà comme contrôles *d’organisation*. Décision : garder `controls` pour l’orga ; catalogue KB = `kb_controls`.

### P4 — Documents (métadonnées, pas de versions)

Livré sur `documents` : `storage_key`, `original_filename`, `mime_type`, `byte_size`.  
Plus tard : `document_versions`, extractions, entités, preuves.

### P4 — Analysis jobs

Livré : `analysis_jobs` (cycle queued/running/completed/failed/cancelled), `analysis_findings` (questions/réponses déjà calculées par `/analyser/`).  
Le pipeline d’analyse n’est pas réécrit. Un échec de journalisation n’interrompt pas l’analyse.  
`/analyser/` synchrone crée le job directement en `running`.  
Plus tard : `analysis_results` / files d’attente async.

Le modèle `analyses` reste la façade MVP.

### P5 — Preuves + traitements

Livré : `compliance_evidence` (propositions depuis findings medium+, revue accepted/rejected), `risk_treatments` (mitigate/accept/transfer/avoid).  
Pas de nouvelle table `actions` : `action_plans` / `corrective_actions` restent.  
Plus tard : mapping exigence KB, billing.

### P6 — Audits structurés

Livré : `audits` (campagnes interne/externe/auto-éval), `audit_findings`.  
Distinct de `audit_logs` (trace) et `compliance_audits` (blob hérité, conservé).  
Import des preuves `accepted` → findings.  
KRIs : `kris` + `kri_metrics` suffisent (pas de `kri_definitions` séparées).

### P7 — Billing (conservé, hors métier)

Stripe, `plan_service`, `quotas`, pages `/abonnement` et profil : **conservés**.  
`BILLING_ENABLED=false` : pas de quota sur `/analyser/`, pas de gate PDF/Excel.  
Réactiver plus tard : `BILLING_ENABLED=true`. Pas de nouvelles tables billing.

---

## Isolation (anti-IDOR)

Toute requête métier :

```
current_user = get_current_user(session)
assert resource.organization_id == current_user.organization_id
  or current_user.is_platform_admin
```

Interdit : `?firebase_uid=`, `?user_id=` comme source d’identité, `organization_id` client sans `require_organization_access`.

---

## Neon / SQLAlchemy

```
DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require
DIRECT_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require
```

- Pooler pour l’app (`pool_pre_ping=True`).
- URL directe pour Alembic.
- Jamais d’URL en dur dans le code.

Alembic : obligatoire pour **toute nouvelle table**. Head actuelle : `0005_audits`. Les ALTER hérités restent dans `init_db()` pour les colonnes du schéma pré-Alembic.

---

## Index minimaux

- `users(email)`, `users(organization_id)`
- `auth_sessions(user_id)`, `auth_sessions(jti)`
- `analyses(organization_id, created_at)`, `analyses(slug)`, `analyses(employee_id)`
- `documents(organization_id)`, `risks(organization_id, status)`
- `analysis_jobs(organization_id, status, slug, user_id)`
- `analysis_findings(job_id, organization_id)`
- Toutes les tables GRC : `(organization_id)`
