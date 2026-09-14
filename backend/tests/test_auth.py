"""
Tests unitaires pour le module d'authentification.
"""

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.auth import (
    get_api_key_from_header,
    verify_api_key,
    verify_api_key_dependency,
    get_api_key_error_message
)
class TestGetAPIKeyFromHeader:
    """Tests pour l'extraction de la clé API depuis le header."""
    
    def test_extract_valid_key(self):
        """Test avec un header valide."""
        header = "Bearer 123456SECRET"
        key = get_api_key_from_header(header)
        assert key == "123456SECRET"
    
    def test_extract_key_with_spaces(self):
        """Test avec des espaces."""
        header = "Bearer  123456SECRET  "
        key = get_api_key_from_header(header)
        assert key == "123456SECRET"
    
    def test_no_bearer_prefix(self):
        """Test sans préfixe Bearer."""
        header = "123456SECRET"
        key = get_api_key_from_header(header)
        assert key is None
    
    def test_empty_header(self):
        """Test avec header vide."""
        key = get_api_key_from_header(None)
        assert key is None
    
    def test_malformed_header(self):
        """Test avec header malformé."""
        header = "Bearer"
        key = get_api_key_from_header(header)
        assert key is None or key == ""


class TestVerifyAPIKey:
    """Tests pour la vérification de la clé API."""
    
    def test_shared_master_key_is_rejected(self):
        assert verify_api_key("legacy-shared-master-key") is False

    def test_verify_incorrect_key(self):
        """Test avec une clé incorrecte."""
        result = verify_api_key("wrong_key")
        assert result is False
    
    def test_verify_empty_key(self):
        """Test avec une clé vide."""
        result = verify_api_key(None)
        assert result is False
    
class TestGetAPIKeyErrorMessage:
    """Tests pour les messages d'erreur."""

    def test_error_key_missing(self):
        """Test quand la clé n'est pas fournie."""
        message = get_api_key_error_message(api_key_provided=False, api_key_valid=False)
        assert "manquante" in message.lower() or "missing" in message.lower()
    
    def test_error_key_invalid(self):
        """Test quand la clé est invalide."""
        message = get_api_key_error_message(api_key_provided=True, api_key_valid=False)
        assert "invalide" in message.lower() or "invalid" in message.lower()


class TestVerifyAPIKeyDependency:
    """Tests pour la dépendance FastAPI."""
    
    @pytest.fixture
    def app(self):
        """Créer une app FastAPI de test."""
        app = FastAPI()
        
        @app.post("/test")
        async def test_endpoint(api_key: str = Depends(verify_api_key_dependency)):
            return {"status": "ok", "api_key": "validated"}
        
        return app
    
    def test_missing_key(self, app):
        """Test sans clé."""
        client = TestClient(app)
        response = client.post("/test")
        assert response.status_code == 401
        assert "error" in response.json()["detail"]
    
    def test_invalid_key(self, app):
        """Test avec une clé invalide."""
        client = TestClient(app)
        response = client.post(
            "/test",
            headers={"Authorization": "Bearer wrong_key"}
        )
        assert response.status_code == 401
        assert "error" in response.json()["detail"]
    
    def test_malformed_header(self, app):
        """Test avec header malformé."""
        client = TestClient(app)
        response = client.post(
            "/test",
            headers={"Authorization": "wrong_format"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

