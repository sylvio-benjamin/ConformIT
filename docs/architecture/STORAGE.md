# Stockage fichiers — état réel

**Façade unique :** `backend/app/storage/` (`app.storage`).  
**Ne pas créer** de dossier `/storage/` à la racine. **Ne pas déplacer** `app.storage`.

```text
Frontend
    ↓
FastAPI (auth + isolation organization_id)
    ↓
app.storage
    ↓
local (dev)  ou  Cloudflare R2 (production)
```

PostgreSQL garde les métadonnées (`organization_id`, `storage_key` interne, slug, type, taille).  
R2 (ou le disque local) garde le binaire.  
Aucune clé objet, URL signée ou credential S3/R2 n’est envoyée au navigateur. `job_to_dict` n’expose pas `storage_key`.

---

## Backends

| `STORAGE_BACKEND` | Usage | Contrôle au boot |
|-------------------|-------|------------------|
| `local` (défaut) | Développement / une instance | `STORAGE_ROOT` (souvent `data/`) |
| `r2` | **Go-Live production** | `S3_BUCKET` + `S3_ACCESS_KEY` + `S3_SECRET_KEY` + **`S3_ENDPOINT` obligatoire** |
| `s3` | Alternative AWS | bucket + clés |

Noms `S3_*` conservés : R2 expose une API S3-compatible.

```env
STORAGE_BACKEND=r2
S3_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_BUCKET=docanalyse-prod
S3_REGION=auto
S3_ACCESS_KEY=
S3_SECRET_KEY=
```

Namespaces : `uploads` / `audits` / `pdfs` / `excels`.  
Clés nouvelles : `{namespace}/{organization_id}/{fichier}`. Lecture de secours de la clé plate héritée.

`FileResponse` sert un **cache local d’instance**. En prod : A `commit` → R2 → B matérialise depuis R2, sans le disque de A.

---

## Migration locale → R2

```bash
python scripts/migrate_local_storage.py
python scripts/migrate_local_storage.py --apply
```

Dry-run par défaut. **Ne supprime jamais** `data/`. Retirer le disque seulement après validation A→R2→B + redémarrage.

Preuves Go-Live (pas encore produites ici) : bucket privé, credentials minimaux, isolation orga réelle, backup/restauration.
