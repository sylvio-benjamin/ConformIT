"""
Schémas Pydantic pour les rapports.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    """Schéma pour créer un rapport."""
    report_type: str = Field(..., description="Type de rapport (risk_report, compliance_report, incident_report, etc.)")
    title: str = Field(..., description="Titre du rapport")
    template_id: Optional[str] = Field(None, description="ID du modèle de rapport")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Paramètres du rapport (filtres, période, etc.)")
    file_format: Optional[str] = Field("pdf", description="Format du rapport (pdf, excel, word, powerpoint)")


class ReportResponse(BaseModel):
    """Schéma de réponse pour un rapport."""
    id: str = Field(..., description="ID du rapport")
    report_type: str = Field(..., description="Type de rapport")
    title: str = Field(..., description="Titre du rapport")
    template_id: Optional[str] = Field(None, description="ID du modèle de rapport")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Paramètres du rapport")
    status: str = Field(..., description="Statut (draft, generating, completed, failed)")
    file_url: Optional[str] = Field(None, description="URL du fichier")
    file_format: Optional[str] = Field(None, description="Format du rapport")
    generated_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a généré")
    generated_at: Optional[datetime] = Field(None, description="Date de génération")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True


class ReportTemplateCreate(BaseModel):
    """Schéma pour créer un modèle de rapport."""
    name: str = Field(..., description="Nom du modèle")
    report_type: Optional[str] = Field(None, description="Type de rapport")
    template_config: Optional[Dict[str, Any]] = Field(None, description="Configuration du modèle (sections, styles, etc.)")
    is_active: Optional[bool] = Field(True, description="Actif ou non")


class ReportTemplateResponse(BaseModel):
    """Schéma de réponse pour un modèle de rapport."""
    id: str = Field(..., description="ID du modèle")
    name: str = Field(..., description="Nom du modèle")
    report_type: Optional[str] = Field(None, description="Type de rapport")
    template_config: Optional[Dict[str, Any]] = Field(None, description="Configuration du modèle")
    is_system_template: bool = Field(False, description="Modèle système ou non")
    is_active: bool = Field(True, description="Actif ou non")
    created_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a créé")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    class Config:
        from_attributes = True


class ReportScheduleCreate(BaseModel):
    """Schéma pour créer une planification de rapport."""
    report_template_id: str = Field(..., description="ID du modèle de rapport")
    schedule_type: str = Field(..., description="Type de planification (daily, weekly, monthly, quarterly, yearly)")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="Configuration de la planification (jour, heure, etc.)")
    recipients: Optional[List[str]] = Field(None, description="IDs des destinataires")
    email_subject: Optional[str] = Field(None, description="Sujet de l'email")
    email_body: Optional[str] = Field(None, description="Corps de l'email")
    is_active: Optional[bool] = Field(True, description="Actif ou non")


class ReportScheduleResponse(BaseModel):
    """Schéma de réponse pour une planification de rapport."""
    id: str = Field(..., description="ID de la planification")
    report_template_id: str = Field(..., description="ID du modèle de rapport")
    schedule_type: str = Field(..., description="Type de planification")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="Configuration de la planification")
    recipients: Optional[List[str]] = Field(None, description="IDs des destinataires")
    email_subject: Optional[str] = Field(None, description="Sujet de l'email")
    email_body: Optional[str] = Field(None, description="Corps de l'email")
    is_active: bool = Field(True, description="Actif ou non")
    next_run_at: Optional[datetime] = Field(None, description="Date de la prochaine exécution")
    last_run_at: Optional[datetime] = Field(None, description="Date de la dernière exécution")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True

