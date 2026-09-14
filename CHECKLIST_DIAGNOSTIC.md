# ✅ Checklist de Diagnostic Frontend-Backend

## 🔍 Vérifications Rapides (5 minutes)

### 1. ✅ Le backend répond-il à la racine ?

**Test dans le navigateur:**
```
http://localhost:8000/
```

**Résultat attendu:**
```json
{"message": "SAE Audit API - Serveur opérationnel", "version": "2.0.0", "status": "online"}
```

**Si ❌ ne fonctionne pas:**
- Le backend n'est pas démarré → Aller à l'étape 2
- Vérifier les logs dans le terminal où vous avez lancé `uvicorn`

---

### 2. ✅ Le backend est-il démarré correctement ?

**Commande pour démarrer:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**⚠️ IMPORTANT:** Utilisez `--host 0.0.0.0` (pas `127.0.0.1`) pour permettre les connexions depuis d'autres interfaces.

**Vérification dans les logs:**
- ✅ `INFO: Application startup complete.`
- ✅ `[OK] Base de données PostgreSQL initialisée`
- ✅ `INFO: Uvicorn running on http://0.0.0.0:8000`

**Si vous voyez des erreurs:**
- Erreur de port → Le port 8000 est peut-être utilisé: `netstat -ano | findstr :8000` (Windows)
- Erreur de dépendances → Réinstaller: `pip install -r requirements.txt`

---

### 3. ✅ CORS est-il configuré ?

**Test rapide dans le navigateur (Console F12):**
```javascript
fetch('http://localhost:8000/', {
  headers: { 'Origin': 'http://localhost:3000' }
}).then(r => {
  console.log('CORS Headers:', {
    'Allow-Origin': r.headers.get('Access-Control-Allow-Origin'),
    'Allow-Methods': r.headers.get('Access-Control-Allow-Methods')
  });
  return r.json();
}).then(console.log).catch(console.error);
```

**Résultat attendu:**
- `Allow-Origin: http://localhost:3000`
- Pas d'erreur CORS dans la console

**Si ❌ erreur CORS:**
- Vérifier `backend/app/main.py` lignes 94-101
- Assurez-vous que `http://localhost:3000` est dans `allow_origins`
- Redémarrer le backend après modification

---

### 4. ✅ L'URL du backend est-elle correcte dans le frontend ?

**Test dans le navigateur (Console F12):**
```javascript
console.log('API URL utilisée:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
```

**Vérifier le fichier `.env.local` à la racine du projet:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**⚠️ IMPORTANT:**
- Le fichier doit être `.env.local` (pas `.env`)
- Il doit être à la racine du projet (même niveau que `package.json`)
- **Après modification, redémarrer complètement Next.js** (Ctrl+C puis `npm run dev`)

**Vérifier dans le code:**
- `src/services/api.js` ligne 6 doit utiliser `process.env.NEXT_PUBLIC_API_URL`
- Vérifier que toutes les requêtes utilisent la même variable

---

### 5. ✅ Le protocole HTTP/HTTPS est-il cohérent ?

**Problème de contenu mixte:**
Si le frontend est sur `https://` et le backend sur `http://`, vous aurez une erreur:
```
Mixed Content: The page was loaded over HTTPS, but requested an insecure resource
```

**Solutions:**
1. **En développement:** Utilisez HTTP pour les deux:
   - Frontend: `http://localhost:3000`
   - Backend: `http://localhost:8000`

2. **Vérifier dans le navigateur:**
   - L'URL dans la barre d'adresse doit être `http://localhost:3000` (pas `https://`)

---

### 6. ✅ Vérifier l'erreur exacte dans la console du navigateur

**Ouvrir la Console développeur (F12) → Onglet Console et Network**

