# Déploiement — état réel (pas une cible théorique)

Ce fichier décrit **ce que le dépôt sait déployer aujourd’hui**.  
Pas de Docker, Kubernetes, nginx, Redis, Celery ni workers dans ce repo. Ces sujets restent post-MVP.

```text
Internet
   ↓
Next.js          (src/ à la racine, npm run build / start)
   ↓  cookies + NEXT_PUBLIC_API_URL
FastAPI          (backend/app/main.py, Uvicorn)
   ├── Neon      (DATABASE_URL pooler)
   └── R2        (app.storage, STORAGE_BACKEND=r2)
```

Alembic utilise `DIRECT_DATABASE_URL` (connexion directe, pas le pooler).

---

## Health (existant, non réécrit)

| Route | Rôle |
|-------|------|
| `GET /health/live` | process vivant |
| `GET /health` et `GET /health/ready` | ping SQL réel ; 503 si Neon down |

Pas de ping R2 dans le ready (éviterait d’exiger le bucket au health). Stockage : valider à l’upload après deploy.

---

## Variables

Voir `.env.example` (classes PUBLIC / SERVER ONLY / SECRET / INFRASTRUCTURE).  
Aucune valeur réelle ici. `S3_ACCESS_KEY` / `S3_SECRET_KEY` = noms du code.

Hors `ENV=development` : `JWT_SECRET`, `ENCRYPTION_KEY`, `CORS_ORIGINS` HTTPS explicites (pas localhost, pas `*`).  
`STORAGE_BACKEND=r2` sans `S3_ENDPOINT` → échec au boot.

---

## Séquence de déploiement

1. Provisionner R2 privé (`R2_GO_LIVE.md`).
2. Configurer les secrets (hébergeur / secret manager).
3. Vérifier Neon production (projet dédié, pas le `.env` local).
4. **Backup** Neon (`NEON_BACKUP_RESTORE.md`).
5. Déployer le backend (`ENV=production`).
6. `cd backend && .venv/bin/alembic upgrade head` **[BLOCKED — NEON PRODUCTION]** tant que la prod n’est pas accessible.
7. Déployer Next.js (`NEXT_PUBLIC_API_URL` = URL HTTPS publique de l’API).
8. `GET /health/ready`.
9. Login JWT.
10. Upload (données de test).
11. Vérifier l’objet dans R2 (console, clé interne).
12. Vérifier la référence PostgreSQL.
13. Download (idéalement depuis une 2ᵉ instance).
14. Analyse.
15. GRC (compliance / risk / contrôles).
16. Isolation orga A vs B.
17. Export PDF/Excel.
18. Restart des deux process + retéléchargement.
19. Smoke test (ci-dessous).

### Rollback

- Application : redéployer le commit précédent.
- Schéma : ne pas `downgrade` à l’aveugle ; restaurer une branche Neon de test d’abord, puis décider.
- R2 : ne pas vider le bucket ; revenir aux credentials / `S3_PREFIX` précédents.
- Ne pas supprimer le disque local de transition tant que R2 n’est pas [PASS].

---

## Smoke test production

Ne cocher **que** ce qui a été réellement testé sur l’environnement cible.

- [ ] Frontend accessible
- [ ] Backend accessible
- [ ] HTTPS
- [ ] Login
- [ ] JWT
- [ ] Neon
- [ ] Organization
- [ ] Upload
- [ ] R2
- [ ] Download
- [ ] Analyse
- [ ] Résultat
- [ ] Compliance
- [ ] Risk
- [ ] GRC
- [ ] Export
- [ ] Suppression
- [ ] Isolation

---

## Dump RTDB

`analysesae-default-rtdb-export.json` : PII potentielle, dans `.gitignore`, **pas** dans `public/`, **pas** importé par `src/` ni `backend/app/`.  
**[MANUAL DELETE]** sur les postes qui le possèdent encore. Cet audit ne l’a pas détruit.

---

## GCP

Checklist humaine : `GCP_SECRET_REVOCATION.md`. Ne pas provisionner GCS.

---

## Références

- `R2_GO_LIVE.md` — bucket et tests fichiers
- `NEON_BACKUP_RESTORE.md` — PITR / clone
- `CI_CD_GO_LIVE.md` — CI [PASS] définition, CD [BLOCKED]
- `GO_LIVE_EVIDENCE.md` — preuves / NO-GO
