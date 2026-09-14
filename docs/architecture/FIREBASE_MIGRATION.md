# Firebase → Neon — inventaire réel (dépôt existant)

**Date :** 13 septembre 2026  
**Règle :** décrit le code actuel. Pas une cible hexagonale. P0–P10 figés.  
**Chaîne runtime :** Next.js → FastAPI → SQLAlchemy → Neon. Le navigateur n’écrit ni dans Firebase ni dans PostgreSQL.

`scripts/migrate_firebase.py` est un outil **one-shot archivé** (hors FastAPI / Next.js). Ne pas le supprimer tant qu’un restore RTDB reste possible. Ne pas en créer un second.

---

## Verdict runtime

| Surface | Firebase runtime | Statut |
|---------|------------------|--------|
| `src/` | Aucun import `firebase` / `getAuth` / `getDatabase` / `onValue` | [OK] |
| `package.json` | Pas de dépendance `firebase` | [OK] |
| `backend/app/` | Aucune occurrence `firebase` / `firebase_uid` / `firebase_key` | [OK] |
| `backend/requirements.txt` | Pas de `firebase-admin` | [OK] |
| Colonne `users.firebase_uid` | Droppée Alembic `0006` | [OK] |
| Identité | JWT cookies `da_access` / `da_refresh` | [OK] |
| Double écriture Firebase + SQL | Absente du runtime | [OK] |

Les chunks `@firebase/*` sous `.next/` sont un **cache de build ancien**, pas du source. Ils disparaissent au prochain `next build` propre.

---

## Cartographie

| Usage Firebase | Fichier | Fonction | Données | Remplacement PostgreSQL | Statut |
| -------------- | ------- | -------- | ------- | ----------------------- | ------ |
| Auth email/mdp | (supprimé) `src/services/firebase.js` | login / register | comptes | `backend/app/api/auth.py` + `users.password_hash` | [OK] runtime |
| `utilisateurs/{uid}` | script archivé | import | profil, admin | `users` + `organizations` ; `admin` → `is_platform_admin` | [OK] code ; apply data = ops |
| `?firebase_uid=` | (supprimé) analyses / users / risks | IDOR | identité client | `get_current_user` JWT | [OK] |
| `users.firebase_uid` | `0006_drop_firebase_uid.py` | lookup | uid legacy | `users.id` UUID ; script par **email** | [OK] |
| RTDB `analyses` / `entreprises` / GRC | `scripts/migrate_firebase.py` | import one-shot | historique | `analyses`, `companies`, risques, contrôles, incidents, kris | [OK] script ; apply = ops |
| Admin SDK | `backend/app/firebase_key.json` | Admin | projet GCP | **fichier hors repo** ; **révoquer la clé dans GCP** | [OK] code ; [À FAIRE] humain |
| Export RTDB local | `analysesae-default-rtdb-export.json` | dump | PII | gitignoré ; ne pas committer | [OK] gitignore ; [À FAIRE] destruction hors git |
| SQL legacy add column | `database/migration_add_firebase_uid.sql` | ALTER | `firebase_uid` | **Ne pas exécuter** (régresserait P8) | [À SUPPRIMER] fichier mort |
| Tests garde-fou | `tests/test_firebase_uid_removed.py` | CI | — | interdit toute recréation runtime | [OK] |
| Docs / décisions | `MIGRATION_PLAN.md`, `DECISIONS.md` | historique | — | référence, pas runtime | [OK] |

---

## Script `scripts/migrate_firebase.py`

Inspecté, **non réécrit**.

- Dry-run par défaut ; `--apply` / `--verify`.
- Résout users/GRC par **email** (carte uid→email de l’export).
- N’écrit plus `users.firebase_uid`.
- Journalise les incohérences (Auth sans nœud RTDB, etc.).
- Mots de passe Firebase **non migrables** → inscription ou mot de passe oublié.

Compléter un apply sur un dump réel = opération Go-Live, pas un nouveau modèle de données.

---

## Ce qui n’est plus à faire dans le code

- Introduire PostgreSQL (déjà Neon).
- Remplacer le JWT.
- Recréer des bounded contexts.
- Rouvrir P8–P10.

## Ce qui reste (exploitation, pas backlog applicatif)

- Appliquer le script sur un dump si des comptes historiques manquent encore en Neon.
- Révoquer la clé Admin dans GCP.
- Auditer CI/CD et secrets d’hébergement.
- Détruire ou archiver hors git le dump RTDB.

---

## Recherche de contrôle

```bash
rg -i 'firebase|firebase_uid|firebase_key' src backend/app --glob '!**/node_modules/**'
# attendu : 0
```
