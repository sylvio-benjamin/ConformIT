"""
Schémas Pydantic pour la validation des entrées API.
Fichiers uploadés, analyses, etc.
"""

import os
import re
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


class AnalyseRequest(BaseModel):
    """Schéma pour la requête d'analyse de document."""
    pass  # Le fichier PDF est géré via UploadFile


class AnalyseResponse(BaseModel):
    """Schéma pour la réponse d'analyse."""
    message: str
    slug: str


class ResultatResponse(BaseModel):
    """Schéma pour le résultat d'analyse."""
    nom: str
    type: str
    rcs: str
    score_total: int
    risque: Literal["Low", "Medium", "High", "Critical"]
    precision: float
    qualite: Optional[str] = None
    details: list[dict]
    analyseTerminee: bool = True


class WebhookStripeRequest(BaseModel):
    """Schéma pour les webhooks Stripe (validation interne)."""
    type: str
    data: dict


class ModifierAnalyseRequest(BaseModel):
    """Schéma pour la modification d'analyse."""
    nom: Optional[str] = None
    type: Optional[str] = None
    rcs: Optional[str] = None
    score_total: Optional[int] = None
    risque: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    precision: Optional[float] = None
    details: Optional[list[dict]] = None


class UploadFileValidation:
    """Classe utilitaire pour valider les fichiers uploadés."""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_MIME_TYPES = [
        "application/pdf",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    ALLOWED_EXTENSIONS = [".pdf", ".csv", ".xls", ".xlsx"]
    COMPTES_SOCIAUX_EXTENSIONS = {".csv", ".xls", ".xlsx"}  # Extensions pour comptes sociaux
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Vérifie que la taille du fichier est acceptable."""
        return file_size <= UploadFileValidation.MAX_FILE_SIZE
    
    @staticmethod
    def validate_mime_type(mime_type: Optional[str]) -> bool:
        """Vérifie que le type MIME est acceptable."""
        if not mime_type:
            return False
        return mime_type in UploadFileValidation.ALLOWED_MIME_TYPES
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Vérifie que le nom de fichier est valide."""
        if not filename:
            return False
        # Vérifier l'extension
        for ext in UploadFileValidation.ALLOWED_EXTENSIONS:
            if filename.lower().endswith(ext):
                return True
        return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Nettoie le nom de fichier pour éviter les problèmes de sécurité."""
        # Enlever les caractères dangereux
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limiter la longueur
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        return filename

    @staticmethod
    def infer_document_type(extension: str, filename: Optional[str] = None) -> Optional[str]:
        """Détermine le type de document en fonction de l'extension et du nom de fichier."""
        if not extension:
            return None
        ext = extension.lower()
        
        # Détection depuis l'extension
        if ext in UploadFileValidation.COMPTES_SOCIAUX_EXTENSIONS:
            return "comptes_sociaux"
        
        # Détection depuis le nom de fichier (pour les PDFs)
        if filename and ext == ".pdf":
            filename_lower = filename.lower()
            
            # Patterns pour détecter Kbis (priorité haute car très spécifique)
            if any(pattern in filename_lower for pattern in ["kbis", "rcs", "extrait"]):
                return "extrait_kbis"
            
            # Patterns pour détecter attestation
            if any(pattern in filename_lower for pattern in ["attestation", "assurance", "police"]):
                return "attestation_assurance"
            
            # Patterns pour détecter statuts
            if any(pattern in filename_lower for pattern in ["statuts", "statut", "pacte", "reglement"]):
                return "statuts"
            
            # Patterns pour détecter les comptes sociaux (bilan + compte de résultat) - PRIORITÉ HAUTE
            # Car les comptes sociaux contiennent souvent les mots "bilan" et "compte de résultat"
            if any(pattern in filename_lower for pattern in [
                "comptes sociaux", "comptessociaux", "comptes-sociaux",
                "comptes annuels", "comptesannuels", "comptes-annuels",
                "annexe comptable", "annexe-comptable"
            ]):
                return "comptes_sociaux"
            
            # Patterns pour détecter compte de résultat (AVANT bilan pour éviter les conflits)
            # Si le fichier contient "compte de résultat" mais pas "bilan", c'est probablement un compte de résultat seul
            if any(pattern in filename_lower for pattern in [
                "compte de resultat", "compte-resultat", "compte_resultat", "compte_resultat"
            ]) and "bilan" not in filename_lower:
                return "compte_resultat"
            
            # Patterns pour détecter relevé bancaire
            if any(pattern in filename_lower for pattern in [
                "releve bancaire", "relevé bancaire", "releve-bancaire", "relevé-bancaire",
                "releve de compte", "relevé de compte", "releve-de-compte", "relevé-de-compte",
                "extrait de compte", "extrait-de-compte", "extrait compte"
            ]):
                return "releve_bancaire"
            
            # Patterns pour détecter liasse fiscale
            if any(pattern in filename_lower for pattern in [
                "liasse fiscale", "liasse-fiscale", "liassefiscale", "liasse fiscale"
            ]):
                return "liasse_fiscale"
            
            # Patterns pour détecter statuts (AVANT bilan pour éviter les conflits)
            if any(pattern in filename_lower for pattern in [
                "statuts", "statut", "pacte", "reglement interieur", "reglement-interieur",
                "reglement intérieur", "règlement intérieur"
            ]):
                return "statuts"
            
            # Patterns pour détecter les comptes sociaux via "bilan" (si pas déjà détecté comme compte de résultat)
            # Attention : "bilan" peut aussi apparaître dans un compte de résultat, donc on vérifie d'abord
            if "bilan" in filename_lower and "compte de resultat" not in filename_lower:
                # Si le fichier contient "bilan" mais pas "compte de résultat", 
                # c'est probablement des comptes sociaux (qui incluent le bilan)
                return "comptes_sociaux"
            
            # Patterns pour détecter autorisation commerciale
            if any(pattern in filename_lower for pattern in [
                "autorisation", "permis", "licence", "autorisation commerciale",
                "autorisation-commerciale", "autorisationcommerciale"
            ]):
                return "autorisation_commerciale"
        
        return None

