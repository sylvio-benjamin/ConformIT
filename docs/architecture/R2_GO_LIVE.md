# Cloudflare R2 — procédure Go-Live

**Statut infra :** [BLOCKED] — bucket / credentials non provisionnés dans cet audit.  
**Statut code :** prêt. `STORAGE_BACKEND=local` (dev) ou `r2` (prod). Le métier ne change pas.

Aucun credential dans ce document.

Noms **réels** du code (`backend/app/config.py`) :

| Variable | Rôle |
|----------|------|
| `STORAGE_BACKEND` | `local` (défaut) ou `r2` |
| `S3_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` — **obligatoire** si `r2` |
| `S3_BUCKET` | nom du bucket |
| `S3_ACCESS_KEY` | access key R2 (pas `S3_ACCESS_KEY_ID`) |
| `S3_SECRET_KEY` | secret R2 (pas `S3_SECRET_ACCESS_KEY`) |
| `S3_REGION` | `auto` recommandé pour R2 |
| `S3_PREFIX` | optionnel (isolation d’environnement) |

---

## 1. Créer le bucket

1. Cloudflare Dashboard → R2 → Create bucket.
2. Nom suggéré : `docanalyse-prod` (ou `docanalyse-staging`).
3. **Privé.** Pas d’accès public, pas de custom domain public, pas de « public access ».
4. Accès **API S3 uniquement** (Application credentials).

## 2. Credentials minimaux

1. R2 → Manage R2 API Tokens.
2. Token **dédié ConformIT**, un par environnement.
3. Permissions : lecture + écriture **sur ce bucket seulement** (pas Account-level Admin).
4. Pas d’accès à d’autres buckets.
5. Injecter via le secret manager de l’hébergeur, jamais Git, jamais `NEXT_PUBLIC_*`.

## 3. Variables d’environnement (production)

```env
STORAGE_BACKEND=r2
S3_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_BUCKET=docanalyse-prod
S3_REGION=auto
S3_ACCESS_KEY=
S3_SECRET_KEY=
```

Boot FastAPI : si `r2` sans `S3_ENDPOINT` / bucket / clés → **échec au démarrage** (`validate_storage_config`).

## 4. Tests manuels (après provisionnement)

Données de test minimales, pas de PII réelle.

### Upload

Utilisateur authentifié orga A → `/analyser/` ou endpoint d’upload existant.  
Vérifier objet R2 : `uploads/<organization_id>/<fichier>` (clé interne, jamais renvoyée au navigateur).

### Existence / SQL

Ligne `analysis_jobs` / `documents` : `storage_key` interne en base.  
`exists()` côté backend = true.

### Download (A → R2 → B)

Instance B (autre process, cache local vide) : téléchargement PDF/Excel autorisé.  
Contenu identique. Pas d’URL R2 dans le navigateur (`FileResponse` via cache local matérialisé).

### Delete

`DELETE /supprimer-fichiers/{slug}` (session orga A) : objet absent de R2, 404 ensuite.

### Accès interdit

Orga B : même slug / ID / URL → 401 si anonyme, 403/404 si authentifié hors orga (conventions actuelles).

## 5. Rollback

1. Remettre `STORAGE_BACKEND=local` **uniquement** si une instance unique et `STORAGE_ROOT` partagé — pas un rollback multi-instance.
2. Rollback prod sain : restaurer les secrets R2 précédents ou le prefix `S3_PREFIX` ; ne pas vider le bucket.
3. Ne jamais supprimer `data/` local tant que A→R2→B + redémarrage ne sont pas [PASS].

Migration fichiers : `python scripts/migrate_local_storage.py` puis `--apply`. Voir `STORAGE_MIGRATION.md`.
