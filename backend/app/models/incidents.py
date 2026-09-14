"""
Modèles SQLAlchemy pour les incidents.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Incident(Base):
    """Incident/Événement."""
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    incident_type = Column(String(50))  # security, operational, financial, etc.
    severity = Column(String(50))  # low, medium, high, critical
    status = Column(String(50), default="reported")  # reported, investigating, resolved, closed
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    impact_description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical') OR severity IS NULL", name="chk_incident_severity"),
        CheckConstraint("status IN ('reported', 'investigating', 'resolved', 'closed')", name="chk_incident_status"),
    )

    # Relations
    organization = relationship("Organization", back_populates="incidents")
    # RootCauseAnalysis a incident_id qui pointe vers Incident, donc la relation est de RootCauseAnalysis vers Incident
    root_cause_analysis = relationship("RootCauseAnalysis", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    risks = relationship("Risk", secondary="incident_risks", back_populates="incidents")
    corrective_actions = relationship("CorrectiveAction", back_populates="incident", cascade="all, delete-orphan")
    preventive_actions = relationship("PreventiveAction", back_populates="incident", cascade="all, delete-orphan")


class IncidentRisk(Base):
    """Liaison Incidents-Risques."""
    __tablename__ = "incident_risks"

    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    relationship_type = Column(String(50))  # triggered_by, mitigated_by, related_to
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RootCauseAnalysis(Base):
    """Analyse de cause racine."""
    __tablename__ = "root_cause_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    methodology = Column(String(50))  # 5_why, ishikawa, fault_tree
    analysis = Column(Text)
    root_causes = Column(ARRAY(Text))
    contributing_factors = Column(ARRAY(Text))
    analyzed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    # RootCauseAnalysis appartient à un Incident (many-to-one)
    incident = relationship("Incident", back_populates="root_cause_analysis")


class CorrectiveAction(Base):
    """Action corrective."""
    __tablename__ = "corrective_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="planned")
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    incident = relationship("Incident", back_populates="corrective_actions")


class PreventiveAction(Base):
    """Action préventive."""
    __tablename__ = "preventive_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="planned")
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    incident = relationship("Incident", back_populates="preventive_actions")

