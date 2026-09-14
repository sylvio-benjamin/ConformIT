"""
Script de test pour vérifier la communication frontend/backend.
Exécute toutes les vérifications nécessaires.
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_KEY = "0b43FP8v3aQ1jAzvqb6ThYhdJ5MGunhC"  # À adapter selon votre .env.local

def test_backend_health():
    """Étape 1 : Vérifier que le backend tourne"""
    print("=" * 60)
    print("ÉTAPE 1 : Vérification du backend")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend accessible sur {BACKEND_URL}")
            print(f"   Réponse: {response.json()}")
            return True
        else:
            print(f"❌ Backend répond mais avec erreur {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {BACKEND_URL}")
        print("   → Vérifiez que le serveur est démarré avec: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_endpoint_root():
    """Test de l'endpoint racine"""
    print("\n" + "=" * 60)
    print("Test endpoint racine (/)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Endpoint racine accessible")
            print(f"   Réponse: {response.json()}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_cors():
    """Étape 3 : Vérifier la configuration CORS"""
    print("\n" + "=" * 60)
    print("ÉTAPE 3 : Vérification CORS")
    print("=" * 60)
    
    try:
        # Test OPTIONS (preflight)
        headers = {
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        response = requests.options(f"{BACKEND_URL}/health", headers=headers, timeout=5)
        
        cors_headers = {
            "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
            "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
            "access-control-allow-headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        
        print(f"✅ Requête OPTIONS réussie (status {response.status_code})")
        print(f"   Headers CORS:")
        for key, value in cors_headers.items():
            if value:
                print(f"     {key}: {value}")
            else:
                print(f"     {key}: ❌ MANQUANT")
        
        if cors_headers["access-control-allow-origin"]:
            return True
        else:
            print("❌ Headers CORS manquants")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test CORS: {e}")
        return False


def test_endpoint_resultat():
    """Étape 2 & 4 : Tester l'endpoint /resultat/{slug}"""
    print("\n" + "=" * 60)
    print("ÉTAPE 2 & 4 : Test endpoint /resultat/{slug}")
    print("=" * 60)
    
    # Chercher un slug existant dans ./audits/
    audits_dir = Path("./audits")
    if not audits_dir.exists():
        print("⚠️  Dossier ./audits/ non trouvé")
        print("   → Créez une analyse d'abord pour tester")
        return None
    
    json_files = list(audits_dir.glob("*.json"))
    if not json_files:
        print("⚠️  Aucun fichier JSON trouvé dans ./audits/")
        print("   → Créez une analyse d'abord pour tester")
        return None
    
    # Prendre le premier fichier
    test_slug = json_files[0].stem
    print(f"📄 Test avec slug: {test_slug}")
    
    # Test SANS header Authorization
    print("\n1. Test SANS header Authorization:")
    try:
        response = requests.get(f"{BACKEND_URL}/resultat/{test_slug}", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Endpoint accessible sans auth (peut être normal si /resultat/ n'exige pas d'auth)")
            data = response.json()
            print(f"   Réponse: {json.dumps(data, indent=2)[:200]}...")
        elif response.status_code == 401:
            print("   ⚠️  401 Unauthorized - L'endpoint nécessite une clé API")
        else:
            print(f"   ⚠️  Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test AVEC header Authorization
    print("\n2. Test AVEC header Authorization:")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        response = requests.get(f"{BACKEND_URL}/resultat/{test_slug}", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Endpoint accessible avec auth")
            data = response.json()
            # Vérifier les NaN
            data_str = json.dumps(data, indent=2)
            if "nan" in data_str.lower() or "NaN" in data_str:
                print("   ⚠️  ATTENTION: Valeurs NaN détectées dans la réponse!")
            else:
                print("   ✅ Pas de valeurs NaN dans la réponse")
            print(f"   Réponse: {data_str[:300]}...")
            return True
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized - Clé API incorrecte")
            print(f"   → Vérifiez que API_KEY_ATTENDUE dans .env.local correspond à: {API_KEY[:10]}...")
            return False
        else:
            print(f"   ⚠️  Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def test_endpoint_resultat_inexistant():
    """Test avec un slug inexistant"""
    print("\n" + "=" * 60)
    print("Test avec slug inexistant")
    print("=" * 60)
    
    test_slug = "slug_inexistant_test_12345"
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        response = requests.get(f"{BACKEND_URL}/resultat/{test_slug}", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("terminee") == False or data.get("analyseTerminee") == False:
                print("✅ Réponse correcte pour slug inexistant")
                return True
            else:
                print("⚠️  Réponse inattendue")
                return False
        else:
            print(f"⚠️  Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécute tous les tests"""
    print("\n" + "=" * 60)
    print("TESTS DE COMMUNICATION FRONTEND ↔ BACKEND")
    print("=" * 60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"API Key: {API_KEY[:10]}...\n")
    
    results = {
        "backend_health": test_backend_health(),
        "endpoint_root": test_endpoint_root(),
        "cors": test_cors(),
        "resultat": test_endpoint_resultat(),
        "resultat_inexistant": test_endpoint_resultat_inexistant(),
    }
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}")
        elif result is False:
            print(f"❌ {test_name}")
        else:
            print(f"⚠️  {test_name} (non testé)")
    
    print("\n" + "=" * 60)
    print("RECOMMANDATIONS")
    print("=" * 60)
    
    if not results["backend_health"]:
        print("1. Démarrez le backend: uvicorn app.main:app --reload")
    
    if not results["cors"]:
        print("2. Vérifiez la configuration CORS dans main.py")
    
    if results["resultat"] is False:
        print("3. Vérifiez la clé API dans .env.local")
        print("4. Vérifiez que l'endpoint /resultat/{slug} fonctionne")
    
    print("\n✅ Tests terminés!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)

