# Services d'Intégration - APIs Externes

Ce dossier contient les services pour interagir avec les APIs externes :
- **Infogreffe** : Données d'entreprises françaises
- **INSEE** : Données statistiques et économiques
- **Dun & Bradstreet** : Données financières et de crédit
- **PowerBI** : Génération de dashboards et rapports

## Configuration

### Variables d'environnement

Pour activer le chiffrement des credentials, ajoutez dans `.env.local` :

```env
# Clé de chiffrement (générer avec: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=votre_clé_de_chiffrement_base64
```

### Obtenir les credentials

#### Infogreffe
1. Créer un compte sur https://www.infogreffe.fr/
2. Souscrire à l'API Infogreffe
3. Récupérer votre clé API

#### INSEE
1. Créer un compte sur https://api.insee.fr/
2. Demander un accès à l'API Sirene
3. Récupérer votre clé API (Consumer Key et Consumer Secret)

#### Dun & Bradstreet
1. Contacter Dun & Bradstreet pour un accès API
2. Récupérer votre clé API

#### PowerBI
1. Créer une application Azure AD
2. Configurer les permissions PowerBI
3. Récupérer Client ID, Client Secret et Tenant ID

## Utilisation

Les services sont automatiquement utilisés par l'API backend lors de la connexion d'une intégration.

### Test manuel

```python
from app.services.integrations import InfogreffeService, INSEEService

# Test Infogreffe
infogreffe = InfogreffeService(api_key="votre_cle")
result = infogreffe.search_company("nom entreprise")
print(result)

# Test INSEE
insee = INSEEService(api_key="votre_cle")
result = insee.search_siren("123456789")
print(result)
```

## Notes

- Les credentials sont automatiquement chiffrés lors du stockage dans PostgreSQL
- Les services gèrent les erreurs de connexion et retournent des messages explicites
- Les tests de connexion vérifient la validité des credentials avant l'activation

