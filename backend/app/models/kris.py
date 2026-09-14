"""
Modèles SQLAlchemy pour les KRIs (Indicateurs Clés de Risque).
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class KRI(Base):
    """Indicateur Clé de Risque."""
    __tablename__ = "kris"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("risk_categories.id"))
    calculation_formula = Column(Text)
    data_source = Column(String(100))  # API, manual, import
    unit = Column(String(50))  # percentage, count, currency, etc.
    frequency = Column(String(50))  # daily, weekly, monthly, quarterly
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="kris")
    metrics = relationship("KRIMetric", back_populates="kri", cascade="all, delete-orphan")
    alerts = relationship("KRIAlert", back_populates="kri", cascade="all, delete-orphan")


class KRIMetric(Base):
    """Métrique KRI."""
    __tablename__ = "kri_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kri_id = Column(UUID(as_uuid=True), ForeignKey("kris.id", ondelete="CASCADE"), nullable=False)
    measurement_date = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric(15, 2), nullable=False)
    target_value = Column(Numeric(15, 2))
    threshold_green = Column(Numeric(15, 2))
    threshold_yellow = Column(Numeric(15, 2))
    threshold_orange = Column(Numeric(15, 2))
    threshold_red = Column(Numeric(15, 2))
    status = Column(String(50))  # green, yellow, orange, red
    data_source = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    kri = relationship("KRI", back_populates="metrics")
    alerts = relationship("KRIAlert", back_populates="metric", cascade="all, delete-orphan")


class KRIAlert(Base):
    """Alerte KRI."""
    __tablename__ = "kri_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kri_id = Column(UUID(as_uuid=True), ForeignKey("kris.id", ondelete="CASCADE"), nullable=False)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("kri_metrics.id"))
    alert_type = Column(String(50))  # threshold_exceeded, trend_change, anomaly
    severity = Column(String(50))  # low, medium, high, critical
    message = Column(Text)
    status = Column(String(50), default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    kri = relationship("KRI", back_populates="alerts")
    metric = relationship("KRIMetric", back_populates="alerts")

