"""
Modèles SQLAlchemy pour les quotas mensuels d'analyses.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Quota(Base):
    """Quota mensuel d'analyses pour un utilisateur."""
    __tablename__ = "quotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    count = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Contrainte unique : un seul quota par utilisateur et par mois
    __table_args__ = (
        UniqueConstraint('user_id', 'month', name='uq_quota_user_month'),
    )

    # Relations
    user = relationship("User", back_populates="quotas")

