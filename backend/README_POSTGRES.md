# Configuration PostgreSQL pour les modules GRC

Ce projet utilise **PostgreSQL** pour les modules GRC (Gestion des Risques et de la Conformité) tout en conservant **Firebase** pour l'authentification et les données existantes.

## Configuration

### 1. Variables d'environnement

Ajoutez les variables suivantes dans votre fichier `.env.local` :

```env
# Configuration PostgreSQL (pour les modules GRC)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=grc_db

# URL de connexion PostgreSQL complète (optionnel - sera construite automatiquement si non fourni)
# POSTGRES_URL=postgresql+psycopg2://postgres:password@localhost:5432/grc_db
```

### 2. Créer la base de données

Exécutez le script SQL pour créer toutes les tables :

```bash
# Depuis pgAdmin ou psql
psql -U postgres -d grc_db -f database/schema.sql
```

Ou créez manuellement la base de données :

```sql
CREATE DATABASE grc_db;
```

Puis exécutez le script `database/schema.sql`.

### 3. Initialisation automatique

L'application initialise automatiquement la base de données au démarrage. Si les tables n'existent pas, elles seront créées automatiquement.

## Architecture

### Base de données PostgreSQL
- Utilisée pour : **Modules GRC** (Risques, Contrôles, KRIs, Incidents, Conformité, Rapports, Intégrations)
- Avantages : Relations complexes, requêtes SQL avancées, transactions ACID, scalabilité

### Firebase Realtime Database
- Utilisée pour : **Authentification**, **Analyses existantes**, **Données utilisateur**
- Avantages : Temps réel, simplicité, pas de configuration serveur

## Structure des modules

```
backend/app/
├── database.py          # Connexion PostgreSQL avec SQLAlchemy
├── models/              # Modèles SQLAlchemy
│   ├── organizations.py
│   ├── risks.py
│   ├── controls.py
│   ├── kris.py
│   ├── incidents.py
│   ├── compliance.py
│   ├── integrations.py
│   ├── reports.py
│   └── audit.py
└── api/                 # API REST pour PostgreSQL
    ├── risks.py
    ├── controls.py
    ├── kris.py
    ├── incidents.py
    ├── compliance.py
    └── ...
```

## Utilisation

### Dans les API FastAPI

Utilisez la dépendance `get_db` pour obtenir une session PostgreSQL :

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.risks import Risk

@router.get("/risks")
async def list_risks(db: Session = Depends(get_db)):
    risks = db.query(Risk).all()
    return risks
```

### En dehors de FastAPI

Utilisez le context manager `get_db_context` :

```python
from app.database import get_db_context
from app.models.risks import Risk

with get_db_context() as db:
    risks = db.query(Risk).all()
```

## Migration des données Firebase vers PostgreSQL

Pour migrer les données existantes de Firebase vers PostgreSQL, créez un script de migration personnalisé selon vos besoins spécifiques.

## Dépendances

Les dépendances PostgreSQL sont déjà ajoutées dans `requirements.txt` :

```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
```

Installez-les avec :

```bash
pip install -r requirements.txt
```

## Support

En cas de problème de connexion PostgreSQL, vérifiez :
1. Que PostgreSQL est démarré
2. Que les identifiants dans `.env.local` sont corrects
3. Que la base de données `grc_db` existe
4. Les logs de l'application au démarrage

