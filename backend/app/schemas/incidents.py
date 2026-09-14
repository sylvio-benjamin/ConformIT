"""
Schémas Pydantic pour les incidents.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """Schéma pour créer un incident."""
    title: str = Field(..., description="Titre de l'incident")
    description: Optional[str] = Field(None, description="Description détaillée de l'incident")
    incident_type: Optional[str] = Field(None, description="Type d'incident (security, operational, financial, etc.)")
    severity: Optional[str] = Field("medium", description="Gravité (low, medium, high, critical)")
    impact_description: Optional[str] = Field(None, description="Description de l'impact")
    risk_ids: Optional[List[str]] = Field(None, description="IDs des risques liés")


class IncidentUpdate(BaseModel):
    """Schéma pour mettre à jour un incident."""
    title: Optional[str] = Field(None, description="Titre de l'incident")
    description: Optional[str] = Field(None, description="Description détaillée")
    incident_type: Optional[str] = Field(None, description="Type d'incident")
    severity: Optional[str] = Field(None, description="Gravité")
    status: Optional[str] = Field(None, description="Statut (reported, investigating, resolved, closed)")
    impact_description: Optional[str] = Field(None, description="Description de l'impact")


class IncidentResponse(BaseModel):
    """Schéma de réponse pour un incident."""
    id: str = Field(..., description="ID de l'incident")
    code: str = Field(..., description="Code unique de l'incident")
    title: str = Field(..., description="Titre de l'incident")
    description: Optional[str] = Field(None, description="Description détaillée")
    incident_type: Optional[str] = Field(None, description="Type d'incident")
    severity: str = Field(..., description="Gravité (low, medium, high, critical)")
    status: str = Field(..., description="Statut (reported, investigating, resolved, closed)")
    reported_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a déclaré l'incident")
    reported_at: datetime = Field(..., description="Date de déclaration")
    resolved_at: Optional[datetime] = Field(None, description="Date de résolution")
    closed_at: Optional[datetime] = Field(None, description="Date de fermeture")
    impact_description: Optional[str] = Field(None, description="Description de l'impact")
    risk_ids: Optional[List[str]] = Field(None, description="IDs des risques liés")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    class Config:
        from_attributes = True


class RootCauseAnalysisCreate(BaseModel):
    """Schéma pour créer une analyse de cause racine."""
    incident_id: str = Field(..., description="ID de l'incident")
    methodology: Optional[str] = Field("5_why", description="Méthodologie (5_why, ishikawa, fault_tree)")
    analysis: Optional[str] = Field(None, description="Analyse de cause racine")
    root_causes: Optional[List[str]] = Field(None, description="Causes racines identifiées")
    contributing_factors: Optional[List[str]] = Field(None, description="Facteurs contributifs")


class RootCauseAnalysisResponse(BaseModel):
    """Schéma de réponse pour une analyse de cause racine."""
    id: str = Field(..., description="ID de l'analyse")
    incident_id: str = Field(..., description="ID de l'incident")
    methodology: Optional[str] = Field(None, description="Méthodologie")
    analysis: Optional[str] = Field(None, description="Analyse de cause racine")
    root_causes: Optional[List[str]] = Field(None, description="Causes racines identifiées")
    contributing_factors: Optional[List[str]] = Field(None, description="Facteurs contributifs")
    analyzed_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a analysé")
    analyzed_at: datetime = Field(..., description="Date d'analyse")

    class Config:
        from_attributes = True

