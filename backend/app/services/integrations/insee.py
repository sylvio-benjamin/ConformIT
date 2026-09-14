"""
Service pour l'intégration INSEE.
L'INSEE fournit des données statistiques et économiques sur les entreprises françaises.
"""

import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class INSEEService:
    """Service pour interagir avec l'API INSEE."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.insee.fr/entreprises/sirene/V3"):
        """
        Initialise le service INSEE.
        
        Args:
            api_key: Clé API INSEE (nécessaire pour la plupart des endpoints)
            base_url: URL de base de l'API INSEE
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def search_siren(self, siren: str) -> Dict[str, Any]:
        """
        Recherche une entreprise par son numéro SIREN.
        
        Args:
            siren: Numéro SIREN (9 chiffres)
            
        Returns:
            Dict contenant les informations de l'entreprise
        """
        try:
            url = f"{self.base_url}/siren/{siren}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche INSEE: {e}")
            raise Exception(f"Erreur de communication avec l'INSEE: {str(e)}")
    
    def search_siret(self, siret: str) -> Dict[str, Any]:
        """
        Recherche un établissement par son numéro SIRET.
        
        Args:
            siret: Numéro SIRET (14 chiffres)
            
        Returns:
            Dict contenant les informations de l'établissement
        """
        try:
            url = f"{self.base_url}/siret/{siret}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche SIRET INSEE: {e}")
            raise Exception(f"Erreur de communication avec l'INSEE: {str(e)}")
    
    def search_by_name(self, name: str, limit: int = 20) -> Dict[str, Any]:
        """
        Recherche des entreprises par nom.
        
        Args:
            name: Nom de l'entreprise
            limit: Nombre de résultats maximum
            
        Returns:
            Dict contenant les résultats de recherche
        """
        try:
            url = f"{self.base_url}/siren"
            params = {
                "q": f"denominationUniteLegale:{name}",
                "nombre": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche par nom INSEE: {e}")
            raise Exception(f"Erreur de communication avec l'INSEE: {str(e)}")
    
    def get_economic_data(self, siren: str) -> Dict[str, Any]:
        """
        Récupère les données économiques d'une entreprise.
        
        Args:
            siren: Numéro SIREN de l'entreprise
            
        Returns:
            Dict contenant les données économiques
        """
        try:
            # Exemple: récupération des données de l'entreprise
            company_data = self.search_siren(siren)
            
            # Ici, on pourrait enrichir avec d'autres endpoints INSEE
            # selon les besoins (données financières, emploi, etc.)
            
            return company_data
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données économiques: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API INSEE.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            # Test simple avec un SIREN connu (ex: État français)
            self.search_siren("130025265")
            return True
        except Exception as e:
            logger.error(f"Test de connexion INSEE échoué: {e}")
            return False

