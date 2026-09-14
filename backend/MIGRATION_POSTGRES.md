# Migration Firebase → PostgreSQL

## Vue d'ensemble

Cette migration transfère toutes les données opérationnelles de Firebase vers PostgreSQL, tout en conservant Firebase uniquement pour l'authentification.

## Architecture

- **Firebase** : Authentification uniquement (uid, email, tokens)
- **PostgreSQL** : Toutes les données (analyses, entreprises, documents, utilisateurs, GRC)

## Modèles créés

### Analyses
- `Analysis` : Analyse d'un document
- `Company` : Entreprise analysée
- `Document` : Document associé à une analyse
- `Counter` : Compteurs pour générer des IDs

### Utilisateurs
- `User` : Profil utilisateur (lié à Firebase via `firebase_uid`)
- `Collaborator` : Collaborateurs d'un utilisateur
- `Organization` : Organisation de l'utilisateur

## APIs créées

### `/api/users`
- `GET /api/users/me` : Récupère le profil utilisateur
- `POST /api/users/me` : Crée ou met à jour un utilisateur depuis Firebase
- `PUT /api/users/me` : Met à jour le profil utilisateur
- `GET /api/users/{user_id}/collaborators` : Liste les collaborateurs
- `POST /api/users/{user_id}/collaborators` : Ajoute un collaborateur
- `DELETE /api/users/{user_id}/collaborators/{collaborator_id}` : Supprime un collaborateur

### `/api/analyses`
- `GET /api/analyses` : Liste les analyses d'un utilisateur
- `GET /api/analyses/{slug}` : Récupère une analyse par slug
- `POST /api/analyses` : Crée une nouvelle analyse
- `PUT /api/analyses/{slug}` : Met à jour une analyse
- `DELETE /api/analyses/{slug}` : Supprime une analyse
- `GET /api/analyses/companies/list` : Liste les entreprises

## Adaptation frontend

### Remplacer les appels Firebase directs

**Avant (Firebase) :**
```javascript
import { ref, onValue, set, remove } from "firebase/database";
import { db } from "@/services/firebase";

const analysesRef = ref(db, `analyses/${user.uid}`);
onValue(analysesRef, (snapshot) => {
  const data = snapshot.val();
  setAnalyses(data);
});
```

**Après (API Backend) :**
```javascript
const response = await fetch(`http://localhost:8000/api/analyses?firebase_uid=${user.uid}`);
const data = await response.json();
setAnalyses(data.analyses);
```

### Adapter les hooks

Créer des hooks personnalisés pour les appels API :

```javascript
// hooks/useAnalyses.js
import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";

export function useAnalyses() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    
    fetch(`http://localhost:8000/api/analyses?firebase_uid=${user.uid}`)
      .then(res => res.json())
      .then(data => {
        setAnalyses(data.analyses || []);
        setLoading(false);
      });
  }, [user]);

  return { analyses, loading };
}
```

### Fichiers à adapter

1. **Pages analyses :**
   - `src/app/employe/page.js`
   - `src/app/employe/resultat-analyse/page.js`
   - `src/app/historique/page.js`
   - `src/app/employe/dashboard/page.js`

2. **Pages utilisateurs :**
   - `src/app/employe/profile/page.js`
   - `src/app/employe/parametres/page.js`
   - `src/app/admin/utilisateur/page.js`
   - `src/app/inscription/page.js`

3. **Pages GRC :**
   - `src/app/grc/risks/page.js`
   - `src/app/grc/controls/page.js`
   - `src/app/grc/incidents/page.js`
   - `src/app/grc/kris/page.js`
   - `src/app/grc/compliance/page.js`
   - `src/app/grc/reports/page.js`

## Services backend à adapter

Les services suivants utilisent encore Firebase et doivent être migrés :

1. `backend/app/services/plan_service.py` : Utilise Firebase pour quotas et analyses
2. `backend/app/user_routes.py` : Utilise Firebase pour utilisateurs
3. `backend/app/api_keys.py` : Utilise Firebase pour les clés API
4. `backend/app/plan_routes.py` : Utilise Firebase pour l'historique
5. `backend/app/stripe_webhook.py` : Utilise Firebase pour mettre à jour les abonnements

## Variables d'environnement

S'assurer que `.env.local` contient :

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sae_grc
POSTGRES_URL=postgresql://postgres:votre_mot_de_passe@localhost:5432/sae_grc
ENCRYPTION_KEY=votre_clé_32_bytes
```

## Migration des données existantes

Un script de migration peut être créé pour transférer les données Firebase existantes vers PostgreSQL. Voir `backend/scripts/migrate_firebase_to_pg.py` (à créer).

## Notes importantes

1. **Firebase UID** : Tous les utilisateurs doivent avoir un `firebase_uid` correspondant à leur UID Firebase
2. **Organisations** : Chaque utilisateur doit avoir une organisation associée
3. **Compatibilité** : Les anciennes données Firebase peuvent coexister pendant la migration
4. **Tests** : Tester chaque module individuellement avant de migrer complètement

