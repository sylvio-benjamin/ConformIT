# Diagnostic de Communication Frontend-Backend

## Checklist de Vérification Rapide

### ✅ 1. Vérifier que le backend répond à la racine

**Test rapide dans le navigateur:**
```
http://localhost:8000/
```

**Ou via curl dans le terminal:**
```bash
curl http://localhost:8000/
```

**Résultat attendu:** 
```json
{
  "message": "SAE Audit API - Serveur opérationnel",
  "version": "2.0.0",
  "status": "online"
}
```

**Si ça ne fonctionne pas:**
- Le backend n'est pas démarré → Voir étape 2
- Erreur de connexion → Vérifier que le port 8000 n'est pas utilisé par autre chose
- Timeout → Vérifier le firewall/antivirus

---

### ✅ 2. Vérifier que le backend est démarré

**Commande pour démarrer le backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Vérification:**
- Vous devriez voir: `INFO: Application startup complete.`
- Le message: `[OK] Base de données PostgreSQL initialisée`
- Le serveur doit écouter sur `0.0.0.0:8000` (pas seulement 127.0.0.1)

**Attention:** Si vous utilisez `--host 127.0.0.1` au lieu de `--host 0.0.0.0`, le backend ne sera accessible que depuis localhost, ce qui peut causer des problèmes CORS.

---

### ✅ 3. Vérifier la configuration CORS

**Dans le terminal (depuis le dossier backend):**
```bash
python test_api_connection.py
```

**Ou vérification manuelle:**

Testez une requête OPTIONS depuis le terminal:
```bash
curl -X OPTIONS http://localhost:8000/api/analyses \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Vérifiez dans les headers de réponse:**
- `Access-Control-Allow-Origin: http://localhost:3000` (ou `*`)
- `Access-Control-Allow-Methods: GET, POST, PUT, ...`
- `Access-Control-Allow-Headers: *`

**Si CORS n'est pas configuré correctement:**
- Vérifiez `backend/app/main.py` lignes 94-101
- Assurez-vous que `http://localhost:3000` est dans `allow_origins`
- Redémarrez le backend après modification

---

### ✅ 4. Vérifier l'URL utilisée par le frontend

**Dans le navigateur (Console développeur):**
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
```

**Ou vérifiez dans les fichiers:**
- `src/services/api.js` ligne 6
- `src/utils/syncUserToPostgres.js` ligne 8
- `src/lib/apiConfig.js` (si existe)

**Vérifiez aussi:**
- Dans `.env.local` à la racine du projet, vous devez avoir:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Important:** 
- Les variables d'environnement Next.js qui commencent par `NEXT_PUBLIC_` sont accessibles côté client
- Après modification de `.env.local`, **redémarrez le serveur Next.js** (pas juste le rafraîchissement)
- Les variables sans `NEXT_PUBLIC_` ne sont accessibles que côté serveur

---

### ✅ 5. Vérifier le protocole HTTP/HTTPS

**Problème de contenu mixte:**

Si votre frontend est sur `https://` et votre backend sur `http://`, vous aurez une erreur:
```
Mixed Content: The page was loaded over HTTPS, but requested an insecure resource
```

**Solutions:**
1. Utiliser HTTP pour les deux en développement: `http://localhost:3000` et `http://localhost:8000`
2. Ou configurer HTTPS pour le backend aussi

**Vérification:**
- Frontend URL doit être: `http://localhost:3000` (pas `https://`)
- Backend URL doit être: `http://localhost:8000` (pas `https://`)

---

### ✅ 6. Vérifier l'erreur exacte dans le navigateur

**Ouvrez la Console développeur (F12) et onglet Network:**

1. **Erreur CORS:**
   ```
   Access to fetch at 'http://localhost:8000/api/analyses' from origin 'http://localhost:3000' 
   has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
   ```
   → **Solution:** Vérifier la configuration CORS (étape 3)

2. **Erreur de connexion:**
   ```
   Failed to fetch
   TypeError: Failed to fetch
   ```
   → **Solutions possibles:**
   - Backend non démarré (étape 2)
   - Mauvaise URL (étape 4)
   - Port bloqué par firewall

3. **Erreur 404:**
   ```
   GET http://localhost:8000/api/analyses 404 (Not Found)
   ```
   → **Solution:** Vérifier que le route est bien montée dans `app.main.py`

4. **Erreur 500:**
   ```
   GET http://localhost:8000/api/analyses 500 (Internal Server Error)
   ```
   → **Solution:** Vérifier les logs du backend pour voir l'erreur exacte

---

### ✅ 7. Test rapide depuis le navigateur

**Ouvrez la console développeur (F12) et exécutez:**

```javascript
// Test 1: Vérifier que l'API répond
fetch('http://localhost:8000/')
  .then(r => r.json())
  .then(d => console.log('✅ Backend OK:', d))
  .catch(e => console.error('❌ Backend inaccessible:', e))

// Test 2: Test avec CORS
fetch('http://localhost:8000/api/analyses?firebase_uid=test123')
  .then(r => {
    console.log('Status:', r.status);
    return r.json();
  })
  .then(d => console.log('✅ API OK:', d))
  .catch(e => console.error('❌ API erreur:', e))
```

---

### ✅ 8. Vérifier les variables d'environnement Next.js

**Problème courant:** Les variables d'environnement ne sont pas chargées.

**Solution:**
1. Créez/modifiez `.env.local` à la racine du projet (même niveau que `package.json`)
2. Ajoutez:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
3. **Redémarrez complètement le serveur Next.js** (Ctrl+C puis `npm run dev`)

**Vérification que la variable est chargée:**
```javascript
// Dans la console du navigateur
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)
```

---

## Script de Diagnostic Automatique

Exécutez le script Python de diagnostic:

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

## Solutions Rapides par Type d'Erreur

### Erreur: "Failed to fetch" / "NetworkError"
1. Vérifiez que le backend est démarré (port 8000)
2. Vérifiez l'URL dans le frontend
3. Vérifiez que les deux utilisent HTTP (pas HTTPS)

### Erreur: CORS blocked
1. Vérifiez `backend/app/main.py` CORS config
2. Assurez-vous que `http://localhost:3000` est dans `allow_origins`
3. Redémarrez le backend

### Erreur: 404 Not Found
1. Vérifiez que les routes sont bien montées dans `app.main.py`
2. Vérifiez que l'URL dans le frontend correspond à la route backend

### Erreur: Mixed Content
1. Utilisez HTTP pour les deux en développement
2. Ou configurez HTTPS pour le backend

---

## Configuration Recommandée pour le Développement

**Backend (`backend/app/main.py`):**
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

**Frontend (`.env.local` à la racine):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Commandes de démarrage:**
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
npm run dev
```

