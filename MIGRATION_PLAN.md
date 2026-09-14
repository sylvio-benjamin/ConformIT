# MIGRATION_PLAN — Firebase → Neon PostgreSQL

**Objectif :** Neon PostgreSQL = unique source de vérité. Firebase retiré du runtime.  
**Règle :** ne jamais créer une nouvelle architecture hybride durable.

---

## Phases

| Phase | Contenu | Statut |
|-------|---------|--------|
| 1 | Cartographie Firebase (ce document + audit) | [FAIT] |
| 2 | Modèle Postgres / Neon (`DATABASE_ARCHITECTURE.md`) | [FAIT] |
| 3 | Script `scripts/migrate_firebase.py` + export RTDB | [FAIT] script (apply users + GRC) |
| 4 | Backend : JWT, isolation orga, plus de `firebase_uid` query | [FAIT] |
| 5 | Frontend : plus d’accès RTDB / Auth Firebase | [FAIT] |
| 6 | Auth 100 % FastAPI | [FAIT] |
| 7 | Suppression SDK, Admin, `firebase_key.json` | [FAIT] runtime |
| P7 | Durcissement : jobs SQL, webhook secretisé, plus de clé maître, IDOR Neon | [FAIT] code |
| P8 | Retirer `firebase_uid` + chemins de compatibilité | [FAIT] |
| P9 | Durcissement production (CORS, secrets, rate limit, health, Stripe) | [FAIT] code |
| P10 | Object storage derrière `app.storage` | [FAIT] code |
| Go-live | Checklist infra R2 + GCP (voir PROJECT_AUDIT §8) | [À FAIRE] ops — **aucun lot applicatif** |

Priorité produit : **P0 sécurité → P1 source unique → P2 data → P3…P7 métier**.  
Ne pas reconstruire l’UI (section 18 de la mission) avant P3.

---

## Matrice Firebase → PostgreSQL

