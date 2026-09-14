# Décisions techniques

Journal court. Format : date — décision — statut.

| Date | Décision | Statut |
|------|----------|--------|
| 2026-09-12 | Neon PostgreSQL = source unique. Pas de nouvel hybride Firebase+SQL. | [FAIT] |
| 2026-09-12 | Auth : JWT + cookies httpOnly (`da_access` / `da_refresh`), plus Firebase Auth. | [FAIT] |
| 2026-09-12 | Identité toujours dérivée du token. Interdit `firebase_uid` query. | [FAIT] |
| 2026-09-12 | `users.firebase_uid` nullable (transition). Drop colonne plus tard, après migration data. | [FAIT] drop P8 / `0006` |
| 2026-09-12 | Admin = `users.is_platform_admin`, jamais un champ client. | [FAIT] |
| 2026-09-12 | Knowledge Base globale vs données orga. Collision : `controls` (orga) vs futur `kb_controls`. | [FAIT] |
| 2026-09-12 | Routes UI actuelles (`/employe`, `/grc`) conservées en P0–P2. Renommage section 18 plus tard. | [FAIT] |
| 2026-09-12 | Mots de passe Firebase non migrés. Reset obligatoire. | [FAIT] |
| 2026-09-12 | Fichiers : disque local en dev ; objet plus tard. Métadonnées en SQL. | [FAIT] |
| 2026-09-12 | Alembic pour les **nouvelles** tables. `init_db()` reste pour colonnes héritées le temps du snapshot. | [FAIT] |
| 2026-09-12 | Pas de texte ISO intégral en base. | [FAIT] |
| 2026-09-12 | P0 livré : JWT + cookies, plus de clé client, plus de `firebase_uid` query sur analyses/users/risks, résultats et exports protégés. | [FAIT] |
| 2026-09-12 | Pages GRC, profil, paramètres, résultat-analyse : plus de Firebase runtime. | [FAIT] |
| 2026-09-12 | Phase 7 : SDK `firebase` retiré, plus de `firebase.js` / Admin key template. | [FAIT] |
| 2026-09-12 | Alembic baseline `0001_baseline` (schéma historique via `init_db`). | [FAIT] |
| 2026-09-12 | Tests IDOR (orga + 401 listes) sans Neon. | [FAIT] |
| 2026-09-12 | P3 : `organization_profiles`, règles globales, décisions orga, `kb_controls` (pas de texte ISO). | [FAIT] |
| 2026-09-12 | P4 : jobs SQL autour de `/analyser/` (pas de réécriture pipeline). Tracker best-effort. | [FAIT] |
| 2026-09-12 | P4 : job sync démarre en `running` (pas de file `queued`). Findings extraits de `details[]`. | [FAIT] |
| 2026-09-12 | P5 : preuves proposées depuis findings (medium+), revue manuelle. Traitements ISO 31000. | [FAIT] |
| 2026-09-12 | P5 : pas de table `actions` distincte (`action_plans` / `corrective_actions` suffisent). | [FAIT] |
| 2026-09-12 | P6 : `audits` / `audit_findings` ; garder `audit_logs` et `compliance_audits`. | [FAIT] |
| 2026-09-12 | P6 : KRIs restent `kris` + `kri_metrics` (pas de tables parallèle). | [FAIT] |
| 2026-09-12 | Billing conservé (Stripe, plans, quotas, /abonnement) mais déconnecté. `BILLING_ENABLED=false`. | [FAIT] |
| 2026-09-12 | P7 : `analysis_jobs` unique source d’état ; dicts process (`etat_analyses`) supprimés. | [FAIT] |
| 2026-09-12 | P7 : webhook Make.com via `MAKE_WEBHOOK_URL` / `MAKE_WEBHOOK_SECRET` (jamais le navigateur). | [FAIT] |
| 2026-09-12 | P7 : plus de clé maître `API_KEY_ATTENDUE`. Clés `api_keys` Enterprise seulement. | [FAIT] |
| 2026-09-12 | P7 : tests IDOR étendus + suite live Neon (`IDOR_LIVE=1`). | [FAIT] |
| 2026-09-12 | P8 : grep global puis drop `firebase_uid`. `PlanService` lookup UUID seul. Script de migration résout par email. | [FAIT] |
| 2026-09-12 | Pas de P9 Firebase. `migrate_firebase.py` archivé (non-runtime) jusqu’à close historique. Suite = risques production. | [FAIT] |
| 2026-09-12 | P9 : CORS/JWT/ENCRYPTION fail-fast hors dev ; stockage via `app.storage` ; rate limits ; Alembic seul ; health ping ; Stripe si billing on. | [FAIT] |
| 2026-09-12 | P10 : backend S3-compatible derrière `app.storage` ; isolation `organization_id` dans la clé ; pas d’exposition navigateur ; migration locale sans delete. Rate limit Redis / observabilité / jobs distribués = lots suivants. | [FAIT] |
| 2026-09-12 | P0–P10 figés. Jalon = MVP production-ready **applicatif**, sous réserve infra prod. Pas de P11 automatique. Suite = go-live / exploitation. Redis, observabilité, jobs distribués = post-MVP non bloquants. | [FAIT] |
| 2026-09-12 | Stockage go-live = **Cloudflare R2** (`STORAGE_BACKEND=r2`, API S3-compatible, noms `S3_*`). `local` reste le défaut de développement. Aucun lot applicatif pour ce choix. | [FAIT] |
| 2026-09-12 | Baseline Go-Live figée : P0–P10 code-complete ; R2 = prod ; `app.storage` seule API ; prochaine étape = validation infra réelle uniquement. Redis / observabilité / jobs = post-MVP. | [FAIT] |
| 2026-09-12 | Baseline de référence close : aucun P11, aucune réouverture P9/P10. Checklist PROJECT_AUDIT = exploitation. Prochain audit = Go-Live réel (preuves infra), pas une revue de code. Firebase = révocation GCP + audit environnements. | [FAIT] |
| 2026-09-13 | Dépôt fonctionnel gelé (P0–P10 FROZEN). Phase exclusive infra : provisionner → configurer → déployer → tester → prouver. R2/Neon « ready » code ≠ PASS production. NO-GO jusqu’aux preuves. Pas de simulation Cloudflare/Neon/GCP/hébergeur. | [FAIT] |
