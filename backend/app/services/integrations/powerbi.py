"""
Service pour l'intégration PowerBI.
PowerBI permet de générer des dashboards et rapports.
"""

import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PowerBIService:
    """Service pour interagir avec l'API PowerBI."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                 tenant_id: Optional[str] = None, base_url: str = "https://api.powerbi.com/v1.0/myorg"):
        """
        Initialise le service PowerBI.
        
        Args:
            client_id: ID client Azure AD
            client_secret: Secret client Azure AD
            tenant_id: ID du tenant Azure AD
            base_url: URL de base de l'API PowerBI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.base_url = base_url
        self.access_token: Optional[str] = None
        
        if client_id and client_secret and tenant_id:
            self._authenticate()
    
    def _authenticate(self) -> None:
        """Authentifie le service avec Azure AD."""
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://analysis.windows.net/powerbi/api/.default",
                "grant_type": "client_credentials"
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            if not self.access_token:
                raise Exception("Impossible d'obtenir le token d'accès")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'authentification PowerBI: {e}")
            raise Exception(f"Erreur d'authentification PowerBI: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Retourne les headers avec le token d'authentification."""
        if not self.access_token:
            raise Exception("Non authentifié. Veuillez fournir les identifiants.")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des workspaces.
        
        Returns:
            Liste des workspaces
        """
        try:
            url = f"{self.base_url}/groups"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des workspaces: {e}")
            raise Exception(f"Erreur de communication avec PowerBI: {str(e)}")
    
    def get_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère la liste des datasets.
        
        Args:
            workspace_id: ID du workspace (optionnel, utilise le workspace par défaut sinon)
            
        Returns:
            Liste des datasets
        """
        try:
            if workspace_id:
                url = f"{self.base_url}/groups/{workspace_id}/datasets"
            else:
                url = f"{self.base_url}/datasets"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des datasets: {e}")
            raise Exception(f"Erreur de communication avec PowerBI: {str(e)}")
    
    def create_dataset(self, dataset_config: Dict[str, Any], workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée un nouveau dataset.
        
        Args:
            dataset_config: Configuration du dataset
            workspace_id: ID du workspace (optionnel)
            
        Returns:
            Dict contenant les informations du dataset créé
        """
        try:
            if workspace_id:
                url = f"{self.base_url}/groups/{workspace_id}/datasets"
            else:
                url = f"{self.base_url}/datasets"
            
            response = requests.post(url, headers=self._get_headers(), json=dataset_config, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la création du dataset: {e}")
            raise Exception(f"Erreur de communication avec PowerBI: {str(e)}")
    
    def get_reports(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère la liste des rapports.
        
        Args:
            workspace_id: ID du workspace (optionnel)
            
        Returns:
            Liste des rapports
        """
        try:
            if workspace_id:
                url = f"{self.base_url}/groups/{workspace_id}/reports"
            else:
                url = f"{self.base_url}/reports"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des rapports: {e}")
            raise Exception(f"Erreur de communication avec PowerBI: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API PowerBI.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            return False
        
        try:
            self.get_workspaces()
            return True
        except Exception as e:
            logger.error(f"Test de connexion PowerBI échoué: {e}")
            return False

