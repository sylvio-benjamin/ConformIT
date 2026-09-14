"""
Utilitaires pour l'application avec optimisations async et performance.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache
import aiofiles
import aiofiles.os


class AuditService:
    """Service pour gérer les audits avec support async."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.audits_dir = self.base_dir / "audits"
        self.audits_dir.mkdir(exist_ok=True)
    
    def enregistrer_audit_json(self, slug: str, infos: Dict[str, Any]) -> bool:
        """
        Enregistre les données d'audit dans un fichier JSON (synchrone).
        
        Args:
            slug: Identifiant unique de l'audit
            infos: Données à sauvegarder
            
        Returns:
            True si succès, False sinon
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(infos, f, indent=2, ensure_ascii=False)
            print(f"✅ Audit sauvegardé dans {chemin}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement de l'audit : {e}")
            return False
    
    async def enregistrer_audit_json_async(self, slug: str, infos: Dict[str, Any]) -> bool:
        """
        Enregistre les données d'audit dans un fichier JSON (asynchrone).
        
        Args:
            slug: Identifiant unique de l'audit
            infos: Données à sauvegarder
            
        Returns:
            True si succès, False sinon
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            async with aiofiles.open(chemin, "w", encoding="utf-8") as f:
                await f.write(json.dumps(infos, indent=2, ensure_ascii=False))
            print(f"✅ Audit sauvegardé dans {chemin}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement de l'audit : {e}")
            return False
    
    @lru_cache(maxsize=200)
    def charger_audit_json(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Charge un audit depuis un fichier JSON (avec cache).
        
        Args:
            slug: Identifiant unique de l'audit
            
        Returns:
            Données de l'audit ou None si non trouvé
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            if not chemin.exists():
                return None
            
            with open(chemin, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'audit : {e}")
            return None
    
    async def charger_audit_json_async(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Charge un audit depuis un fichier JSON (asynchrone).
        
        Args:
            slug: Identifiant unique de l'audit
            
        Returns:
            Données de l'audit ou None si non trouvé
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            if not await aiofiles.os.path.exists(chemin):
                return None
            
            async with aiofiles.open(chemin, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'audit : {e}")
            return None
    
    def supprimer_audit(self, slug: str) -> bool:
        """
        Supprime un fichier d'audit.
        
        Args:
            slug: Identifiant unique de l'audit
            
        Returns:
            True si succès, False sinon
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            if chemin.exists():
                chemin.unlink()
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur lors de la suppression de l'audit : {e}")
            return False
    
    async def supprimer_audit_async(self, slug: str) -> bool:
        """
        Supprime un fichier d'audit (asynchrone).
        
        Args:
            slug: Identifiant unique de l'audit
            
        Returns:
            True si succès, False sinon
        """
        try:
            chemin = self.audits_dir / f"{slug}.json"
            if await aiofiles.os.path.exists(chemin):
                await aiofiles.os.remove(chemin)
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur lors de la suppression de l'audit : {e}")
            return False


# Instance globale du service
audit_service = AuditService()


# Fonctions de compatibilité (ancienne API)
def enregistrer_audit_json(slug: str, infos: Dict[str, Any]) -> None:
    """
    Fonction de compatibilité pour l'ancienne API.
    
    Args:
        slug: Identifiant unique de l'audit
        infos: Données à sauvegarder
    """
    audit_service.enregistrer_audit_json(slug, infos)


# =====================================================
# Utilitaires de chiffrement pour les credentials API
# =====================================================

import base64
from cryptography.fernet import Fernet
import logging

_crypto_logger = logging.getLogger(__name__)

def get_encryption_key() -> bytes:
    from app import config as app_config

    key = app_config.ENCRYPTION_KEY
    if not key:
        if not app_config.IS_DEVELOPMENT:
            raise RuntimeError("ENCRYPTION_KEY absente : refus de chiffrer")
        key = Fernet.generate_key().decode()
        app_config.ENCRYPTION_KEY = key
        app_config.ENCRYPTION_KEY_EPHEMERAL = True
        _crypto_logger.warning("Clé de chiffrement éphémère générée (dev, non persistante)")
    try:
        Fernet(key.encode())
    except Exception as exc:
        raise RuntimeError("ENCRYPTION_KEY invalide") from exc
    return key.encode()


def encrypt_value(value: str) -> str:
    """
    Chiffre une valeur avec Fernet.
    
    Args:
        value: Valeur à chiffrer
        
    Returns:
        Valeur chiffrée en base64
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        _crypto_logger.error(f"Erreur lors du chiffrement: {e}")
        raise Exception(f"Erreur de chiffrement: {str(e)}")


def decrypt_value(encrypted_value: str) -> str:
    """
    Déchiffre une valeur avec Fernet.
    
    Args:
        encrypted_value: Valeur chiffrée en base64
        
    Returns:
        Valeur déchiffrée
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        _crypto_logger.error(f"Erreur lors du déchiffrement: {e}")
        raise Exception(f"Erreur de déchiffrement: {str(e)}")