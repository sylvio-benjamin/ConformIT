"""
Modèles SQLAlchemy pour la conformité.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ComplianceFramework(Base):
    """Cadre de conformité."""
    __tablename__ = "compliance_frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # ISO 31000, ISO 27005, COSO ERM, etc.
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    version = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    requirements = relationship("ComplianceRequirement", back_populates="framework", cascade="all, delete-orphan")
    assessments = relationship("ComplianceAssessment", back_populates="framework")
    audits = relationship("ComplianceAudit", back_populates="framework")


class ComplianceRequirement(Base):
    """Exigence de conformité."""
    __tablename__ = "compliance_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    requirement_type = Column(String(50))  # mandatory, recommended, optional
    parent_requirement_id = Column(UUID(as_uuid=True), ForeignKey("compliance_requirements.id"))
    section = Column(String(100))
    subsection = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    framework = relationship("ComplianceFramework", back_populates="requirements")
    assessments = relationship("ComplianceAssessment", back_populates="requirement")


class ComplianceAssessment(Base):
    """Évaluation de conformité."""
    __tablename__ = "compliance_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"))
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("compliance_requirements.id"))
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    compliance_status = Column(String(50))  # compliant, non_compliant, partially_compliant, not_applicable
    evidence = Column(Text)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    organization = relationship("Organization", back_populates="compliance_assessments")
    framework = relationship("ComplianceFramework", back_populates="assessments")
    requirement = relationship("ComplianceRequirement", back_populates="assessments")
    gaps = relationship("ComplianceGap", back_populates="assessment", cascade="all, delete-orphan")


class ComplianceGap(Base):
    """Écart de conformité."""
    __tablename__ = "compliance_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("compliance_assessments.id", ondelete="CASCADE"), nullable=False)
    gap_description = Column(Text, nullable=False)
    severity = Column(String(50))  # low, medium, high, critical
    status = Column(String(50), default="open")  # open, in_progress, closed
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    assessment = relationship("ComplianceAssessment", back_populates="gaps")
    # ComplianceRemediation a gap_id qui pointe vers ComplianceGap, donc la relation est de ComplianceRemediation vers ComplianceGap
    remediation = relationship("ComplianceRemediation", back_populates="gap", uselist=False, cascade="all, delete-orphan")


class ComplianceRemediation(Base):
    """Plan de remédiation."""
    __tablename__ = "compliance_remediations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gap_id = Column(UUID(as_uuid=True), ForeignKey("compliance_gaps.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="planned")
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    # ComplianceRemediation appartient à un ComplianceGap (many-to-one)
    gap = relationship("ComplianceGap", back_populates="remediation")


class ComplianceAudit(Base):
    """Audit de conformité."""
    __tablename__ = "compliance_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"))
    audit_type = Column(String(50))  # internal, external, self_assessment
    audit_date = Column(DateTime(timezone=True))
    auditor_name = Column(String(255))
    audit_scope = Column(Text)
    findings = Column(Text)
    recommendations = Column(Text)
    audit_report_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    framework = relationship("ComplianceFramework", back_populates="audits")

