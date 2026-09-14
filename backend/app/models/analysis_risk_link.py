"""
Modèle pour lier les analyses aux risques GRC.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class AnalysisRiskLink(Base):
    """Lien entre une analyse et un risque GRC."""
    __tablename__ = "analysis_risk_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Informations sur le finding extrait de l'analyse
    finding_type = Column(String(100))  # risk, anomaly, non_compliance
    severity = Column(String(50))  # low, medium, high, critical
    finding_description = Column(Text)  # Description du finding extrait
    finding_details = Column(JSONB)  # Détails supplémentaires du finding
    
    # Score et niveau de risque de l'analyse
    analysis_score = Column(Integer)  # Score total de l'analyse
    analysis_risk_level = Column(String(50))  # Niveau de risque de l'analyse
    
    # Statut de l'intégration
    integration_status = Column(String(50), default="created")  # created, updated, closed
    auto_generated = Column(Boolean, default=True)  # Si généré automatiquement
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    analysis = relationship("Analysis", foreign_keys=[analysis_id])
    risk = relationship("Risk", foreign_keys=[risk_id])


class RiskHistory(Base):
    """Historique des modifications d'un risque, incluant les analyses liées."""
    __tablename__ = "risk_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Type de changement
    change_type = Column(String(50))  # created, updated, status_changed, priority_changed, linked_analysis, closed
    
    # Données du changement
    old_value = Column(JSONB)  # Valeurs avant le changement
    new_value = Column(JSONB)  # Valeurs après le changement
    
    # Analyse associée (si changement lié à une analyse)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    
    # Utilisateur qui a fait le changement
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Description du changement
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    risk = relationship("Risk", foreign_keys=[risk_id])
    analysis = relationship("Analysis", foreign_keys=[analysis_id])
    user = relationship("User", foreign_keys=[changed_by])

