"""
Schémas Pydantic pour les intégrations externes.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class ExternalIntegrationCreate(BaseModel):
    """Schéma pour créer une intégration externe."""
    integration_type: str = Field(..., description="Type d'intégration (infogreffe, insee, dun_bradstreet, powerbi)")
    name: str = Field(..., description="Nom de l'intégration")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration (API keys, endpoints, etc.)")
    sync_frequency: Optional[str] = Field("daily", description="Fréquence de synchronisation (daily, weekly, monthly, manual)")


class ExternalIntegrationUpdate(BaseModel):
    """Schéma pour mettre à jour une intégration externe."""
    name: Optional[str] = Field(None, description="Nom de l'intégration")
    status: Optional[str] = Field(None, description="Statut (active, inactive, error)")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration")
    sync_frequency: Optional[str] = Field(None, description="Fréquence de synchronisation")


class ExternalIntegrationResponse(BaseModel):
    """Schéma de réponse pour une intégration externe."""
    id: str = Field(..., description="ID de l'intégration")
    integration_type: str = Field(..., description="Type d'intégration")
    name: str = Field(..., description="Nom de l'intégration")
    status: str = Field(..., description="Statut (active, inactive, error)")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration")
    last_sync_at: Optional[datetime] = Field(None, description="Date de la dernière synchronisation")
    sync_frequency: Optional[str] = Field(None, description="Fréquence de synchronisation")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    @model_validator(mode='before')
    @classmethod
    def convert_uuid_to_string(cls, data: Any):
        """Convert UUID objects to strings before validation."""
        if isinstance(data, dict):
            if 'id' in data and isinstance(data['id'], UUID):
                data = {**data, 'id': str(data['id'])}
        elif hasattr(data, '__table__'):
            # Handle SQLAlchemy models - convert to dict first
            result = {}
            for column in data.__table__.columns:
                value = getattr(data, column.name, None)
                if isinstance(value, UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
            data = result
        return data

    class Config:
        from_attributes = True


class APICredentialCreate(BaseModel):
    """Schéma pour créer des identifiants API."""
    integration_id: str = Field(..., description="ID de l'intégration")
    credential_type: str = Field(..., description="Type d'identifiant (api_key, oauth_token, username_password)")
    credential_name: Optional[str] = Field(None, description="Nom de l'identifiant")
    credential_value: str = Field(..., description="Valeur de l'identifiant (sera chiffrée)")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration")


class APICredentialResponse(BaseModel):
    """Schéma de réponse pour des identifiants API."""
    id: str = Field(..., description="ID de l'identifiant")
    integration_id: str = Field(..., description="ID de l'intégration")
    credential_type: str = Field(..., description="Type d'identifiant")
    credential_name: Optional[str] = Field(None, description="Nom de l'identifiant")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    @model_validator(mode='before')
    @classmethod
    def convert_uuid_to_string(cls, data: Any):
        """Convert UUID objects to strings before validation."""
        if isinstance(data, dict):
            data = {**data}
            for field in ['id', 'integration_id']:
                if field in data and isinstance(data[field], UUID):
                    data[field] = str(data[field])
        elif hasattr(data, '__table__'):
            # Handle SQLAlchemy models - convert to dict first
            result = {}
            for column in data.__table__.columns:
                value = getattr(data, column.name, None)
                if isinstance(value, UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
            data = result
        return data

    class Config:
        from_attributes = True