**A. Erreur CORS:**
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```
**Solution:** → Voir étape 3

**B. Erreur "Failed to fetch":**
```
TypeError: Failed to fetch
NetworkError when attempting to fetch resource
```
**Solutions possibles:**
- Backend non démarré → Voir étape 2
- Mauvaise URL → Voir étape 4
- Firewall/antivirus bloque la connexion
- Port bloqué

**C. Erreur de connexion:**
```
ERR_CONNECTION_REFUSED
```
**Solution:** → Voir étape 2 (backend non démarré)

**D. Erreur 404:**
```
GET http://localhost:8000/api/analyses 404 (Not Found)
```
**Solution:** 
- Vérifier que la route existe dans `backend/app/main.py`
- Vérifier l'URL complète (pas d'erreur de frappe)

**E. Erreur 500:**
```
GET http://localhost:8000/api/analyses 500 (Internal Server Error)
```
**Solution:**
- Vérifier les logs du backend pour voir l'erreur exacte
- Souvent: problème de base de données, colonnes manquantes, etc.

---

## 🧪 Tests Automatiques

### Script de Diagnostic Python

**Exécuter le script de diagnostic:**
```bash
cd backend
python test_api_connection.py
```

Ce script teste automatiquement:
- ✅ Connexion au backend
- ✅ Configuration CORS
- ✅ Requêtes préflight (OPTIONS)
- ✅ Requêtes réelles
- ✅ Ports ouverts

---

### Test depuis la Console du Navigateur

**Copier-coller dans la console du navigateur (F12):**

```javascript
// Test complet de communication
async function testBackendConnection() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  console.log('🔍 Test de connexion au backend...');
  console.log('URL utilisée:', API_URL);
  
  try {
    // Test 1: Backend répond-il ?
    const health = await fetch(`${API_URL}/`);
    console.log('✅ Test 1 - Backend accessible:', health.status);
    console.log('   Réponse:', await health.json());
    
    // Test 2: CORS fonctionne-t-il ?
    const corsTest = await fetch(`${API_URL}/health`);
    const corsHeaders = {
      'Origin': corsTest.headers.get('Access-Control-Allow-Origin'),
      'Methods': corsTest.headers.get('Access-Control-Allow-Methods')
    };
    console.log('✅ Test 2 - Headers CORS:', corsHeaders);
    
    if (!corsHeaders.Origin) {
      console.warn('⚠️  Pas de header Access-Control-Allow-Origin détecté');
    }
    
    // Test 3: Endpoint API
    const apiTest = await fetch(`${API_URL}/api/analyses?firebase_uid=test`);
    console.log('✅ Test 3 - Endpoint API:', apiTest.status);
    
    if (apiTest.status === 500) {
      const error = await apiTest.json();
      console.error('❌ Erreur serveur:', error);
    }
    
    console.log('✅ Tous les tests de base ont réussi !');
    
  } catch (error) {
    console.error('❌ Erreur de connexion:', error.message);
    console.error('   → Vérifiez que le backend est démarré sur', API_URL);
  }
}

testBackendConnection();
```

---

## 📋 Configuration Recommandée

### Backend (`backend/app/main.py`)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend (`.env.local` à la racine)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**⚠️ Important:** 
- Le fichier doit être `.env.local` (pas `.env`)
- À la racine du projet (même niveau que `package.json`)
- Après modification: **redémarrer Next.js complètement**

### Commandes de Démarrage

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

---

## 🐛 Solutions Rapides par Erreur

| Erreur | Solution |
|--------|----------|
| `Failed to fetch` | Backend non démarré → `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| `CORS blocked` | Vérifier `allow_origins` dans `backend/app/main.py` → Redémarrer backend |
| `404 Not Found` | Vérifier l'URL de la requête et que la route existe |
| `500 Internal Server Error` | Vérifier les logs du backend pour l'erreur exacte |
| `Mixed Content` | Utiliser HTTP pour les deux (pas HTTPS en dev) |
| Variables non chargées | Redémarrer Next.js après modification de `.env.local` |

---

## ✅ Validation Finale

**Checklist complète - Vérifier chaque point:**

- [ ] Backend répond sur `http://localhost:8000/`
- [ ] Backend démarré avec `--host 0.0.0.0` (pas `127.0.0.1`)
- [ ] CORS configuré avec `http://localhost:3000` dans `allow_origins`
- [ ] `.env.local` existe à la racine avec `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Next.js redémarré après modification de `.env.local`
- [ ] Frontend utilise `http://localhost:3000` (pas `https://`)
- [ ] Pas d'erreur CORS dans la console du navigateur
- [ ] Les ports 8000 et 3000 ne sont pas bloqués par firewall

**Si tous les points sont cochés et ça ne fonctionne toujours pas:**
1. Exécuter `python backend/test_api_connection.py`
2. Copier-coller les logs complets
3. Vérifier les logs du backend au moment de la requête qui échoue

