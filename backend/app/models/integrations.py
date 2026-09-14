"""
Modèles SQLAlchemy pour les intégrations externes.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ExternalIntegration(Base):
    """Intégration externe."""
    __tablename__ = "external_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    integration_type = Column(String(50))  # infogreffe, insee, dun_bradstreet, powerbi
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")  # active, inactive, error
    config = Column(JSONB)  # Configuration (API keys, endpoints, etc.)
    last_sync_at = Column(DateTime(timezone=True))
    sync_frequency = Column(String(50))  # daily, weekly, monthly, manual
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="external_integrations")
    credentials = relationship("APICredential", back_populates="integration", cascade="all, delete-orphan")
    syncs = relationship("DataSync", back_populates="integration", cascade="all, delete-orphan")


class APICredential(Base):
    """Identifiant API."""
    __tablename__ = "api_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False)
    credential_type = Column(String(50))  # api_key, oauth_token, username_password
    credential_name = Column(String(255))
    encrypted_value = Column(Text)  # Valeur chiffrée
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    integration = relationship("ExternalIntegration", back_populates="credentials")


class DataSync(Base):
    """Synchronisation de données."""
    __tablename__ = "data_syncs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False)
    sync_type = Column(String(50))  # full, incremental
    status = Column(String(50))  # pending, running, completed, failed
    records_synced = Column(Integer)
    records_failed = Column(Integer)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    integration = relationship("ExternalIntegration", back_populates="syncs")

