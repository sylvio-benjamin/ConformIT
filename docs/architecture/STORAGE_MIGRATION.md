# Migration stockage local → R2

**Date :** 13 septembre 2026  
**Script :** `scripts/migrate_local_storage.py` (inspecté, **non adapté**, **non --apply**)  
**Règle :** ne pas déclarer la migration terminée sans comparaison source/destination.

---

| Champ | Valeur |
|-------|--------|
| Source | `data/` (défaut `STORAGE_ROOT` ; hors `.cache`) |
| Destination | Cloudflare R2 (`STORAGE_BACKEND=r2`) — **non configuré** |
| Nombre de fichiers métier | **0** |
| Taille | **0 octets** |
| Types | — |
| Succès | 0 |
| Échecs | 0 (aucun apply) |
| Références PostgreSQL vérifiées | non (pas de run) |
| Fichiers orphelins | n/a |
| Fichiers manquants | n/a |
| Dry-run exécuté vers R2 | non |
| `--apply` | non |
| Données locales supprimées | **non** |

Hors scope `app.storage` : dump `analysesae-default-rtdb-export.json` présent localement (gitignoré).

**Statut :** [NOT APPLICABLE] transfert (rien à copier sur ce poste) + [BLOCKED] validation R2 réelle (pas de bucket / credentials / deux instances).
