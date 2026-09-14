"""Profil d'organisation, règles d'applicabilité (KB globale) et décisions orga."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class OrganizationProfile(Base):
    __tablename__ = "organization_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    sector = Column(String(100))
    size = Column(String(50))
    country = Column(String(2))
    criticality = Column(String(50))
    processes_personal_data = Column(Boolean, default=False)
    hosting = Column(String(50))
    listed_company = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization")


class ApplicabilityRule(Base):
    """Règle globale (pas d'organization_id)."""
    __tablename__ = "applicability_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(80), unique=True, nullable=False)
    framework_code = Column(String(50), nullable=False, index=True)
    condition = Column(JSONB, nullable=False, default=dict)
    reason = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApplicabilityDecision(Base):
    __tablename__ = "applicability_decisions"
    __table_args__ = (
        UniqueConstraint("organization_id", "framework_code", name="uq_applicability_org_framework"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    framework_code = Column(String(50), nullable=False)
    applicable = Column(Boolean, nullable=False, default=False)
    reason = Column(Text)
    confidence = Column(Float, default=0.8)
    source_rule = Column(String(80))
    override = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KbControl(Base):
    """Contrôle catalogue global — distinct des controls d'organisation."""
    __tablename__ = "kb_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(80), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    framework_code = Column(String(50), nullable=False, index=True)
    control_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
