"""
Modèles de données pour l'application.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class AnalyseData:
    """Modèle de données pour une analyse."""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le modèle en dictionnaire."""
        return {
            "nom": self.nom,
            "type": self.type,
            "rcs": self.rcs,
            "score_total": self.score_total,
            "risque": self.risque,
            "precision": self.precision,
            "qualite": self.qualite or self.precision,
            "details": self.details or [],
            "analyseTerminee": True
        }


@dataclass
class QuestionReponse:
    """Modèle pour une question et sa réponse."""
    numero: int
    question: str
    reponse: str
    justification: Optional[str] = None
    score: Optional[int] = None

