"""
Service pour l'intégration Dun & Bradstreet.
Dun & Bradstreet fournit des données financières et de crédit sur les entreprises.
"""

import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DunBradstreetService:
    """Service pour interagir avec l'API Dun & Bradstreet."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://plus.dnb.com/v1"):
        """
        Initialise le service Dun & Bradstreet.
        
        Args:
            api_key: Clé API Dun & Bradstreet (nécessaire)
            base_url: URL de base de l'API Dun & Bradstreet
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def search_company(self, name: str, country: str = "FR", limit: int = 10) -> Dict[str, Any]:
        """
        Recherche une entreprise par nom.
        
        Args:
            name: Nom de l'entreprise
            country: Code pays (FR par défaut)
            limit: Nombre de résultats maximum
            
        Returns:
            Dict contenant les résultats de recherche
        """
        try:
            url = f"{self.base_url}/companies/search"
            params = {
                "name": name,
                "country": country,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche Dun & Bradstreet: {e}")
            raise Exception(f"Erreur de communication avec Dun & Bradstreet: {str(e)}")
    
    def get_company_details(self, duns: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une entreprise par son numéro DUNS.
        
        Args:
            duns: Numéro DUNS (Data Universal Numbering System)
            
        Returns:
            Dict contenant les détails de l'entreprise
        """
        try:
            url = f"{self.base_url}/companies/{duns}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des détails Dun & Bradstreet: {e}")
            raise Exception(f"Erreur de communication avec Dun & Bradstreet: {str(e)}")
    
    def get_credit_score(self, duns: str) -> Dict[str, Any]:
        """
        Récupère le score de crédit d'une entreprise.
        
        Args:
            duns: Numéro DUNS de l'entreprise
            
        Returns:
            Dict contenant le score de crédit et les informations associées
        """
        try:
            url = f"{self.base_url}/companies/{duns}/credit-score"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du score de crédit: {e}")
            raise Exception(f"Erreur de communication avec Dun & Bradstreet: {str(e)}")
    
    def get_financial_data(self, duns: str) -> Dict[str, Any]:
        """
        Récupère les données financières d'une entreprise.
        
        Args:
            duns: Numéro DUNS de l'entreprise
            
        Returns:
            Dict contenant les données financières
        """
        try:
            url = f"{self.base_url}/companies/{duns}/financials"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des données financières: {e}")
            raise Exception(f"Erreur de communication avec Dun & Bradstreet: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Dun & Bradstreet.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        if not self.api_key:
            return False
        
        try:
            # Test simple avec une recherche
            self.search_company("test", limit=1)
            return True
        except Exception as e:
            logger.error(f"Test de connexion Dun & Bradstreet échoué: {e}")
            return False

