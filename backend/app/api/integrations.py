"""
API REST pour la gestion des intégrations externes.
Endpoints : GET /api/integrations, GET /api/integrations/:id, POST /api/integrations, PUT /api/integrations/:id, DELETE /api/integrations/:id, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID as PyUUID
from datetime import datetime

from app.database import get_db
from app.models.integrations import ExternalIntegration, APICredential, DataSync
from app.models.organizations import User, Organization
from app.schemas.integrations import (
    ExternalIntegrationCreate, ExternalIntegrationUpdate, ExternalIntegrationResponse,
    APICredentialCreate, APICredentialResponse
)
from app.utils import encrypt_value, decrypt_value
from app.services.integrations import (
    InfogreffeService, INSEEService, DunBradstreetService, PowerBIService
)
from app.core.permissions import get_current_user

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _organization_of(db: Session, current: User) -> Organization:
    if not current.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    org = db.query(Organization).filter(Organization.id == current.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


def get_integration_service(integration_type: str, config: Dict[str, Any]):
    """
    Crée et retourne le service approprié selon le type d'intégration.
    
    Args:
        integration_type: Type d'intégration (infogreffe, insee, dun_bradstreet, powerbi)
        config: Configuration contenant les credentials
        
    Returns:
        Service d'intégration approprié
    """
    if integration_type == "infogreffe":
        api_key = config.get("api_key")
        return InfogreffeService(api_key=api_key)
    
    elif integration_type == "insee":
        api_key = config.get("api_key")
        return INSEEService(api_key=api_key)
    
    elif integration_type == "dun_bradstreet":
        api_key = config.get("api_key")
        return DunBradstreetService(api_key=api_key)
    
    elif integration_type == "powerbi":
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        tenant_id = config.get("tenant_id")
        return PowerBIService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Type d'intégration non supporté: {integration_type}")


@router.get("", response_model=List[ExternalIntegrationResponse])
async def list_integrations(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Liste des intégrations d'une organisation."""
    org = _organization_of(db, current)
    integrations = db.query(ExternalIntegration).filter(
        ExternalIntegration.organization_id == org.id
    ).all()
    return integrations