| Firebase | Table cible | Migration data | Code à modifier | Statut |
|----------|-------------|----------------|-----------------|--------|
| Auth (email/mdp) | `users.password_hash` + `auth_sessions` | **Impossible** (hash Firebase non exportable). Reset mot de passe. | LoginForm, inscription, useAuth, AuthProvider, LogoutButton, mdp-oublie | [EN COURS] |
| `utilisateurs/{uid}` | `users` + `organizations` | Script : email, nom, abonnement, téléphone. `admin` → `is_platform_admin` | useAuth, parametres, inscription, admin/* | [À MIGRER] |
| `utilisateurs.admin` | `users.is_platform_admin` (serveur seul) | Mapper booléen | admin/ajouter (ne plus écrire le rôle côté client) | [À MIGRER] |
| `utilisateurs.preferences` | `users.preferences` JSONB | Copier JSON | parametres | [À MIGRER] |
| `analyses` | `analyses` | Déjà écrites par `/analyser/` ; fusionner orphelins RTDB | resultat-analyse, entreprise-graph | [À MIGRER] |
| `entreprises/{slug}` | `companies` | Script par slug | tableau-et-graph, GraphiqueNiveauxRisque | [À MIGRER] |
| `documents/{id}` | `documents` | Script | resultat-analyse | [À MIGRER] |
| `compteurs/analyse_{uid}` | `counters` | Recalculer max(`analysis_number`) | — | [À MIGRER] |
| `collaborateurs/{uid}` | `collaborators` / `organization_members` | Script | profile | [À MIGRER] |
| `grc/{uid}/risks` | `risks` | Mapper `name`→`title`, `severity`→`priority` | grc/risks | [À MIGRER] |
| `grc/{uid}/controls` | `controls` | Mapper champs UI → SQL | grc/controls | [À MIGRER] |
| `grc/{uid}/kris` | `kris` | Mapper | grc/kris | [À MIGRER] |
| `grc/{uid}/incidents` | `incidents` | Mapper | grc/incidents | [À MIGRER] |
| `grc/{uid}/compliance` | `compliance_assessments` | Partiel | grc/compliance | [À MIGRER] |
| `grc/{uid}/reports` | `reports` | Partiel | grc/reports | [À MIGRER] |
| `grc/{uid}/stats` | vues / agrégats | Recalculer, ne pas migrer | grc/page | [À MIGRER] |
| `?firebase_uid=` | session JWT | — | api.js, analyses.py, users.py, compliance, integrations | [FAIT] |
| `firebase_key.json` | — | Révoquer dans GCP | main.py init | [FAIT] fichier ; révocation GCP manuelle |
| `src/services/firebase.js` | — | — | tous les imports | [FAIT] |
| `src/app/firebase/firebase.js` | — | doublon | supprimer | [FAIT] |
| `firebase-admin` | — | — | requirements.txt, user_routes | [FAIT] (jamais dans requirements actuel) |

---

## Script de migration

Fichier : `scripts/migrate_firebase.py`

1. Lire `analysesae-default-rtdb-export.json` (ou dump frais).
2. Créer `organizations` + `users` (sans mot de passe).
3. Importer analyses / companies / documents / GRC avec mapping.
4. Journaliser les erreurs dans `scripts/migration_log.json`.
5. `--dry-run` par défaut. `--apply` pour écrire.
6. `--verify` compare comptes (emails RTDB vs `users.email`).

**Incohérence connue :** un utilisateur Auth Firebase sans nœud RTDB, ou l’inverse. Documenter dans le log, ne pas inventer d’email.

---

## Ordre d’exécution (ne pas inverser)

1. Secrets hors git + rotation manuelle (humain).
2. Auth FastAPI + cookie httpOnly.
3. Endpoints dérivent l’identité du token.
4. Frontend login/register/me/logout.
5. Couper les écritures RTDB (resultat-analyse, GRC, admin).
6. Migrer les données (`--dry-run` puis `--apply`).
7. Vérifier cohérence.
8. Retirer SDK Firebase.

---

## Critères de sortie (Phase 7)

- `rg firebase src backend/app` → 0 usage runtime
- Plus de `firebase_key.json`
- Plus de `NEXT_PUBLIC_*` secret
- Alembic : `0001` → `0006_drop_firebase_uid` (Firebase) ; head actuel `0007_iso_catalog` (catalogue ISO, hors P8)
- Tests auth + IDOR verts (CI mocks ; live : `IDOR_LIVE=1 pytest tests/test_idor_live.py`)
- `npm run build` OK
- Backend démarre sans Firebase

---

## P8 — Nettoyage migration

1. Grep global : consommateurs runtime étaient `PlanService._find_user`, `init_db`, `User.firebase_uid`, `auth.register`.
2. `PlanService` résout uniquement `users.id` (UUID). Plus de chemin Firebase.
3. `scripts/migrate_firebase.py` reste un import one-shot : users/GRC par **email** (carte uid→email de l’export), plus d’écriture de colonne.
4. Alembic `0006_drop_firebase_uid` (idempotent).
5. `init_db()` ne recrée plus la colonne.

### Script `scripts/migrate_firebase.py` — archivé, pas runtime

Hors FastAPI / Next.js. Conservé pour une dernière import/restauration.  
Résolution par email uniquement. Ne pas le supprimer automatiquement.

**Supprimer seulement quand :** comptes utiles en Neon + plus de restore RTDB + dumps hors git.  
Puis retirer le script, `tests/test_migrate_planners.py`, et les mentions associées.

**Pas de P9 Firebase.** Suite = durcissement production, pas les traces Firebase.

## P10 — Object storage

1. `app.storage` reste la seule API métier (namespaces `uploads` / `audits` / `pdfs` / `excels`).
2. Backend `local` (défaut **dev**) ; **R2 = cible go-live** (`STORAGE_BACKEND=r2`, variables `S3_*`). Les clés objet ne sortent pas du backend (`job_to_dict` n’expose pas `storage_key`).
3. Préfixe `{namespace}/{organization_id}/` pour les nouveaux fichiers ; lecture de secours de la clé plate héritée.
4. Analyseur / PDF / Excel / `FileResponse` passent par un chemin local matérialisé + `commit()` vers le bucket.
5. Migration : `python scripts/migrate_local_storage.py` (dry-run) puis `--apply`. **Ne supprime jamais** le disque local.
6. Valider avec deux instances sur le même bucket, puis un redémarrage, avant d’abandonner `STORAGE_ROOT`.
7. **Figé.** Pas de P11 automatique. Redis / observabilité / jobs distribués = post-MVP, non bloquants.

### Go-live R2 (ops, pas un lot code)

```env
STORAGE_BACKEND=r2
S3_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_BUCKET=docanalyse-prod
S3_REGION=auto
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

1. Bucket R2 **privé**.
2. Credentials dédiés ConformIT, permissions minimales.
3. `STORAGE_BACKEND=r2` (secrets via l’hébergeur).
4. `python scripts/migrate_local_storage.py` en dry-run.
5. Vérifier les namespaces : `uploads|audits|pdfs|excels/{org}/...`
6. `--apply` (le disque local n’est pas supprimé).
7. **instance A → `commit` → R2 → instance B → téléchargement sans cache A.**
8. Redémarrer les deux instances, retélécharger.
9. Isolation : org A ne lit jamais une clé de org B.
10. Seulement après : retrait progressif du disque local.

`FileResponse` sert le cache local de l’instance, pas une URL R2. FakeS3 couvre le principe ; le bucket R2 réel est la dernière validation P10.
