"""
Modèles SQLAlchemy pour les contrôles.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Control(Base):
    """Contrôle/Mesure de maîtrise."""
    __tablename__ = "controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    control_type = Column(String(50))  # preventive, detective, corrective
    control_category = Column(String(50))  # technical, administrative, physical
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="planned")  # planned, in_progress, completed, verified
    effectiveness_rating = Column(Integer)  # 1-5
    last_test_date = Column(DateTime(timezone=True))
    next_test_date = Column(DateTime(timezone=True))
    documentation_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('planned', 'in_progress', 'completed', 'verified')", name="chk_control_status"),
    )

    # Relations
    organization = relationship("Organization", back_populates="controls")
    risk_controls = relationship("RiskControl", back_populates="control", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlan", back_populates="control", cascade="all, delete-orphan")
    tests = relationship("ControlTest", back_populates="control", cascade="all, delete-orphan")


class RiskControl(Base):
    """Liaison Risques-Contrôles."""
    __tablename__ = "risk_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False)
    effectiveness = Column(Numeric(5, 2))  # 0-100
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    risk = relationship("Risk")
    control = relationship("Control", back_populates="risk_controls")


class ActionPlan(Base):
    """Plan d'action."""
    __tablename__ = "action_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"))
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="planned")  # planned, in_progress, completed, cancelled
    priority = Column(String(50))  # low, medium, high, critical
    completion_percentage = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    control = relationship("Control", back_populates="action_plans")


class ControlTest(Base):
    """Test de contrôle."""
    __tablename__ = "control_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False)
    test_date = Column(DateTime(timezone=True), server_default=func.now())
    tested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    test_method = Column(String(50))  # walkthrough, inquiry, observation, inspection
    test_result = Column(String(50))  # passed, failed, partial
    findings = Column(Text)
    recommendations = Column(Text)
    next_test_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    control = relationship("Control", back_populates="tests")

