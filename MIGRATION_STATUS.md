# État de la migration PostgreSQL

## ✅ Complété

### Backend
- ✅ Modèles PostgreSQL créés (`analyses.py`, `collaborators.py`, `organizations.py` adapté)
- ✅ API `/api/users` (CRUD utilisateurs, collaborateurs)
- ✅ API `/api/analyses` (CRUD analyses, entreprises, documents)
- ✅ Intégration dans `main.py`

### Frontend - Services & Hooks
- ✅ `src/services/api.js` - Service API centralisé pour communiquer avec le backend
- ✅ `src/hooks/useAnalyses.js` - Hook pour gérer les analyses depuis PostgreSQL
- ✅ `src/hooks/useUserProfile.js` - Hook pour gérer le profil utilisateur et collaborateurs

### Frontend - Pages adaptées
- ✅ `src/app/employe/page.js` - Page principale des analyses
- ✅ `src/app/historique/page.js` - Historique des analyses
- ✅ `src/app/employe/dashboard/page.js` - Tableau de bord

## 🔄 En cours / À faire

### Frontend - Pages utilisateurs
- ⏳ `src/app/employe/profile/page.js` - Profil utilisateur (utilise encore Firebase pour collaborateurs)
- ⏳ `src/app/employe/parametres/page.js` - Paramètres utilisateur
- ⏳ `src/app/admin/utilisateur/page.js` - Gestion utilisateurs admin
- ⏳ `src/app/inscription/page.js` - Inscription (créer utilisateur dans PostgreSQL)

### Frontend - Pages GRC
- ⏳ `src/app/grc/risks/page.js` - Risques
- ⏳ `src/app/grc/controls/page.js` - Contrôles
- ⏳ `src/app/grc/incidents/page.js` - Incidents
- ⏳ `src/app/grc/kris/page.js` - KRIs
- ⏳ `src/app/grc/compliance/page.js` - Conformité
- ⏳ `src/app/grc/reports/page.js` - Rapports

### Backend - Services à migrer
- ⏳ `backend/app/services/plan_service.py` - Utilise Firebase pour quotas
- ⏳ `backend/app/user_routes.py` - Utilise Firebase pour utilisateurs
- ⏳ `backend/app/api_keys.py` - Utilise Firebase pour clés API
- ⏳ `backend/app/plan_routes.py` - Utilise Firebase pour historique
- ⏳ `backend/app/stripe_webhook.py` - Utilise Firebase pour abonnements

## 📝 Notes importantes

1. **Authentification** : Firebase reste utilisé uniquement pour l'authentification (auth)
2. **Données** : Toutes les données opérationnelles passent maintenant par PostgreSQL
3. **Migration progressive** : Les anciennes données Firebase peuvent coexister pendant la transition
4. **Tests** : Tester chaque page individuellement après migration

## 🚀 Prochaines étapes

1. Adapter les pages utilisateurs restantes
2. Adapter toutes les pages GRC
3. Migrer les services backend restants
4. Créer un script de migration pour transférer les données Firebase existantes vers PostgreSQL
5. Tests complets de bout en bout

