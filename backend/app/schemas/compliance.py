"""
Schémas Pydantic pour la conformité.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ComplianceFrameworkResponse(BaseModel):
    """Schéma de réponse pour un cadre de conformité."""
    id: str = Field(..., description="ID du cadre")
    name: str = Field(..., description="Nom du cadre (ISO 31000, ISO 27005, etc.)")
    code: str = Field(..., description="Code du cadre")
    description: Optional[str] = Field(None, description="Description")
    version: Optional[str] = Field(None, description="Version")
    is_active: bool = Field(True, description="Actif ou non")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True


class ComplianceAssessmentCreate(BaseModel):
    """Schéma pour créer une évaluation de conformité."""
    framework_id: str = Field(..., description="ID du cadre de conformité")
    requirement_id: Optional[str] = Field(None, description="ID de l'exigence")
    compliance_status: str = Field(..., description="Statut (compliant, non_compliant, partially_compliant, not_applicable)")
    evidence: Optional[str] = Field(None, description="Preuve de conformité")
    notes: Optional[str] = Field(None, description="Notes")


class ComplianceAssessmentResponse(BaseModel):
    """Schéma de réponse pour une évaluation de conformité."""
    id: str = Field(..., description="ID de l'évaluation")
    framework_id: str = Field(..., description="ID du cadre de conformité")
    requirement_id: Optional[str] = Field(None, description="ID de l'exigence")
    assessment_date: datetime = Field(..., description="Date d'évaluation")
    compliance_status: str = Field(..., description="Statut de conformité")
    evidence: Optional[str] = Field(None, description="Preuve de conformité")
    assessed_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a évalué")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True


class ComplianceGapResponse(BaseModel):
    """Schéma de réponse pour un écart de conformité."""
    id: str = Field(..., description="ID de l'écart")
    assessment_id: str = Field(..., description="ID de l'évaluation")
    gap_description: str = Field(..., description="Description de l'écart")
    severity: str = Field(..., description="Sévérité (low, medium, high, critical)")
    remediation_plan_id: Optional[str] = Field(None, description="ID du plan de remédiation")
    status: str = Field(..., description="Statut (open, in_progress, closed)")
    closed_at: Optional[datetime] = Field(None, description="Date de fermeture")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True

