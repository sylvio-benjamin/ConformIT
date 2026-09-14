"""
Modèles SQLAlchemy pour PostgreSQL.
Tous les modèles sont importés ici pour faciliter l'utilisation.
"""

from app.database import Base

# Import des anciens modèles (dataclasses pour compatibilité)
import sys
from pathlib import Path
models_py = Path(__file__).parent.parent / "models.py"
if models_py.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_models", models_py)
    app_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_models)
    AnalyseData = app_models.AnalyseData
    QuestionReponse = app_models.QuestionReponse
else:
    # Fallback si models.py n'existe pas
    from dataclasses import dataclass
    from typing import Optional, List, Dict, Any
    from datetime import datetime
    
    @dataclass
    class AnalyseData:
        slug: str
        nom: str
        type: str
        rcs: str
        score_total: int
        risque: str
        precision: float
        qualite: Optional[str] = None
        details: Optional[List[Dict[str, Any]]] = None
        date_creation: Optional[datetime] = None
        date_modification: Optional[datetime] = None
    
    @dataclass
    class QuestionReponse:
        numero: int
        question: str
        reponse: str
        justification: Optional[str] = None
        score: Optional[int] = None

# Import de tous les modèles SQLAlchemy
from app.models.organizations import Organization, User, Role, Permission, RolePermission
from app.models.risks import (
    RiskCategory, Risk, RiskDependency,
    RiskMatrix, RiskAssessment, RiskScore
)
from app.models.controls import (
    Control, RiskControl, ActionPlan, ControlTest
)
from app.models.kris import (
    KRI, KRIMetric, KRIAlert
)
from app.models.dashboards import (
    Dashboard, DashboardWidget
)
from app.models.incidents import (
    Incident, IncidentRisk, RootCauseAnalysis,
    CorrectiveAction, PreventiveAction
)
from app.models.compliance import (
    ComplianceFramework, ComplianceRequirement,
    ComplianceAssessment, ComplianceGap,
    ComplianceRemediation, ComplianceAudit
)
from app.models.integrations import (
    ExternalIntegration, APICredential, DataSync
)
from app.models.reports import (
    ReportTemplate, Report, ReportSchedule
)
from app.models.audit import (
    AuditLog, SecurityPolicy
)
from app.models.analyses import (
    Analysis, Company, Document, Counter
)
from app.models.analysis_risk_link import (
    AnalysisRiskLink, RiskHistory
)
from app.models.collaborators import (
    Collaborator
)
from app.models.quotas import (
    Quota
)
from app.models.api_keys import (
    APIKey
)
from app.models.auth_session import (
    AuthSession,
    PasswordResetToken,
)
from app.models.applicability import (
    OrganizationProfile,
    ApplicabilityRule,
    ApplicabilityDecision,
    KbControl,
)
from app.models.analysis_jobs import AnalysisJob, AnalysisFinding
from app.models.compliance_evidence import ComplianceEvidence, RiskTreatment
from app.models.grc_audits import GrcAudit, AuditFinding
from app.models.iso_catalog import IsoDeliverable

__all__ = [
    # Organizations
    "Organization",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    # Risks
    "RiskCategory",
    "Risk",
    "RiskDependency",
    "RiskMatrix",
    "RiskAssessment",
    "RiskScore",
    # Controls
    "Control",
    "RiskControl",
    "ActionPlan",
    "ControlTest",
    # KRIs
    "KRI",
    "KRIMetric",
    "KRIAlert",
    # Dashboards
    "Dashboard",
    "DashboardWidget",
    # Incidents
    "Incident",
    "IncidentRisk",
    "RootCauseAnalysis",
    "CorrectiveAction",
    "PreventiveAction",
    # Compliance
    "ComplianceFramework",
    "ComplianceRequirement",
    "ComplianceAssessment",
    "ComplianceGap",
    "ComplianceRemediation",
    "ComplianceAudit",
    # Integrations
    "ExternalIntegration",
    "APICredential",
    "DataSync",
    # Reports
    "ReportTemplate",
    "Report",
    "ReportSchedule",
    # Audit
    "AuditLog",
    "SecurityPolicy",
    # Anciens modèles (dataclasses)
    "AnalyseData",
    "QuestionReponse",
    # Analyses
    "Analysis",
    "Company",
    "Document",
    "Counter",
    # Analysis-GRC Integration
    "AnalysisRiskLink",
    "RiskHistory",
    # Collaborators
    "Collaborator",
    # Quotas
    "Quota",
    # API Keys
    "APIKey",
    "AuthSession",
    "PasswordResetToken",
    "OrganizationProfile",
    "ApplicabilityRule",
    "ApplicabilityDecision",
    "KbControl",
    "AnalysisJob",
    "AnalysisFinding",
    "ComplianceEvidence",
    "RiskTreatment",
    "GrcAudit",
    "AuditFinding",
    "IsoDeliverable",
]

