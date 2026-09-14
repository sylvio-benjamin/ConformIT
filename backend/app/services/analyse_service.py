"""
Service pour la logique métier d'analyse de documents.
"""

import os
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

from app.calculs.calculs_kbis import analyser_et_calculer
from app.models import AnalyseData


class AnalyseService:
    """Service pour gérer les analyses de documents."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.audits_dir = self.base_dir / "audits"
        self.reponses_dir = self.base_dir / "reponses"
        self.uploads_dir = self.base_dir / "uploads"
        
        # Créer les dossiers si nécessaire
        self.audits_dir.mkdir(exist_ok=True)
        self.reponses_dir.mkdir(exist_ok=True)
        self.uploads_dir.mkdir(exist_ok=True)
    
    def extraire_numero_rcs(self, justification: str) -> str:
        """
        Extrait le numéro RCS d'une justification.
        
        Args:
            justification: Texte contenant potentiellement un numéro RCS
            
        Returns:
            Numéro RCS ou "Non trouvé" / "Pas de RCS"
        """
        if not justification:
            return "Pas de RCS"
        
        match = re.search(r"\b(\d{3,}\s?\d{3,}\s?\d{3,})\b", justification)
        if match:
            return match.group(1).replace(" ", "")
        return "Non trouvé"
    
    def calculer_resultats(self, reponses: Dict[int, Any]) -> Dict[str, Any]:
        """
        Calcule les résultats d'analyse à partir des réponses.
        
        Args:
            reponses: Dictionnaire avec les numéros de questions et leurs réponses
            
        Returns:
            Dictionnaire avec score_total, niveau_risque, precision, scores_detail
        """
        return analyser_et_calculer(reponses)
    
    def sauvegarder_analyse(self, slug: str, data: AnalyseData) -> bool:
        """
        Sauvegarde une analyse dans un fichier JSON.
        
        Args:
            slug: Identifiant unique de l'analyse
            data: Données d'analyse à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            json_path = self.audits_dir / f"{slug}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de l'analyse : {e}")
            return False
    
    def charger_analyse(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Charge une analyse depuis un fichier JSON.
        
        Args:
            slug: Identifiant unique de l'analyse
            
        Returns:
            Dictionnaire avec les données d'analyse ou None si non trouvé
        """
        json_path = self.audits_dir / f"{slug}.json"
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'analyse : {e}")
            return None
    
    def creer_analyse_data(self, slug: str, reponses: Dict[int, Any], 
                           justifications: Dict[int, str],
                           questions: Dict[int, str]) -> AnalyseData:
        """
        Crée un objet AnalyseData à partir des réponses collectées.
        
        Args:
            slug: Identifiant unique de l'analyse
            reponses: Dictionnaire avec les numéros de questions et leurs réponses
            justifications: Dictionnaire avec les justifications
            questions: Dictionnaire avec les questions
            
        Returns:
            Objet AnalyseData
        """
        # Calculer les résultats
        resultats = self.calculer_resultats(reponses)
        
        # Extraire les informations spécifiques
        a_un_rcs = reponses.get(2, "")
        justification_rcs = justifications.get(2, "")
        
        if a_un_rcs and str(a_un_rcs).lower() == "oui":
            numero_rcs = self.extraire_numero_rcs(justification_rcs)
        else:
            numero_rcs = "Pas de RCS"
        
        # Créer les détails
        details = []
        for i in range(2, 14):
            if i in questions:
                details.append({
                    "question": questions[i],
                    "reponse": str(reponses.get(i, "")),
                    "justification": justifications.get(i, "Aucune justification")
                })
        
        return AnalyseData(
            slug=slug,
            nom=slug,
            type=str(reponses.get(3, "")),
            rcs=numero_rcs,
            score_total=resultats["score_total"],
            risque=resultats["niveau_risque"],
            precision=resultats["precision"],
            qualite=f"{resultats['precision']}%",
            details=details
        )

