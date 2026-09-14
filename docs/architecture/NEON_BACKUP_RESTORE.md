# Neon — backup / restauration

**Statut :** [DOCUMENTED]  
**Preuve réelle :** [BLOCKED — NEON PRODUCTION] — aucune restauration n’a été exécutée dans cet audit.

Le runtime utilise `DATABASE_URL` (pooler) et Alembic `DIRECT_DATABASE_URL` (connexion directe).  
Pas de nouvelle couche `database/`. Pas de nouveau modèle.

---

## 1. Méthode réellement disponible

Sur Neon (console du projet), le mécanisme standard est :

- **Point-in-time recovery (PITR)** / branches de restauration selon le plan Neon ;
- branches de développement séparées (dev / staging / prod = projets ou branches distincts).

Ce dépôt ne contient pas de script de dump cron. Ne pas inventer un `pg_dump` maison comme s’il était déjà en place.

Avant toute `alembic upgrade` prod :

```text
backup (console Neon / branche)
    ↓
alembic upgrade head
    ↓
GET /health/ready  (postgresql: true)
    ↓
smoke tests
```

```bash
cd backend && .venv/bin/alembic upgrade head
```

Ne jamais lancer une migration destructive sur la prod sans backup et validation humaine.

---

## 2. Environnement de restauration

**Ne pas restaurer par-dessus la production.**

1. Créer une branche / un projet Neon de **restauration-test**.
2. Pointer un backend de recette (`DIRECT_DATABASE_URL` / `DATABASE_URL` de ce clone uniquement).
3. Restaurer le PITR ou la branche à l’instant T.
4. Vérifier (ci-dessous).
5. Détruire le clone quand c’est fini.

---

## 3. Restauration

1. Console Neon → projet prod → Restore / Branch from timestamp (libellé exact selon l’UI).
2. Attendre que la branche soit `Ready`.
3. Copier l’URL **directe** (Alembic) et l’URL **pooler** (app) vers l’env de test.
4. Démarrer FastAPI de test avec ces URLs. Ne pas toucher aux secrets prod.

---

## 4. Vérification

- [ ] `GET /health/ready` → 200, `"postgresql": true`
- [ ] Login JWT
- [ ] Comptage d’une table métier connue (`users`, `analyses` ou `organizations`)
- [ ] Une analyse / un slug de test lisible
- [ ] Alembic : `alembic current` = `0007_iso_catalog` (head code ; n’appliquer `0007` en prod qu’après backup + validation staging)

---

## 5. Critères de succès

La restauration est [PASS] seulement si les cases ci-dessus sont cochées **sur le clone**, avec date, environnement et méthode notés dans `GO_LIVE_EVIDENCE.md`.

Tant que ce n’est pas fait : **[DOCUMENTED]**, pas [PASS].
