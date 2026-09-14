"""
Module d'authentification centralisé pour l'API SAE Audit.

Fournit :
- Dépendance FastAPI réutilisable pour vérifier la clé API
- Middleware de logging des tentatives d'authentification
- Messages d'erreur clairs et sécurisés
"""

import logging
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.api_keys import APIKey

# Configuration du logger
logger = logging.getLogger(__name__)

# Schéma de sécurité HTTP Bearer
security = HTTPBearer(auto_error=False)


class APIKeyError(Exception):
    """Exception personnalisée pour les erreurs de clé API."""
    pass


def get_api_key_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extrait la clé API du header Authorization.
    
    Args:
        authorization: Header Authorization (format: "Bearer {key}")
        
    Returns:
        Clé API extraite ou None
    """
    if not authorization:
        logger.debug("Header Authorization manquant")
        return None
    
    # Logger le header reçu (partiellement masqué pour debug)
    logger.debug(f"Header Authorization reçu: {authorization[:30]}..." if len(authorization) > 30 else authorization)
    
    # Vérifier le format "Bearer {key}"
    if not authorization.startswith("Bearer "):
        logger.warning(f"Format incorrect: le header doit commencer par 'Bearer ' (reçu: {authorization[:20]}...)")
        return None
    
    # Extraire la clé
    try:
        api_key = authorization.split("Bearer ", 1)[1].strip()
        if api_key:
            logger.debug(f"Clé extraite: {len(api_key)} caractères")
            return api_key
        else:
            logger.warning("Clé vide après 'Bearer '")
            return None
    except (IndexError, AttributeError) as e:
        logger.error(f"Erreur lors de l'extraction de la clé: {e}")
        return None


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    Vérifie si la clé API fournie est valide.
    
    Args:
        api_key: Clé API à vérifier
        
    Returns:
        True si la clé est valide, False sinon
    """
    if not api_key:
        return False

    # Vérifier dans les clés dynamiques (table api_keys) — plus de clé maître partagée.
    hashed = hashlib.sha256(api_key.encode()).hexdigest()
    
    try:
        from sqlalchemy.orm import joinedload
        
        db: Session = SessionLocal()
        try:
            # Charger l'APIKey avec la relation user (joinedload pour éviter les requêtes N+1)
            api_key_obj = db.query(APIKey).options(
                joinedload(APIKey.user)
            ).filter(
                APIKey.key_hash == hashed,
                APIKey.is_active.is_(True)
            ).first()
            
            if api_key_obj and api_key_obj.user:
                # Mettre à jour la date de dernière utilisation
                from datetime import datetime
                api_key_obj.last_used_at = datetime.now()
                db.commit()
                
                # Vérifier que l'utilisateur a le plan enterprise
                try:
                    from app.services.plan_service import PlanService
                    plan = PlanService.get_user_plan(str(api_key_obj.user.id))
                    if plan == "enterprise":
                        return True
                except Exception as exc:
                    logger.error(f"Erreur lors de la vérification du plan pour clé API dynamique: {exc}")
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"Erreur lors de la vérification de la clé API dans PostgreSQL: {exc}")

    return False


def get_api_key_error_message(api_key_provided: bool, api_key_valid: bool) -> str:
    """
    Génère un message d'erreur clair et sécurisé.
    
    Args:
        api_key_provided: Si une clé a été fournie
        api_key_valid: Si la clé est valide
        
    Returns:
        Message d'erreur approprié
    """
    if not api_key_provided:
        return (
            "Clé API manquante. "
            "Veuillez fournir le header 'Authorization: Bearer {votre_cle}'. "
            "Vérifiez votre fichier .env.local pour la clé correcte."
        )
    
    if not api_key_valid:
        return (
            "Clé API invalide ou révoquée. "
            "Si vous êtes sur le plan Business, générez une nouvelle clé depuis votre profil."
        )
    
    return "Erreur d'authentification inconnue."


def log_auth_attempt(api_key_provided: bool, api_key_valid: bool, client_ip: Optional[str] = None):
    """
    Log les tentatives d'authentification (sans exposer la clé).
    
    Args:
        api_key_provided: Si une clé a été fournie
        api_key_valid: Si la clé est valide
        client_ip: Adresse IP du client (optionnel)
    """
    ip_info = f" depuis {client_ip}" if client_ip else ""
    
    if not api_key_provided:
        logger.warning(f"Tentative d'accès sans clé API{ip_info}")
    elif not api_key_valid:
        logger.warning(f"Tentative d'accès avec clé API invalide{ip_info}")
    else:
        logger.info(f"Authentification réussie{ip_info}")


async def verify_api_key_dependency(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Dépendance FastAPI pour vérifier la clé API.
    
    Utilisation :
        @app.post("/endpoint")
        async def my_endpoint(api_key: str = Depends(verify_api_key_dependency)):
            # api_key est garanti valide ici
            ...
    
    Args:
        authorization: Header Authorization brut
        credentials: Credentials HTTP Bearer (alternative)
        
    Returns:
        Clé API validée
        
    Raises:
        HTTPException: Si la clé est manquante ou invalide
    """
    # Debug: Logger ce qui est reçu
    logger.debug(f"Authorization header reçu: {authorization[:20] + '...' if authorization and len(authorization) > 20 else authorization}")
    logger.debug(f"Credentials reçus: {credentials is not None}")
    
    # Essayer d'extraire la clé depuis le header Authorization
    api_key = get_api_key_from_header(authorization)
    
    # Si pas trouvé, essayer depuis HTTPBearer
    if not api_key and credentials:
        api_key = credentials.credentials
        logger.debug("Clé extraite depuis HTTPBearer")
    
    # Debug: Logger si la clé a été trouvée
    if api_key:
        logger.debug(f"Clé extraite: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else '***'}")
    else:
        logger.debug("Aucune clé extraite")
    
    # Vérifier la clé
    api_key_provided = api_key is not None
    api_key_valid = verify_api_key(api_key)
    
    # Logger la tentative (sans exposer la clé)
    log_auth_attempt(api_key_provided, api_key_valid)
    
    # Si la clé n'est pas valide, lever une exception
    if not api_key_valid:
        error_message = get_api_key_error_message(api_key_provided, api_key_valid)
        
        # Déterminer le code d'erreur approprié
        if not api_key_provided:
            status_code = 401
            logger.warning("Tentative d'accès sans clé API")
        else:
            status_code = 401
            logger.warning("Tentative d'accès avec clé API invalide ou révoquée")
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": error_message,
                "error_code": "API_KEY_INVALID" if api_key_provided else "API_KEY_MISSING"
            }
        )
    
    # Retourner la clé validée (ou juste confirmer)
    logger.info("Authentification réussie")
    return api_key or "validated"


def get_client_ip(request) -> Optional[str]:
    """
    Extrait l'adresse IP du client depuis la requête.
    
    Args:
        request: Objet Request FastAPI
        
    Returns:
        Adresse IP du client ou None
    """
    if not request:
        return None
    
    # Vérifier les headers de proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Prendre la première IP (client réel)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # IP directe
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return None


# Alias pour faciliter l'utilisation
verify_api_key_required = verify_api_key_dependency

