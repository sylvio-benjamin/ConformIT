"""
Modèles SQLAlchemy pour les risques.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, ARRAY, CheckConstraint, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class RiskCategory(Base):
    """Catégorie de risque."""
    __tablename__ = "risk_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("risk_categories.id"))
    color = Column(String(7))  # Code couleur hex
    icon = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    risks = relationship("Risk", back_populates="category")
    parent_category = relationship("RiskCategory", remote_side=[id])


class Risk(Base):
    """Risque."""
    __tablename__ = "risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # RISK-001, RISK-002, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("risk_categories.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="identified")  # identified, assessed, treated, accepted, closed
    parent_risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id"))  # Pour hiérarchie
    priority = Column(String(50))  # low, medium, high, critical
    tags = Column(ARRAY(Text))  # Array de tags
    meta_data = Column(JSONB)  # Métadonnées personnalisées
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Champs pour l'intégration avec les analyses
    source_analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)  # Première analyse qui a créé ce risque
    analysis_history = Column(JSONB)  # Historique des analyses associées [{"analysis_id": "...", "date": "...", "score": ..., "risk_level": "..."}]
    linked_analyses_count = Column(Integer, default=0)  # Nombre d'analyses liées
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))

    # Contraintes
    __table_args__ = (
        CheckConstraint("status IN ('identified', 'assessed', 'treated', 'accepted', 'closed')", name="chk_risk_status"),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical') OR priority IS NULL", name="chk_risk_priority"),
    )

    # Relations
    organization = relationship("Organization", back_populates="risks")
    category = relationship("RiskCategory", back_populates="risks")
    assessments = relationship("RiskAssessment", back_populates="risk", cascade="all, delete-orphan")
    scores = relationship("RiskScore", back_populates="risk", cascade="all, delete-orphan")
    parent_risk = relationship("Risk", remote_side=[id])
    incidents = relationship("Incident", secondary="incident_risks", back_populates="risks")
    risk_controls = relationship("RiskControl", back_populates="risk", cascade="all, delete-orphan")
    source_analysis = relationship("Analysis", foreign_keys=[source_analysis_id])
    analysis_links = relationship("AnalysisRiskLink", back_populates="risk", cascade="all, delete-orphan")
    histories = relationship("RiskHistory", back_populates="risk", cascade="all, delete-orphan")


class RiskDependency(Base):
    """Dépendance entre risques."""
    __tablename__ = "risk_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    depends_on_risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(50))  # triggers, mitigates, exacerbates
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        {"comment": "Dépendances entre risques"},
    )


class RiskMatrix(Base):
    """Matrice de risque."""
    __tablename__ = "risk_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    probability_levels = Column(Integer, default=5)
    impact_levels = Column(Integer, default=5)
    matrix_config = Column(JSONB)  # Configuration de la matrice (seuils, couleurs)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskAssessment(Base):
    """Évaluation de risque."""
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    probability_level = Column(Integer)  # 1-5
    impact_level = Column(Integer)  # 1-5
    risk_level = Column(String(50))  # Calculé: low, medium, high, critical
    risk_score = Column(Integer)  # Score normalisé 0-100
    methodology = Column(String(50))  # qualitative, quantitative, semi-quantitative
    justification = Column(Text)
    confidence_level = Column(Integer)  # 1-5
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Contraintes
    __table_args__ = (
        CheckConstraint("probability_level >= 1 AND probability_level <= 5 OR probability_level IS NULL", name="chk_probability_level"),
        CheckConstraint("impact_level >= 1 AND impact_level <= 5 OR impact_level IS NULL", name="chk_impact_level"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical') OR risk_level IS NULL", name="chk_risk_level"),
    )

    # Relations
    risk = relationship("Risk", back_populates="assessments")
    scores = relationship("RiskScore", back_populates="assessment", cascade="all, delete-orphan")


class RiskScore(Base):
    """Score de risque."""
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("risk_assessments.id"))
    score = Column(Integer, nullable=False)  # 0-100
    normalized_score = Column(Numeric(5, 2))  # Score normalisé
    calculation_method = Column(String(50))
    factors = Column(JSONB)  # Facteurs de calcul (probabilité, impact, etc.)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    risk = relationship("Risk", back_populates="scores")
    assessment = relationship("RiskAssessment", back_populates="scores")

