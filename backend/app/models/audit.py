"""
Modèles SQLAlchemy pour l'audit et la sécurité.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class AuditLog(Base):
    """Log d'audit."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # create, update, delete, read
    resource_type = Column(String(50), nullable=False)  # risk, control, incident, etc.
    resource_id = Column(UUID(as_uuid=True))
    resource_name = Column(String(255))
    changes = Column(JSONB)  # Changements effectués (avant/après)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    organization = relationship("Organization", back_populates="audit_logs")


class SecurityPolicy(Base):
    """Politique de sécurité."""
    __tablename__ = "security_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    policy_type = Column(String(50))  # password, session, 2fa, encryption
    policy_config = Column(JSONB)  # Configuration de la politique
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="security_policies")

