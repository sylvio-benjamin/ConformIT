"""
Schémas Pydantic pour la validation des données.
Schémas pour les risques, contrôles, incidents, conformité, KRIs, rapports, intégrations.
"""

# Imports des schémas pour les risques
from .risks import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
    RiskAssessmentCreate,
    RiskAssessmentResponse,
)

# Imports des schémas pour les contrôles
from .controls import (
    ControlCreate,
    ControlUpdate,
    ControlResponse,
    ActionPlanCreate,
    ActionPlanResponse,
)

# Imports des schémas pour les incidents
from .incidents import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    RootCauseAnalysisCreate,
    RootCauseAnalysisResponse,
)

# Imports des schémas pour la conformité
from .compliance import (
    ComplianceFrameworkResponse,
    ComplianceAssessmentCreate,
    ComplianceAssessmentResponse,
    ComplianceGapResponse,
)

# Imports des schémas pour les KRIs
from .kris import (
    KRICreate,
    KRIUpdate,
    KRIResponse,
    KRIMetricCreate,
    KRIMetricResponse,
    KRIAlertResponse,
)

# Imports des schémas pour les rapports
from .reports import (
    ReportCreate,
    ReportResponse,
    ReportTemplateCreate,
    ReportTemplateResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
)

# Imports des schémas pour les intégrations
from .integrations import (
    ExternalIntegrationCreate,
    ExternalIntegrationUpdate,
    ExternalIntegrationResponse,
    APICredentialCreate,
    APICredentialResponse,
)

# Imports des schémas de validation (fichiers uploadés, analyses)
from .validation import (
    UploadFileValidation,
    AnalyseRequest,
    AnalyseResponse,
    ResultatResponse,
    WebhookStripeRequest,
    ModifierAnalyseRequest,
)

__all__ = [
    # Risks
    "RiskCreate",
    "RiskUpdate",
    "RiskResponse",
    "RiskAssessmentCreate",
    "RiskAssessmentResponse",
    # Controls
    "ControlCreate",
    "ControlUpdate",
    "ControlResponse",
    "ActionPlanCreate",
    "ActionPlanResponse",
    # Incidents
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    "RootCauseAnalysisCreate",
    "RootCauseAnalysisResponse",
    # Compliance
    "ComplianceFrameworkResponse",
    "ComplianceAssessmentCreate",
    "ComplianceAssessmentResponse",
    "ComplianceGapResponse",
    # KRIs
    "KRICreate",
    "KRIUpdate",
    "KRIResponse",
    "KRIMetricCreate",
    "KRIMetricResponse",
    "KRIAlertResponse",
    # Reports
    "ReportCreate",
    "ReportResponse",
    "ReportTemplateCreate",
    "ReportTemplateResponse",
    "ReportScheduleCreate",
    "ReportScheduleResponse",
    # Integrations
    "ExternalIntegrationCreate",
    "ExternalIntegrationUpdate",
    "ExternalIntegrationResponse",
    "APICredentialCreate",
    "APICredentialResponse",
    # Validation
    "UploadFileValidation",
    "AnalyseRequest",
    "AnalyseResponse",
    "ResultatResponse",
    "WebhookStripeRequest",
    "ModifierAnalyseRequest",
]

