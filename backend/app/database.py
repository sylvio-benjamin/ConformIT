"""
Module de connexion à la base de données PostgreSQL avec SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from app.config import POSTGRES_URL

logger = logging.getLogger(__name__)

# Créer l'engine SQLAlchemy
engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,  # Vérifie les connexions avant utilisation
    pool_recycle=3600,  # Recycle les connexions après 1 heure
    echo=False  # Mettre à True pour voir les requêtes SQL dans les logs
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def import_models() -> None:
    """Enregistre les modèles SQLAlchemy. Ne mute pas le schéma."""
    from app.models import (  # noqa: F401
        Organization, Role, Permission, User,
        RiskCategory, Risk, RiskDependency,
        RiskMatrix, RiskAssessment, RiskScore,
        Control, RiskControl, ActionPlan, ControlTest,
        KRI, KRIMetric, KRIAlert,
        Dashboard, DashboardWidget,
        Incident, IncidentRisk, RootCauseAnalysis,
        CorrectiveAction, PreventiveAction,
        ComplianceFramework, ComplianceRequirement,
        ComplianceAssessment, ComplianceGap, ComplianceRemediation, ComplianceAudit,
        ExternalIntegration, APICredential, DataSync,
        ReportTemplate, Report, ReportSchedule,
        AuditLog, SecurityPolicy,
        Analysis, Company, Document, Counter,
        Collaborator,
        Quota, APIKey,
    )
    from app.models.auth_session import AuthSession, PasswordResetToken  # noqa: F401
    from app.models.analysis_risk_link import AnalysisRiskLink, RiskHistory  # noqa: F401
    from app.models.applicability import (  # noqa: F401
        OrganizationProfile,
        ApplicabilityRule,
        ApplicabilityDecision,
        KbControl,
    )
    from app.models.analysis_jobs import AnalysisJob, AnalysisFinding  # noqa: F401
    from app.models.compliance_evidence import ComplianceEvidence, RiskTreatment  # noqa: F401
    from app.models.grc_audits import GrcAudit, AuditFinding  # noqa: F401
    from app.models.iso_catalog import IsoDeliverable  # noqa: F401


def ping_db() -> bool:
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def init_db():
    """Enregistre les modèles. Le schéma est exclusivement géré par Alembic."""
    import_models()
    logger.info("Modèles SQLAlchemy enregistrés — aucune migration implicite au boot")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI qui fournit une session de base de données.
    Usage:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager pour utiliser la base de données en dehors de FastAPI.
    Usage:
        with get_db_context() as db:
            # Utiliser db ici
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