@router.get("/{integration_id}", response_model=ExternalIntegrationResponse)
async def get_integration(integration_id: str, db: Session = Depends(get_db)):
    """Détails d'une intégration."""
    try:
        integration = db.query(ExternalIntegration).filter(
            ExternalIntegration.id == PyUUID(integration_id)
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Intégration non trouvée")
        
        return integration
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.post("", response_model=ExternalIntegrationResponse, status_code=201)
async def create_integration(
    integration_data: ExternalIntegrationCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Créer une intégration."""
    org = _organization_of(db, current)
    
    # Vérifier si une intégration du même type existe déjà
    existing = db.query(ExternalIntegration).filter(
        ExternalIntegration.organization_id == org.id,
        ExternalIntegration.integration_type == integration_data.integration_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une intégration de type '{integration_data.integration_type}' existe déjà"
        )
    
    # Chiffrer les credentials sensibles dans la config
    config = integration_data.config or {}
    if "api_key" in config:
        config["api_key_encrypted"] = encrypt_value(config["api_key"])
        del config["api_key"]
    if "client_secret" in config:
        config["client_secret_encrypted"] = encrypt_value(config["client_secret"])
        del config["client_secret"]
    
    integration = ExternalIntegration(
        organization_id=org.id,
        integration_type=integration_data.integration_type,
        name=integration_data.name,
        config=config,
        sync_frequency=integration_data.sync_frequency or "manual",
        status="active"
    )
    
    db.add(integration)
    db.commit()
    db.refresh(integration)
    
    return integration


@router.put("/{integration_id}", response_model=ExternalIntegrationResponse)
async def update_integration(
    integration_id: str,
    integration_data: ExternalIntegrationUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une intégration."""
    try:
        integration = db.query(ExternalIntegration).filter(
            ExternalIntegration.id == PyUUID(integration_id)
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Intégration non trouvée")
        
        # Mettre à jour les champs fournis
        update_data = integration_data.dict(exclude_unset=True)
        
        # Chiffrer les nouvelles credentials si présentes
        if "config" in update_data:
            config = update_data["config"]
            if "api_key" in config:
                config["api_key_encrypted"] = encrypt_value(config["api_key"])
                del config["api_key"]
            if "client_secret" in config:
                config["client_secret_encrypted"] = encrypt_value(config["client_secret"])
                del config["client_secret"]
        
        for key, value in update_data.items():
            setattr(integration, key, value)
        
        db.commit()
        db.refresh(integration)
        
        return integration
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(integration_id: str, db: Session = Depends(get_db)):
    """Supprimer une intégration."""
    try:
        integration = db.query(ExternalIntegration).filter(
            ExternalIntegration.id == PyUUID(integration_id)
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Intégration non trouvée")
        
        db.delete(integration)
        db.commit()
        return None
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.post("/{integration_id}/test", status_code=200)
async def test_integration(integration_id: str, db: Session = Depends(get_db)):
    """Tester la connexion d'une intégration."""
    try:
        integration = db.query(ExternalIntegration).filter(
            ExternalIntegration.id == PyUUID(integration_id)
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Intégration non trouvée")
        
        # Récupérer et déchiffrer les credentials
        config = integration.config or {}
        if "api_key_encrypted" in config:
            config["api_key"] = decrypt_value(config["api_key_encrypted"])
        if "client_secret_encrypted" in config:
            config["client_secret"] = decrypt_value(config["client_secret_encrypted"])
        
        # Créer le service approprié et tester la connexion
        service = get_integration_service(integration.integration_type, config)
        is_connected = service.test_connection()
        
        # Mettre à jour le statut
        integration.status = "active" if is_connected else "error"
        integration.last_sync_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": is_connected,
            "status": integration.status,
            "message": "Connexion réussie" if is_connected else "Échec de la connexion"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")
    except Exception as e:
        integration.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync", status_code=200)
async def sync_integration(
    integration_id: str,
    sync_type: str = Query("incremental", description="Type de synchronisation (full, incremental)"),
    db: Session = Depends(get_db)
):
    """Synchroniser une intégration."""
    try:
        integration = db.query(ExternalIntegration).filter(
            ExternalIntegration.id == PyUUID(integration_id)
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Intégration non trouvée")
        
        # Créer un enregistrement de synchronisation
        sync = DataSync(
            integration_id=integration.id,
            sync_type=sync_type,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(sync)
        db.commit()
        
        try:
            # Récupérer et déchiffrer les credentials
            config = integration.config or {}
            if "api_key_encrypted" in config:
                config["api_key"] = decrypt_value(config["api_key_encrypted"])
            if "client_secret_encrypted" in config:
                config["client_secret"] = decrypt_value(config["client_secret_encrypted"])
            
            # Créer le service et effectuer la synchronisation
            service = get_integration_service(integration.integration_type, config)
            
            # Ici, implémenter la logique de synchronisation selon le type
            # Pour l'instant, on simule une synchronisation
            records_synced = 0
            records_failed = 0
            
            # Mettre à jour le statut
            sync.status = "completed"
            sync.records_synced = records_synced
            sync.records_failed = records_failed
            sync.completed_at = datetime.utcnow()
            
            integration.last_sync_at = datetime.utcnow()
            integration.status = "active"
            
            db.commit()
            
            return {
                "success": True,
                "sync_id": str(sync.id),
                "records_synced": records_synced,
                "records_failed": records_failed
            }
            
        except Exception as e:
            sync.status = "failed"
            sync.error_message = str(e)
            sync.completed_at = datetime.utcnow()
            integration.status = "error"
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))
            
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.get("/{integration_id}/syncs", status_code=200)
async def get_integration_syncs(integration_id: str, db: Session = Depends(get_db)):
    """Historique des synchronisations d'une intégration."""
    try:
        syncs = db.query(DataSync).filter(
            DataSync.integration_id == PyUUID(integration_id)
        ).order_by(DataSync.created_at.desc()).limit(50).all()
        
        return {
            "integration_id": integration_id,
            "syncs": [
                {
                    "id": str(sync.id),
                    "sync_type": sync.sync_type,
                    "status": sync.status,
                    "records_synced": sync.records_synced,
                    "records_failed": sync.records_failed,
                    "started_at": sync.started_at.isoformat() if sync.started_at else None,
                    "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                    "error_message": sync.error_message
                }
                for sync in syncs
            ]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")
