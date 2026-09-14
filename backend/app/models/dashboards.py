"""
Modèles SQLAlchemy pour les dashboards.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Dashboard(Base):
    """Tableau de bord."""
    __tablename__ = "dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    layout = Column(JSONB)
    is_shared = Column(Boolean, default=False)
    shared_with = Column(ARRAY(UUID))  # Array d'user IDs
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="dashboards")
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Widget de tableau de bord."""
    __tablename__ = "dashboard_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False)
    widget_type = Column(String(50))  # chart, table, kpi, risk_matrix
    widget_config = Column(JSONB)
    position_x = Column(Integer)
    position_y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    data_source = Column(String(100))  # risk, control, incident, kri
    filters = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    dashboard = relationship("Dashboard", back_populates="widgets")

