# Base de données — état réel

**Moteur :** Neon PostgreSQL.  
**Accès :** FastAPI → SQLAlchemy 2 uniquement. Jamais depuis Next.js.  
**Détail des tables :** [DATABASE_ARCHITECTURE.md](../../DATABASE_ARCHITECTURE.md) à la racine.

Il n’existe **pas** de dossier `backend/app/database/` (modèles / repositories). La connexion est `backend/app/database.py`. Les modèles sont dans `backend/app/models/`. Les migrations sont `backend/alembic/versions/` (`0001` → `0007_iso_catalog`). `0007` = catalogue ISO métadonnées (pas un feu vert Go-Live).

---

## Environnements

Une base Neon **par environnement**. Même noms de variables, valeurs différentes injectées hors git.

| Environnement | Rôle | Variables |
|---------------|------|-----------|
| Development | Dev local | `DATABASE_URL`, `DIRECT_DATABASE_URL`, `ENV=development` |
| Staging | Recette | mêmes noms, projet Neon staging |
| Production | Go-Live | mêmes noms, projet Neon production |

- `DATABASE_URL` : pooler (application).
- `DIRECT_DATABASE_URL` : connexion directe (Alembic).
- Ne jamais coller un mot de passe dans le code. Voir `.env.example` (placeholders uniquement).

```bash
cd backend && .venv/bin/alembic upgrade head
```

`init_db()` n’altère plus le schéma.

---

## Interdit

- Exécuter `database/migration_add_firebase_uid.sql` (fichier mort, recréerait `firebase_uid`).
- Modifier le schéma prod hors Alembic.
- Lire/écrire Neon depuis le navigateur.
