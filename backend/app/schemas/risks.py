"""
Schémas Pydantic pour les risques.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class RiskCreate(BaseModel):
    """Schéma pour créer un risque."""
    title: str = Field(..., description="Titre du risque")
    description: Optional[str] = Field(None, description="Description détaillée du risque")
    category_id: Optional[str] = Field(None, description="ID de la catégorie de risque")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du risque")
    parent_risk_id: Optional[str] = Field(None, description="ID du risque parent (pour hiérarchie)")
    priority: Optional[str] = Field(None, description="Priorité (low, medium, high, critical)")
    tags: Optional[List[str]] = Field(None, description="Tags personnalisés")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées personnalisées")


class RiskUpdate(BaseModel):
    """Schéma pour mettre à jour un risque."""
    title: Optional[str] = Field(None, description="Titre du risque")
    description: Optional[str] = Field(None, description="Description détaillée du risque")
    category_id: Optional[str] = Field(None, description="ID de la catégorie de risque")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du risque")
    status: Optional[str] = Field(None, description="Statut (identified, assessed, treated, accepted, closed)")
    priority: Optional[str] = Field(None, description="Priorité (low, medium, high, critical)")
    tags: Optional[List[str]] = Field(None, description="Tags personnalisés")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées personnalisées")


class RiskResponse(BaseModel):
    """Schéma de réponse pour un risque."""
    id: str = Field(..., description="ID du risque")
    code: str = Field(..., description="Code unique du risque (RISK-001, RISK-002, etc.)")
    title: str = Field(..., description="Titre du risque")
    description: Optional[str] = Field(None, description="Description détaillée du risque")
    category_id: Optional[str] = Field(None, description="ID de la catégorie de risque")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du risque")
    status: str = Field(..., description="Statut (identified, assessed, treated, accepted, closed)")
    priority: Optional[str] = Field(None, description="Priorité (low, medium, high, critical)")
    tags: Optional[List[str]] = Field(None, description="Tags personnalisés")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées personnalisées")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")
    closed_at: Optional[datetime] = Field(None, description="Date de fermeture")

    class Config:
        from_attributes = True


class RiskAssessmentCreate(BaseModel):
    """Schéma pour créer une évaluation de risque."""
    risk_id: str = Field(..., description="ID du risque")
    probability_level: int = Field(..., ge=1, le=5, description="Niveau de probabilité (1-5)")
    impact_level: int = Field(..., ge=1, le=5, description="Niveau d'impact (1-5)")
    methodology: Optional[str] = Field("qualitative", description="Méthodologie (qualitative, quantitative, semi-quantitative)")
    justification: Optional[str] = Field(None, description="Justification de l'évaluation")
    confidence_level: Optional[int] = Field(5, ge=1, le=5, description="Niveau de confiance (1-5)")


class RiskAssessmentResponse(BaseModel):
    """Schéma de réponse pour une évaluation de risque."""
    id: str = Field(..., description="ID de l'évaluation")
    risk_id: str = Field(..., description="ID du risque")
    assessed_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a évalué")
    assessment_date: datetime = Field(..., description="Date d'évaluation")
    probability_level: int = Field(..., description="Niveau de probabilité (1-5)")
    impact_level: int = Field(..., description="Niveau d'impact (1-5)")
    risk_level: str = Field(..., description="Niveau de risque (low, medium, high, critical)")
    risk_score: int = Field(..., description="Score de risque (0-100)")
    methodology: Optional[str] = Field(None, description="Méthodologie")
    justification: Optional[str] = Field(None, description="Justification")
    confidence_level: Optional[int] = Field(None, description="Niveau de confiance (1-5)")

    class Config:
        from_attributes = True

