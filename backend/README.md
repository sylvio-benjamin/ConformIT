# SAE Backend - API d'Audit d'Entreprises

API FastAPI pour l'analyse et l'audit automatisé de documents d'entreprises.

## 🚀 Installation

### Prérequis

- Python 3.11 ou 3.12 (recommandé)
- pip
- Un compte Firebase (optionnel)
- Un compte Stripe (pour les fonctionnalités de paiement)

### Installation automatique

#### Windows (PowerShell)
```powershell
cd backend
.\setup.ps1
```

#### Linux/macOS
```bash
cd backend
chmod +x setup.sh
./setup.sh
```

### Installation manuelle

1. Créer un environnement virtuel:
```bash
python -m venv venv
```

2. Activer l'environnement virtuel:
   - Windows: `.\venv\Scripts\Activate.ps1`
   - Linux/macOS: `source venv/bin/activate`

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Créer les dossiers nécessaires:
```bash
mkdir -p uploads reponses audits pdfs documents
```

## ⚙️ Configuration

### Fichier .env.local

Créez un fichier `.env.local` à la racine du projet (un niveau au-dessus de `backend/`) avec:

```env
# Configuration Stripe
STRIPE_SECRET_KEY=sk_test_votre_clé_stripe
STRIPE_WEBHOOK_SECRET=whsec_votre_secret_webhook

# URL du frontend
FRONTEND_URL=http://localhost:3000
```

## 🏃 Lancement

### Mode développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mode production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentation

Une fois le serveur lancé, accédez à:

- **Documentation interactive (Swagger)**: http://localhost:8000/docs
- **Documentation alternative (ReDoc)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## 🏗️ Structure du projet

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée principal
│   ├── analyse.py           # Routes d'analyse
│   ├── parser.py            # Parsing de documents
│   ├── stripe_routes.py     # Routes de paiement
│   ├── stripe_webhook.py    # Webhooks Stripe
│   ├── utils.py             # Utilitaires
│   └── ...                  # État des jobs : table analysis_jobs (plus de dict process)
├── uploads/                 # PDFs uploadés
├── reponses/               # Fichiers Excel de réponses
├── audits/                 # Résultats d'audit (JSON)
├── pdfs/                   # PDFs générés
├── documents/              # Templates
├── requirements.txt        # Dépendances Python
├── setup.sh               # Script d'installation (Linux/macOS)
├── setup.ps1              # Script d'installation (Windows)
└── README.md              # Ce fichier
```

## 🔧 Endpoints principaux

### Routes système
- `GET /` - Vérification de l'API
- `GET /health` - Health check avec statut des services

### Routes d'analyse
- `POST /analyser/` - Analyser un document PDF
- `POST /analyser-url/` - Analyser un document depuis une URL
- `GET /resultat/{slug}` - Récupérer le résultat d'une analyse
- `PATCH /modifier-analyse/{slug}` - Modifier une analyse
- `POST /annuler-analyse/{slug}` - Annuler une analyse

### Routes de téléchargement
- `GET /telecharger-pdf/{slug}` - Télécharger le rapport PDF
- `GET /telecharger-excel/{slug}` - Télécharger le fichier Excel

### Routes de paiement (Stripe)
- `POST /create-checkout-session/` - Créer une session de paiement
- `POST /stripe/webhook` - Webhook Stripe

## 🐛 Dépannage

### Erreur: Module 'app' has no attribute 'main'

Assurez-vous d'être dans le dossier `backend/` avant de lancer uvicorn.

## 📝 Notes importantes

- **Python 3.13**: Certains packages peuvent ne pas être compatibles. Utilisez Python 3.11 ou 3.12.
- **Excel**: Plus de dépendance à Excel/xlwings - Tous les calculs sont en Python pur.
- **CORS**: Actuellement configuré pour `http://localhost:3000`. Ajustez dans `main.py` si nécessaire.

## 🔒 Sécurité

- Ne commitez jamais `.env` / `.env.local`
- Auth runtime : JWT + cookies. Plus de clé maître `API_KEY_ATTENDUE`
- Utilisez des clés Stripe de test en développement

## 📄 Licence

Projet SAE 4.01

