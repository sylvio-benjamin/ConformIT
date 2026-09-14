"""
Tests unitaires pour le module utils.py.
"""

import pytest
import tempfile
import os
from app.utils import AuditService, audit_service, enregistrer_audit_json


class TestAuditService:
    """Tests pour le service d'audit."""
    
    def test_enregistrer_audit_json(self, tmp_path):
        """Test de l'enregistrement d'audit."""
        service = AuditService(base_dir=str(tmp_path))
        slug = "test_audit"
        infos = {"nom": "Test", "score": 10}
        
        result = service.enregistrer_audit_json(slug, infos)
        assert result is True
        
        # Vérifier que le fichier existe
        audit_file = tmp_path / "audits" / f"{slug}.json"
        assert audit_file.exists()
    
    @pytest.mark.asyncio
    async def test_enregistrer_audit_json_async(self, tmp_path):
        """Test de l'enregistrement async d'audit."""
        service = AuditService(base_dir=str(tmp_path))
        slug = "test_audit_async"
        infos = {"nom": "Test Async", "score": 20}
        
        result = await service.enregistrer_audit_json_async(slug, infos)
        assert result is True
        
        # Vérifier que le fichier existe
        audit_file = tmp_path / "audits" / f"{slug}.json"
        assert audit_file.exists()
    
    def test_charger_audit_json(self, tmp_path):
        """Test du chargement d'audit."""
        service = AuditService(base_dir=str(tmp_path))
        slug = "test_load"
        infos = {"nom": "Test Load", "score": 30}
        
        # Enregistrer d'abord
        service.enregistrer_audit_json(slug, infos)
        
        # Charger
        loaded = service.charger_audit_json(slug)
        assert loaded is not None
        assert loaded["nom"] == "Test Load"
        assert loaded["score"] == 30
    
    @pytest.mark.asyncio
    async def test_charger_audit_json_async(self, tmp_path):
        """Test du chargement async d'audit."""
        service = AuditService(base_dir=str(tmp_path))
        slug = "test_load_async"
        infos = {"nom": "Test Load Async", "score": 40}
        
        # Enregistrer d'abord
        await service.enregistrer_audit_json_async(slug, infos)
        
        # Charger
        loaded = await service.charger_audit_json_async(slug)
        assert loaded is not None
        assert loaded["nom"] == "Test Load Async"
        assert loaded["score"] == 40
    
    def test_charger_audit_inexistant(self, tmp_path):
        """Test du chargement d'un audit inexistant."""
        service = AuditService(base_dir=str(tmp_path))
        loaded = service.charger_audit_json("inexistant")
        assert loaded is None
    
    def test_supprimer_audit(self, tmp_path):
        """Test de la suppression d'audit."""
        service = AuditService(base_dir=str(tmp_path))
        slug = "test_delete"
        infos = {"nom": "Test Delete"}
        
        # Enregistrer
        service.enregistrer_audit_json(slug, infos)
        
        # Supprimer
        result = service.supprimer_audit(slug)
        assert result is True
        
        # Vérifier que le fichier n'existe plus
        audit_file = tmp_path / "audits" / f"{slug}.json"
        assert not audit_file.exists()


class TestCompatibilityFunctions:
    """Tests pour les fonctions de compatibilité."""
    
    def test_enregistrer_audit_json_compat(self, tmp_path):
        """Test de la fonction de compatibilité."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            enregistrer_audit_json("compat_test", {"test": "data"})
            assert (tmp_path / "audits" / "compat_test.json").exists()
        finally:
            os.chdir(original_cwd)

