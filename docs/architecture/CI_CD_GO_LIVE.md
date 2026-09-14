# CI / CD Go-Live

Pipeline réel du dépôt : `.github/workflows/ci.yml`  
**Non réécrit** dans ce passage.

---

## CI

**[PASS]** (définition dans le repo — statut des runs GitHub non consulté ici)

```text
on: pull_request, push → main|master

backend:
  pip install -r requirements.txt
  pytest (suite listée, JWT_SECRET=ci-test-secret, valeur non loguée)

frontend:
  npm ci
  npm run lint
  npm run build
  NEXT_PUBLIC_API_URL=http://localhost:8000
```

Présent : install, pytest, lint, build Next.  
Absent du workflow : déploiement, `alembic upgrade`, health prod, secrets R2/Neon.

---

## CD

**[BLOCKED]** — aucun job de déploiement, hébergeur inconnu.

## Production credentials

**[BLOCKED]** — pas de secret manager d’hébergeur branché sur ce workflow.

## Alembic production

**[BLOCKED]** — migrations à lancer **manuellement** sur l’hôte / un one-shot après backup :

```bash
cd backend && .venv/bin/alembic upgrade head
```

Ne pas ajouter un deploy GitHub Actions tant que l’hébergeur et ses credentials ne sont pas choisis.

---

## Écart pour un futur CD (hors ce passage)

Quand l’hébergeur sera connu : build + env `ENV=production` + secrets injectés + `alembic upgrade head` + smoke `/health/ready`. Rollback = redeploy image/commit précédent + restauration Neon si la migration est en cause (voir `NEON_BACKUP_RESTORE.md`).
