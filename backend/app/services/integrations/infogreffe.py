"""
Service pour l'intégration Infogreffe.
Infogreffe permet de récupérer les données d'entreprises françaises.
"""

import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class InfogreffeService:
    """Service pour interagir avec l'API Infogreffe."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infogreffe.fr/v1"):
        """
        Initialise le service Infogreffe.
        
        Args:
            api_key: Clé API Infogreffe (optionnel pour certaines requêtes publiques)
            base_url: URL de base de l'API Infogreffe
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def search_company(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Recherche une entreprise par nom ou SIREN.
        
        Args:
            query: Nom de l'entreprise ou SIREN
            limit: Nombre de résultats maximum
            
        Returns:
            Dict contenant les résultats de recherche
        """
        try:
            url = f"{self.base_url}/companies/search"
            params = {
                "q": query,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche Infogreffe: {e}")
            raise Exception(f"Erreur de communication avec Infogreffe: {str(e)}")
    
    def get_company_details(self, siren: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son SIREN.
        
        Args:
            siren: Numéro SIREN de l'entreprise
            
        Returns:
            Dict contenant les détails de l'entreprise
        """
        try:
            url = f"{self.base_url}/companies/{siren}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des détails Infogreffe: {e}")
            raise Exception(f"Erreur de communication avec Infogreffe: {str(e)}")
    
    def get_company_rcs(self, rcs: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une entreprise par son numéro RCS.
        
        Args:
            rcs: Numéro RCS (ex: "B 123 456 789")
            
        Returns:
            Dict contenant les informations de l'entreprise
        """
        try:
            url = f"{self.base_url}/companies/rcs/{rcs}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération RCS Infogreffe: {e}")
            raise Exception(f"Erreur de communication avec Infogreffe: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Infogreffe.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            # Test simple avec une recherche générique
            self.search_company("test", limit=1)
            return True
        except Exception as e:
            logger.error(f"Test de connexion Infogreffe échoué: {e}")
            return False

