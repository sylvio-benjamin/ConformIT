"""
Modèles SQLAlchemy pour les rapports.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ReportTemplate(Base):
    """Modèle de rapport."""
    __tablename__ = "report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50))
    template_config = Column(JSONB)  # Configuration du modèle (sections, styles, etc.)
    is_system_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="report_templates")
    reports = relationship("Report", back_populates="template")
    schedules = relationship("ReportSchedule", back_populates="template", cascade="all, delete-orphan")


class Report(Base):
    """Rapport."""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50))  # risk_report, compliance_report, incident_report, etc.
    title = Column(String(255), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("report_templates.id"))
    parameters = Column(JSONB)  # Paramètres du rapport (filtres, période, etc.)
    status = Column(String(50), default="draft")  # draft, generating, completed, failed
    file_url = Column(Text)
    file_format = Column(String(50))  # pdf, excel, word, powerpoint
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    generated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    organization = relationship("Organization", back_populates="reports")
    template = relationship("ReportTemplate", back_populates="reports")


class ReportSchedule(Base):
    """Planification de rapport."""
    __tablename__ = "report_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_template_id = Column(UUID(as_uuid=True), ForeignKey("report_templates.id", ondelete="CASCADE"), nullable=False)
    schedule_type = Column(String(50))  # daily, weekly, monthly, quarterly, yearly
    schedule_config = Column(JSONB)  # Configuration de la planification (jour, heure, etc.)
    recipients = Column(ARRAY(UUID))  # Array d'user IDs
    email_subject = Column(String(255))
    email_body = Column(Text)
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime(timezone=True))
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    template = relationship("ReportTemplate", back_populates="schedules")

