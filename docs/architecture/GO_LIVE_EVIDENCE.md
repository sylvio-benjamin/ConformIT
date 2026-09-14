# Go-Live Evidence

**Date :** 13 septembre 2026  
**Décision :** **NO-GO** (infrastructure de production non démontrée)  
**Code P0–P10 :** non rouvert. Aucun nouveau blocker applicatif.

Trois statuts seulement : **[PASS]** = preuve disponible ; **[BLOCKED]** = infra inaccessible ; **[MANUAL]** = action humaine.

« Le code semble prêt » n’est **pas** un [PASS] d’infrastructure.  
**R2 READY (code) ≠ R2 production PASS. Neon compatible ≠ Neon production démontré.**

Dépôt fonctionnel **gelé**. Phase exclusive : Infrastructure → Déploiement → Preuves.  
NO-GO → GO seulement avec preuves vérifiables des blockers critiques.

---

## Code / préparation repo (ce passage)

| Item | Statut | Preuve |
|------|--------|--------|
| Aucune modification P0–P10 nécessaire | [PASS] | Pas de changement `src/` / `backend/app/` métier |
| `app.storage` prêt pour R2 | [PASS] | `STORAGE_BACKEND=local\|r2` ; `S3_ENDPOINT` obligatoire si `r2` |
| Configuration documentée | [PASS] | `.env.example` classé ; docs ci-dessous |
| CI existant vérifié | [PASS] | `.github/workflows/ci.yml` : install, pytest, lint, build |
| Health existant | [PASS] | `/health/live`, `/health`, `/health/ready` (SQL) |
| Dump RTDB hors runtime / `public/` | [PASS] | gitignore ; pas d’import `src/` / `backend/app/` |
| [NO NEW APPLICATION BLOCKER] | [PASS] | Secrets frontend = `NEXT_PUBLIC_API_URL` (+ Stripe publishable vide) |

Docs produits : `R2_GO_LIVE.md`, `NEON_BACKUP_RESTORE.md`, `CI_CD_GO_LIVE.md`, `GCP_SECRET_REVOCATION.md`, `DEPLOYMENT.md`, `STORAGE_MIGRATION.md`.

---

## Infrastructure (inchangé — inaccessible)

| Item | Statut |
|------|--------|
| R2 réel | [BLOCKED] |
| Neon production | [BLOCKED] |
| Hébergeur / `ENV=production` déployé | [BLOCKED] |
| Secret manager hébergeur | [BLOCKED] |
| A → R2 → B | [BLOCKED] |
| Isolation réelle A/B | [BLOCKED] |
| Redémarrage prod | [BLOCKED] |
| Backup / restore réel | [BLOCKED] ([DOCUMENTED] dans `NEON_BACKUP_RESTORE.md`) |
| CD | [BLOCKED] |
| Parcours e2e production | [BLOCKED] |
| Révocation clé Admin GCP | [MANUAL] |
| Suppression dump RTDB local | [MANUAL] |

Environnement inspecté précédemment : `ENV=development`, localhost, `S3_*` absents. Ce n’est pas la production.

---

## Prochaine étape (hors repo)

```text
PROVISIONNER → CONFIGURER → DÉPLOYER → TESTER → PROUVER → GO / NO-GO
```

Procédures : `DEPLOYMENT.md`, `R2_GO_LIVE.md`.  
Tant qu’un blocker critique subsiste : **NO-GO**.
