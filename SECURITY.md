# SECURITY — ConformIT

Les clés exposées dans l’ancien code sont **compromises**. Les faire tourner hors de Git (Firebase Admin, `API_KEY_ATTENDUE`, Stripe, Grok).

---

## P0 — à corriger / en cours

| Sujet | Risque | Action | Statut |
|-------|--------|--------|--------|
| `backend/app/firebase_key.json` | Admin SDK complet | Fichier retiré du repo ; **révoquer encore la clé dans GCP** | [FAIT] code ; [À FAIRE] révocation humaine |
| `NEXT_PUBLIC_API_KEY` + fallback client | Clé maître dans le JS | Auth session uniquement | [FAIT] |
| `?firebase_uid=` | IDOR | Identité = JWT | [FAIT] |
| Flag `admin` RTDB | Élévation | `is_platform_admin` serveur | [FAIT] |
| `/resultat/{slug}`, downloads, delete | Accès public | `get_current_user` + orga | [FAIT] |
| API GRC sans Depends | Dump cross-tenant | `require_organization_access` | [FAIT] |
| `/api-keys`, export user | Ouvert | Session + self-or-admin | [FAIT] |
| Règles RTDB absentes | Lecture/écriture globale | SDK retiré, plus d’accès RTDB | [FAIT] |
| Middleware cookie `role` | Cosmétique | No-op ; session API | [FAIT] |
| Export RTDB à la racine | PII | gitignore ; ne pas pousser | [À SUPPRIMER] du tracking |
| `GET /api/v1/analysis-jobs` | IDOR | Filtre `organization_id` (admin plateforme excepté) | [FAIT] |
| Preuves / traitements | IDOR | Même filtre orga + revue JWT | [FAIT] |
| `GET /api/v1/audits` | IDOR | Filtre `organization_id` | [FAIT] |
| Dicts process `analyses_owners` | Course multi-worker | Supprimés ; `analysis_jobs` seul | [FAIT] |
| Webhook Make.com en dur | Secret leak | `POST /api/v1/alerts/high-risk` + env | [FAIT] |
| `API_KEY_ATTENDUE` | Clé maître partagée | Retirée | [FAIT] |
| `users.firebase_uid` | Identité legacy | Colonne droppée (`0006`) ; lookup UUID seul | [FAIT] |
| CORS localhost en prod | Cookies volés | Localhost seulement si `ENV=development` | [FAIT] |
| JWT / ENCRYPTION_KEY défaut | Auth cassée | Obligatoires hors development | [FAIT] |
| Fichiers `./uploads` | Traversal / multi-instance | `app.storage` + `safe_filename` + S3/R2 optionnel | [FAIT] P10 |
| Login / analyse sans limite | Brute force / coût IA | Rate limit IP + user/org **par instance** | [FAIT] P9 |
| `init_db` ALTER | Schéma hors Alembic | Boot = import modèles seulement | [FAIT] |
| `/health` faux vert | Ops | `/health/ready` ping SQL | [FAIT] |
| Stripe `user_id` client | Billing IDOR | Routes hors `BILLING_ENABLED` ; org JWT | [FAIT] |

---

## Modèle d’autorisation cible

Dépendances FastAPI :

- `get_current_user()` — cookie `da_access` ou `Authorization: Bearer`
- `require_authenticated_user()`
- `require_organization_access(organization_id)`
- `require_admin()` — `is_platform_admin`
- `require_permission(resource, action)` — RBAC (P3+)

Règles :

- Jamais faire confiance à un id fourni par le client.
- Documents / exports privés : `document.organization_id == current_user.organization_id`.
- Le frontend ne peut pas s’auto-promouvoir admin.

---

## Secrets

| Secret | Où | Public ? |
|--------|----|----------|
| `JWT_SECRET` | backend `.env` | Non |
| `DATABASE_URL` | backend `.env` | Non |
| `MISTRAL_API_KEY` | backend `.env` | Non |
| `STRIPE_SECRET_KEY` | backend `.env` | Non |
| `STRIPE_WEBHOOK_SECRET` | backend `.env` | Non |
| `MAKE_WEBHOOK_URL` | backend `.env` | Non (jamais `NEXT_PUBLIC_`) |
| `MAKE_WEBHOOK_SECRET` | backend `.env` | Non (header `X-DocAnalyse-Secret`) |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | backend `.env` | Non (jamais `NEXT_PUBLIC_`) |
| `NEXT_PUBLIC_API_URL` | frontend | Oui (URL) |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | frontend | Oui (publishable) |

Interdit : `NEXT_PUBLIC_` pour un secret. Interdit : fallback de clé en dur.

---

## Cookies de session

- Nom : `da_access`
- `HttpOnly`, `SameSite=Lax`
- `Secure` dès que `ENV=production`
- Durée access : 15 min ; refresh : `da_refresh` 7 jours

---

## Mots de passe

- Hash bcrypt (passlib / bcrypt).
- Minimum 8 caractères à l’inscription (remplace le 6 Firebase).
- Les hash Firebase **ne sont pas migrables** → flux « mot de passe oublié ».

---

## Checks CI (à brancher)

- Lint frontend + ruff/pytest backend
- Tests auth : anonyme, token invalide, rôle insuffisant
- Tests IDOR : orga A vs ressource B (mocks CI)
- Live Neon : `IDOR_LIVE=1 pytest tests/test_idor_live.py` (jobs, findings, evidence, audits, slugs fichiers)
- `gitleaks` ou équivalent sur les secrets
- Build Next + import FastAPI

---

## Stockage objet (P10)

- Upload / download / delete uniquement via le backend (`app.storage`).
- Jamais de clé objet, d’URL signée ou de credentials S3/R2 côté navigateur.
- Isolation : `{namespace}/{organization_id}/{fichier}` + contrôle d’accès slug/orga déjà en place.
- Rate limiting P9 : compteurs en mémoire **par process**. Derrière plusieurs instances, les limites ne sont pas globales. Redis = post-MVP, **non bloquant**.
- Cible go-live : **Cloudflare R2** privé (`STORAGE_BACKEND=r2`). Noms `S3_*` conservés (API S3-compatible).
- `FileResponse` sert le cache local : en prod, B doit matérialiser depuis R2 après le `commit` de A (pas le disque de A).

---

## Ce qui est déjà correct

- `.env*` gitignoré à la racine
- Webhook Stripe vérifié (`stripe-signature`)
- Pas de `dangerouslySetInnerHTML` dans `src/`
- `backend/.gitignore` listait déjà `app/firebase_key.json` — le fichier existait quand même en local
