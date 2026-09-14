"""Preuves de conformité (issues des findings d'analyse) et traitements de risques."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="SET NULL"),
        nullable=True,
    )
    framework_code = Column(String(50), index=True)
    applicable_frameworks = Column(JSONB, default=list)
    title = Column(String(255), nullable=False)
    detail = Column(Text)
    severity = Column(String(50))
    status = Column(String(50), nullable=False, default="proposed", index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskTreatment(Base):
    __tablename__ = "risk_treatments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_id = Column(
        UUID(as_uuid=True),
        ForeignKey("risks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy = Column(String(50), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="planned", index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    risk = relationship("Risk")
