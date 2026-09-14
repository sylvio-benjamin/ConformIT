"""
Script de diagnostic pour tester la communication entre frontend et backend.
Exécutez ce script pour vérifier si l'API backend répond correctement.
"""

import requests
import sys
import json
from urllib.parse import urljoin

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test 1: Vérifie si le serveur backend répond à la racine."""
    print("=" * 60)
    print("TEST 1: Vérification du serveur backend")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"✅ Serveur backend accessible sur {API_BASE_URL}")
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ ERREUR: Impossible de se connecter à {API_BASE_URL}")
        print(f"   Vérifiez que le serveur backend est démarré:")
        print(f"   cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ ERREUR: Timeout lors de la connexion à {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_health_endpoint():
    """Test 2: Vérifie l'endpoint /health."""
    print("\n" + "=" * 60)
    print("TEST 2: Endpoint /health")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"✅ Endpoint /health accessible")
        print(f"   Status: {response.status_code}")
        print(f"   Réponse: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_cors_configuration():
    """Test 3: Vérifie la configuration CORS."""
    print("\n" + "=" * 60)
    print("TEST 3: Configuration CORS")
    print("=" * 60)
    try:
        headers = {
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        response = requests.options(f"{API_BASE_URL}/", headers=headers, timeout=5)
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
        }
        
        print(f"✅ CORS configuré")
        for key, value in cors_headers.items():
            print(f"   {key}: {value}")
        
        # Vérifier si l'origin du frontend est autorisé
        if cors_headers["Access-Control-Allow-Origin"] in [FRONTEND_URL, "*"]:
            print(f"   ✅ L'origine {FRONTEND_URL} est autorisée")
        else:
            print(f"   ⚠️  L'origine {FRONTEND_URL} pourrait ne pas être autorisée")
            print(f"      Origine autorisée: {cors_headers['Access-Control-Allow-Origin']}")
        
        return True
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_cors_preflight():
    """Test 4: Test une requête CORS préflight complète."""
    print("\n" + "=" * 60)
    print("TEST 4: Requête CORS préflight (OPTIONS)")
    print("=" * 60)
    try:
        headers = {
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        response = requests.options(f"{API_BASE_URL}/api/analyses", headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Requête OPTIONS acceptée")
        else:
            print(f"⚠️  Status inattendu: {response.status_code}")
        
        print("\nHeaders de réponse CORS:")
        for key, value in response.headers.items():
            if "access-control" in key.lower() or "cors" in key.lower():
                print(f"   {key}: {value}")
        
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_actual_request():
    """Test 5: Test une requête réelle avec CORS."""
    print("\n" + "=" * 60)
    print("TEST 5: Requête réelle avec CORS")
    print("=" * 60)
    try:
        headers = {
            "Origin": FRONTEND_URL,
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{API_BASE_URL}/api/analyses",
            headers=headers,
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        # Vérifier les headers CORS dans la réponse
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        if cors_origin:
            print(f"✅ Headers CORS présents dans la réponse")
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"⚠️  Pas de header Access-Control-Allow-Origin dans la réponse")
        
        # Le status peut être 404 (utilisateur non trouvé) ou 200, c'est OK
        if response.status_code in [200, 404]:
            print(f"✅ L'endpoint répond (status {response.status_code})")
            if response.status_code == 404:
                print("   (404 est normal si l'utilisateur n'existe pas)")
        else:
            print(f"⚠️  Status inattendu: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def check_ports():
    """Test 6: Vérifie si les ports sont ouverts."""
    print("\n" + "=" * 60)
    print("TEST 6: Vérification des ports")
    print("=" * 60)
    import socket
    
    def is_port_open(host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    backend_port = 8000
    frontend_port = 3000
    
    if is_port_open("localhost", backend_port):
        print(f"✅ Port {backend_port} (backend) est ouvert")
    else:
        print(f"❌ Port {backend_port} (backend) n'est pas ouvert")
        print(f"   Le backend n'est probablement pas démarré")
    
    if is_port_open("localhost", frontend_port):
        print(f"✅ Port {frontend_port} (frontend) est ouvert")
    else:
        print(f"⚠️  Port {frontend_port} (frontend) n'est pas ouvert")
        print(f"   (Normal si le frontend n'est pas démarré)")

def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("DIAGNOSTIC DE COMMUNICATION FRONTEND-BACKEND")
    print("=" * 60)
    print(f"\nBackend URL: {API_BASE_URL}")
    print(f"Frontend URL: {FRONTEND_URL}\n")
    
    results = []
    results.append(("Backend Health", test_backend_health()))
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("CORS Configuration", test_cors_configuration()))
    results.append(("CORS Preflight", test_cors_preflight()))
    results.append(("Actual Request", test_actual_request()))
    check_ports()
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    failed = [name for name, result in results if not result]
    if failed:
        print(f"\n⚠️  {len(failed)} test(s) ont échoué")
        return 1
    else:
        print("\n✅ Tous les tests ont réussi !")
        return 0

if __name__ == "__main__":
    sys.exit(main())

