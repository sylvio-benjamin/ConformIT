"""
Schémas Pydantic pour les contrôles.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ControlCreate(BaseModel):
    """Schéma pour créer un contrôle."""
    name: str = Field(..., description="Nom du contrôle")
    description: Optional[str] = Field(None, description="Description détaillée du contrôle")
    control_type: Optional[str] = Field(None, description="Type de contrôle (preventive, detective, corrective)")
    control_category: Optional[str] = Field(None, description="Catégorie de contrôle (technical, administrative, physical)")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du contrôle")
    documentation_url: Optional[str] = Field(None, description="URL de la documentation")


class ControlUpdate(BaseModel):
    """Schéma pour mettre à jour un contrôle."""
    name: Optional[str] = Field(None, description="Nom du contrôle")
    description: Optional[str] = Field(None, description="Description détaillée du contrôle")
    control_type: Optional[str] = Field(None, description="Type de contrôle")
    control_category: Optional[str] = Field(None, description="Catégorie de contrôle")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du contrôle")
    status: Optional[str] = Field(None, description="Statut (planned, in_progress, completed, verified)")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="Évaluation de l'efficacité (1-5)")
    documentation_url: Optional[str] = Field(None, description="URL de la documentation")


class ControlResponse(BaseModel):
    """Schéma de réponse pour un contrôle."""
    id: str = Field(..., description="ID du contrôle")
    code: str = Field(..., description="Code unique du contrôle")
    name: str = Field(..., description="Nom du contrôle")
    description: Optional[str] = Field(None, description="Description détaillée du contrôle")
    control_type: Optional[str] = Field(None, description="Type de contrôle")
    control_category: Optional[str] = Field(None, description="Catégorie de contrôle")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire du contrôle")
    status: str = Field(..., description="Statut (planned, in_progress, completed, verified)")
    effectiveness_rating: Optional[int] = Field(None, description="Évaluation de l'efficacité (1-5)")
    last_test_date: Optional[datetime] = Field(None, description="Date du dernier test")
    next_test_date: Optional[datetime] = Field(None, description="Date du prochain test")
    documentation_url: Optional[str] = Field(None, description="URL de la documentation")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    class Config:
        from_attributes = True


class ActionPlanCreate(BaseModel):
    """Schéma pour créer un plan d'action."""
    control_id: Optional[str] = Field(None, description="ID du contrôle")
    risk_id: Optional[str] = Field(None, description="ID du risque")
    title: str = Field(..., description="Titre du plan d'action")
    description: Optional[str] = Field(None, description="Description détaillée")
    assigned_to: Optional[str] = Field(None, description="ID du responsable")
    due_date: Optional[datetime] = Field(None, description="Date d'échéance")
    priority: Optional[str] = Field("medium", description="Priorité (low, medium, high, critical)")


class ActionPlanResponse(BaseModel):
    """Schéma de réponse pour un plan d'action."""
    id: str = Field(..., description="ID du plan d'action")
    control_id: Optional[str] = Field(None, description="ID du contrôle")
    risk_id: Optional[str] = Field(None, description="ID du risque")
    title: str = Field(..., description="Titre du plan d'action")
    description: Optional[str] = Field(None, description="Description détaillée")
    assigned_to: Optional[str] = Field(None, description="ID du responsable")
    due_date: Optional[datetime] = Field(None, description="Date d'échéance")
    status: str = Field(..., description="Statut (planned, in_progress, completed, cancelled)")
    priority: Optional[str] = Field(None, description="Priorité (low, medium, high, critical)")
    completion_percentage: int = Field(0, ge=0, le=100, description="Pourcentage de complétion")
    completed_at: Optional[datetime] = Field(None, description="Date de complétion")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    class Config:
        from_attributes = True

