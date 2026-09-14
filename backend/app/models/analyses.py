"""
Modèles SQLAlchemy pour les analyses, entreprises et documents.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Analysis(Base):
    """Analyse d'un document d'entreprise."""
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False, index=True)  # Identifiant unique de l'analyse
    analysis_number = Column(Integer, nullable=False)  # Numéro d'analyse pour l'utilisateur (1, 2, 3, etc.)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # id_employe
    company_id = Column(String(255), ForeignKey("companies.id"))  # Slug de l'entreprise
    company_name = Column(String(255), nullable=False)  # nom_entreprise / nom
    filename = Column(String(255))  # nom_fichier
    siret = Column(String(14))
    rcs = Column(String(20))
    document_type = Column(String(100))  # type_document / type
    risk_level = Column(String(50))  # risque / niveau_risque
    precision = Column(Numeric(5, 2))  # precision
    total_score = Column(Integer)  # score_total / score
    quality = Column(String(50))  # qualite
    risk_color = Column(String(50))  # risk_color
    status = Column(String(50), default="Terminée")  # status
    details = Column(JSONB)  # details (array de questions/réponses)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Index composite pour garantir l'unicité du numéro d'analyse par utilisateur
    __table_args__ = (
        # Contrainte unique: chaque utilisateur a ses propres numéros séquentiels
        # Note: L'unicité est garantie par la logique métier dans get_next_analysis_id
    )

    # Relations
    organization = relationship("Organization", back_populates="analyses")
    employee = relationship("User", back_populates="analyses")
    company = relationship("Company", back_populates="analyses", foreign_keys=[company_id])
    document = relationship("Document", back_populates="analysis", uselist=False)
    risk_links = relationship("AnalysisRiskLink", back_populates="analysis", cascade="all, delete-orphan")
    risk_histories = relationship("RiskHistory", back_populates="analysis", cascade="all, delete-orphan")


class Company(Base):
    """Entreprise."""
    __tablename__ = "companies"

    id = Column(String(255), primary_key=True)  # Utiliser slug comme clé primaire pour compatibilité
    slug = Column(String(255), unique=True, nullable=False, index=True)  # Identifiant unique (slug)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(String(50))  # id_entreprise (ancien format)
    name = Column(String(255), nullable=False)  # nom
    rcs = Column(String(20))  # rcs
    company_type = Column(String(100))  # type
    risk = Column(String(50))  # risque
    quality = Column(String(50))  # qualite
    total_score = Column(Integer)  # score_total
    details = Column(JSONB)  # details (array de questions/réponses)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    organization = relationship("Organization", back_populates="companies")
    employee = relationship("User", back_populates="companies")
    analyses = relationship("Analysis", back_populates="company", foreign_keys=[Analysis.company_id])


class Document(Base):
    """Document associé à une analyse."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # id_employe
    title = Column(String(255), nullable=False)  # titre
    content = Column(Text)  # contenu (PDF en base64 ou texte brut)
    status = Column(String(50), default="finalise")  # statut
    storage_key = Column(String(500))
    original_filename = Column(String(255))
    mime_type = Column(String(120))
    byte_size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    analysis = relationship("Analysis", back_populates="document")
    organization = relationship("Organization", back_populates="documents")
    employee = relationship("User", back_populates="documents")


class Counter(Base):
    """Compteur pour générer des IDs auto-incrémentés."""
    __tablename__ = "counters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False, index=True)  # Ex: "analyse_user_123"
    value = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

