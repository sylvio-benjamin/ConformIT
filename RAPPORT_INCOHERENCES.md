# 📋 Rapport d'Incohérences et Corrections

## ✅ Corrections Appliquées

### Backend

1. **`backend/app/auth.py`**
   - ✅ Ajout de `joinedload(APIKey.user)` pour charger la relation user
   - ✅ Remplacement de `is_active == True` par `is_active.is_(True)` (syntaxe SQLAlchemy correcte)
   - ✅ Vérification de `api_key_obj.user` avant accès

2. **`backend/app/main.py`**
   - ✅ Suppression de l'import `firebase_admin.db` (plus utilisé pour le stockage)
   - ✅ Suppression de l'import `FIREBASE_DATABASE_URL` (commenté)
   - ✅ Initialisation Firebase uniquement pour l'authentification (sans databaseURL)
   - ✅ Health check mis à jour : `firebase_auth` au lieu de `firebase`

3. **`backend/app/config.py`**
   - ✅ `FIREBASE_DATABASE_URL` commenté (plus nécessaire)

4. **`backend/app/api_keys.py`**
   - ✅ Remplacement de `is_active == True` par `is_active.is_(True)` (3 occurrences)

### Frontend

1. **`src/app/grc/reports/page.js`**
   - ✅ Remplacement de `toast.info()` par `toast()` (react-hot-toast n'a pas de méthode `info()`)

---

## ⚠️ Fichiers Frontend à Migrer vers PostgreSQL API

Les fichiers suivants utilisent encore Firebase Database (`ref(db, ...)`) pour le stockage de données au lieu de l'API PostgreSQL :

### Priorité Haute (Données critiques)

1. **`src/app/employe/resultat-analyse/page.js`**
   - ❌ Utilise `ref(db, 'analyses')` pour sauvegarder les analyses
   - ❌ Utilise `ref(db, 'documents/...')` pour sauvegarder les documents
   - ❌ Utilise `ref(db, 'entreprises/...')` pour sauvegarder les entreprises
   - ✅ **Action** : Ces données sont déjà sauvegardées dans PostgreSQL via `/analyser/`, mais cette page sauvegarde aussi dans Firebase

2. **`src/hooks/useAuth.js`**
   - ❌ Utilise `ref(db, 'utilisateurs/...')` pour lire les données utilisateur
   - ✅ **Action** : Utiliser `/api/users/me` (PostgreSQL)

3. **`src/hooks/useQuota.js`**
   - ❌ Utilise `ref(db, 'utilisateurs/...')` pour lire les quotas
   - ✅ **Action** : Utiliser `/quota/{user_id}` qui utilise maintenant PostgreSQL

### Priorité Moyenne (Pages GRC)

4. **`src/app/grc/risks/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/risks')` pour les risques
   - ✅ **Action** : Utiliser `/api/risks` (PostgreSQL)

5. **`src/app/grc/controls/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/controls')` pour les contrôles
   - ✅ **Action** : Utiliser `/api/controls` (PostgreSQL)

6. **`src/app/grc/incidents/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/incidents')` pour les incidents
   - ✅ **Action** : Utiliser `/api/incidents` (PostgreSQL)

7. **`src/app/grc/kris/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/kris')` pour les KRIs
   - ✅ **Action** : Utiliser `/api/kris` (PostgreSQL)

8. **`src/app/grc/compliance/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/compliance')` pour la conformité
   - ✅ **Action** : Utiliser `/api/compliance` (PostgreSQL)

9. **`src/app/grc/reports/page.js`**
   - ❌ Utilise `ref(db, 'grc/${user.uid}/reports')` pour les rapports
   - ✅ **Action** : Utiliser `/api/reports` (PostgreSQL)

10. **`src/app/grc/page.js`**
    - ❌ Utilise `ref(db, 'grc/${user.uid}/stats')` pour les statistiques
    - ✅ **Action** : Calculer depuis PostgreSQL

### Priorité Faible (Pages admin/utilisateur)

11. **`src/app/employe/profile/page.js`**
    - ❌ Utilise `ref(db, 'collaborateurs/...')` pour les collaborateurs
    - ✅ **Action** : Utiliser `/api/users/me/collaborators` (PostgreSQL)

12. **`src/app/employe/parametres/page.js`**
    - ❌ Utilise `ref(db, 'utilisateurs/...')` pour les préférences
    - ✅ **Action** : Utiliser `/api/users/me` PUT (PostgreSQL)

13. **`src/app/admin/utilisateur/page.js`**
    - ❌ Utilise `ref(db, 'utilisateurs')` pour lister les utilisateurs
    - ✅ **Action** : Utiliser `/api/users` (PostgreSQL) - À créer

14. **`src/app/admin/utilisateur/ajouter/page.js`**
    - ❌ Utilise `ref(db, 'utilisateurs/...')` pour créer un utilisateur
    - ✅ **Action** : Utiliser `/api/users` POST (PostgreSQL) - À créer

15. **`src/services/planClient.js`**
    - ❌ Utilise `ref(db, 'utilisateurs/...')` pour mettre à jour le plan
    - ✅ **Action** : Les plans sont maintenant dans PostgreSQL (`User.abonnement`)

16. **`src/app/abonnement/page.js`**
    - ❌ Utilise `ref(db, 'utilisateurs/...')` pour lire le plan
    - ✅ **Action** : Utiliser `/plan/{user_id}` qui utilise PostgreSQL

---

## 📝 Notes Importantes

### Firebase Auth (Gardé)
- ✅ `src/services/firebase.js` - Service Firebase pour l'authentification
- ✅ `src/hooks/useAuth.js` - Utilise Firebase Auth (correct)
- ✅ Tous les fichiers qui utilisent `auth` de Firebase (correct)

### Firebase Database (À Remplacer)
- ❌ Tous les fichiers qui utilisent `ref(db, ...)` pour le stockage de données
- ❌ Tous les fichiers qui utilisent `set(ref(db, ...))`, `get(ref(db, ...))`, etc.

---

## 🔄 Prochaines Étapes Recommandées

1. ✅ Migrer `src/app/employe/resultat-analyse/page.js` vers PostgreSQL
2. ✅ Migrer `src/hooks/useQuota.js` vers PostgreSQL API (`/quota/{user_id}`)
3. ✅ Migrer toutes les pages GRC vers leurs APIs PostgreSQL respectives
4. ✅ Migrer `src/app/employe/profile/page.js` vers `/api/users/me/collaborators`
5. ✅ Migrer `src/app/employe/parametres/page.js` vers `/api/users/me` PUT
6. ✅ Créer `/api/users` pour la gestion admin des utilisateurs

