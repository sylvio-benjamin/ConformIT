"""
Schémas Pydantic pour les KRIs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class KRICreate(BaseModel):
    """Schéma pour créer un KRI."""
    name: str = Field(..., description="Nom du KRI")
    description: Optional[str] = Field(None, description="Description détaillée")
    risk_id: Optional[str] = Field(None, description="ID du risque associé")
    category_id: Optional[str] = Field(None, description="ID de la catégorie")
    calculation_formula: Optional[str] = Field(None, description="Formule de calcul")
    data_source: Optional[str] = Field("manual", description="Source de données (API, manual, import)")
    unit: Optional[str] = Field(None, description="Unité (percentage, count, currency, etc.)")
    frequency: Optional[str] = Field("monthly", description="Fréquence (daily, weekly, monthly, quarterly)")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire")
    threshold_green: Optional[Decimal] = Field(None, description="Seuil vert")
    threshold_yellow: Optional[Decimal] = Field(None, description="Seuil jaune")
    threshold_orange: Optional[Decimal] = Field(None, description="Seuil orange")
    threshold_red: Optional[Decimal] = Field(None, description="Seuil rouge")


class KRIUpdate(BaseModel):
    """Schéma pour mettre à jour un KRI."""
    name: Optional[str] = Field(None, description="Nom du KRI")
    description: Optional[str] = Field(None, description="Description détaillée")
    calculation_formula: Optional[str] = Field(None, description="Formule de calcul")
    data_source: Optional[str] = Field(None, description="Source de données")
    frequency: Optional[str] = Field(None, description="Fréquence")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire")
    is_active: Optional[bool] = Field(None, description="Actif ou non")
    threshold_green: Optional[Decimal] = Field(None, description="Seuil vert")
    threshold_yellow: Optional[Decimal] = Field(None, description="Seuil jaune")
    threshold_orange: Optional[Decimal] = Field(None, description="Seuil orange")
    threshold_red: Optional[Decimal] = Field(None, description="Seuil rouge")


class KRIResponse(BaseModel):
    """Schéma de réponse pour un KRI."""
    id: str = Field(..., description="ID du KRI")
    code: str = Field(..., description="Code unique du KRI")
    name: str = Field(..., description="Nom du KRI")
    description: Optional[str] = Field(None, description="Description détaillée")
    risk_id: Optional[str] = Field(None, description="ID du risque associé")
    category_id: Optional[str] = Field(None, description="ID de la catégorie")
    calculation_formula: Optional[str] = Field(None, description="Formule de calcul")
    data_source: Optional[str] = Field(None, description="Source de données")
    unit: Optional[str] = Field(None, description="Unité")
    frequency: Optional[str] = Field(None, description="Fréquence")
    owner_id: Optional[str] = Field(None, description="ID du propriétaire")
    is_active: bool = Field(True, description="Actif ou non")
    threshold_green: Optional[Decimal] = Field(None, description="Seuil vert")
    threshold_yellow: Optional[Decimal] = Field(None, description="Seuil jaune")
    threshold_orange: Optional[Decimal] = Field(None, description="Seuil orange")
    threshold_red: Optional[Decimal] = Field(None, description="Seuil rouge")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

    class Config:
        from_attributes = True


class KRIMetricCreate(BaseModel):
    """Schéma pour créer une métrique KRI."""
    kri_id: str = Field(..., description="ID du KRI")
    measurement_date: datetime = Field(..., description="Date de mesure")
    value: Decimal = Field(..., description="Valeur de la métrique")
    target_value: Optional[Decimal] = Field(None, description="Valeur cible")
    data_source: Optional[str] = Field(None, description="Source de données")


class KRIMetricResponse(BaseModel):
    """Schéma de réponse pour une métrique KRI."""
    id: str = Field(..., description="ID de la métrique")
    kri_id: str = Field(..., description="ID du KRI")
    measurement_date: datetime = Field(..., description="Date de mesure")
    value: Decimal = Field(..., description="Valeur de la métrique")
    target_value: Optional[Decimal] = Field(None, description="Valeur cible")
    threshold_green: Optional[Decimal] = Field(None, description="Seuil vert")
    threshold_yellow: Optional[Decimal] = Field(None, description="Seuil jaune")
    threshold_orange: Optional[Decimal] = Field(None, description="Seuil orange")
    threshold_red: Optional[Decimal] = Field(None, description="Seuil rouge")
    status: str = Field(..., description="Statut (green, yellow, orange, red)")
    data_source: Optional[str] = Field(None, description="Source de données")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True


class KRIAlertResponse(BaseModel):
    """Schéma de réponse pour une alerte KRI."""
    id: str = Field(..., description="ID de l'alerte")
    kri_id: str = Field(..., description="ID du KRI")
    metric_id: Optional[str] = Field(None, description="ID de la métrique")
    alert_type: str = Field(..., description="Type d'alerte (threshold_exceeded, trend_change, anomaly)")
    severity: str = Field(..., description="Sévérité (low, medium, high, critical)")
    message: str = Field(..., description="Message d'alerte")
    status: str = Field(..., description="Statut (active, acknowledged, resolved)")
    acknowledged_by: Optional[str] = Field(None, description="ID de l'utilisateur qui a reconnu")
    acknowledged_at: Optional[datetime] = Field(None, description="Date de reconnaissance")
    resolved_at: Optional[datetime] = Field(None, description="Date de résolution")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        from_attributes = True

