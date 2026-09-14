"""
Modèles SQLAlchemy pour les organisations et utilisateurs.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Organization(Base):
    """Organisation/Entreprise."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    siret = Column(String(14))
    rcs = Column(String(20))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    industry = Column(String(100))
    size = Column(String(50))  # TPE, PME, ETI, Grande Entreprise
    plan = Column(String(50))  # basic, pro, enterprise
    subscription_status = Column(String(50))  # active, suspended, cancelled
    grc_snapshot = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    users = relationship("User", back_populates="organization")
    risks = relationship("Risk", back_populates="organization", cascade="all, delete-orphan")
    controls = relationship("Control", back_populates="organization", cascade="all, delete-orphan")
    kris = relationship("KRI", back_populates="organization", cascade="all, delete-orphan")
    dashboards = relationship("Dashboard", back_populates="organization", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="organization", cascade="all, delete-orphan")
    compliance_assessments = relationship("ComplianceAssessment", back_populates="organization", cascade="all, delete-orphan")
    external_integrations = relationship("ExternalIntegration", back_populates="organization", cascade="all, delete-orphan")
    report_templates = relationship("ReportTemplate", back_populates="organization", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    security_policies = relationship("SecurityPolicy", back_populates="organization", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="organization", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")


class Role(Base):
    """Rôle utilisateur."""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class Permission(Base):
    """Permission."""
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(100), nullable=False)  # risk, control, incident, etc.
    action = Column(String(50), nullable=False)  # create, read, update, delete
    description = Column(Text)

    # Relations
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(Base):
    """Table de liaison Rôles-Permissions."""
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class User(Base):
    """Utilisateur. Auth FastAPI (password_hash)."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    nom = Column(String(100))
    prenom = Column(String(100))
    entreprise = Column(String(255))
    telephone = Column(String(20))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    abonnement = Column(String(50), default="basic")
    preferences = Column(JSONB)
    is_active = Column(Boolean, default=True)
    is_platform_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    is_2fa_enabled = Column(Boolean, default=False)
    two_fa_secret = Column(String(255))
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    analyses = relationship("Analysis", back_populates="employee", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    collaborators = relationship("Collaborator", back_populates="user", cascade="all, delete-orphan")
    quotas = relationship("Quota", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

