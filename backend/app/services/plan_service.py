"""
Service de gestion des plans et quotas d'analyse (PostgreSQL).

Gère :
- Les limites par plan (basic: 5, pro: 50, enterprise: illimité)
- Le compteur mensuel d'analyses
- La réinitialisation automatique chaque mois
- La vérification des fonctionnalités disponibles (PDF, Excel, API)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from uuid import UUID

from app.config import BILLING_ENABLED
from app.database import SessionLocal
from app.models.organizations import User
from app.models.quotas import Quota


def _find_user(db: Session, user_id: str) -> Optional[User]:
    try:
        parsed = UUID(str(user_id))
    except (ValueError, TypeError, AttributeError):
        return None
    return db.query(User).filter(User.id == parsed).first()

logger = logging.getLogger(__name__)

# Configuration des plans
PLAN_LIMITS = {
    "basic": 5,
    "pro": 50,
    "enterprise": float("inf"),  # Illimité
}

PLAN_FEATURES = {
    "basic": {
        "pdf": True,
        "excel": False,
        "api": False,
        "alerts": False,
        "collaborators": False,
        "priority_support": False,
    },
    "pro": {
        "pdf": True,
        "excel": True,
        "api": False,
        "alerts": True,
        "collaborators": False,
        "priority_support": True,
    },
    "enterprise": {
        "pdf": True,
        "excel": True,
        "api": True,
        "alerts": True,
        "collaborators": True,
        "priority_support": True,
    },
}


class PlanService:
    """Service de gestion des plans et quotas."""
    
    @staticmethod
    def get_user_plan(user_id: str) -> str:
        """
        Récupère le plan de l'utilisateur depuis PostgreSQL.
        
        Args:
            user_id: UUID utilisateur (JWT)
            
        Returns:
            Plan de l'utilisateur (default: "basic")
        """
        try:
            db: Session = SessionLocal()
            try:
                user = _find_user(db, user_id)
                
                if user and user.abonnement:
                    plan = user.abonnement
                    # Normaliser le nom du plan
                    if plan in ["basic", "pro", "enterprise"]:
                        return plan
                    # Support des anciens noms
                    if plan == "premium":
                        return "pro"
                
                # Par défaut, plan basic
                return "basic"
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du plan pour {user_id}: {e}")
            return "basic"
    
    @staticmethod
    def get_plan_limit(plan: str) -> int:
        """
        Retourne la limite d'analyses pour un plan.
        
        Args:
            plan: Nom du plan (basic, pro, enterprise)
            
        Returns:
            Limite d'analyses (inf pour enterprise)
        """
        return PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])
    
    @staticmethod
    def get_current_month_key() -> str:
        """
        Retourne la clé du mois courant (format: YYYY-MM).
        
        Returns:
            Clé du mois courant
        """
        now = datetime.now()
        return now.strftime("%Y-%m")
    
    @staticmethod
    def get_user_quota(user_id: str) -> Dict:
        """
        Récupère le quota actuel de l'utilisateur pour le mois en cours.
        
        Args:
            user_id: UUID utilisateur (JWT)
            
        Returns:
            Dictionnaire avec:
            - count: Nombre d'analyses effectuées ce mois
            - limit: Limite du plan
            - plan: Plan de l'utilisateur
            - month: Mois courant
            - reset_date: Date de réinitialisation (premier jour du mois suivant)
        """
        try:
            db: Session = SessionLocal()
            try:
                user = _find_user(db, user_id)
                if not user:
                    # Retourner un quota par défaut si l'utilisateur n'existe pas
                    return {
                        "count": 0,
                        "limit": PLAN_LIMITS["basic"],
                        "plan": "basic",
                        "month": PlanService.get_current_month_key(),
                        "reset_date": None,
                        "unlimited": False,
                    }
                
                plan = user.abonnement or "basic"
                limit = PlanService.get_plan_limit(plan)
                current_month = PlanService.get_current_month_key()
                
                # Récupérer le quota du mois courant
                quota = db.query(Quota).filter(
                    and_(
                        Quota.user_id == user.id,
                        Quota.month == current_month
                    )
                ).first()
                
                count = quota.count if quota else 0
                
                # Calculer la date de réinitialisation (premier jour du mois suivant)
                now = datetime.now()
                if now.month == 12:
                    reset_date = datetime(now.year + 1, 1, 1)
                else:
                    reset_date = datetime(now.year, now.month + 1, 1)
                
                return {
                    "count": count,
                    "limit": limit if limit != float("inf") else None,
                    "plan": plan,
                    "month": current_month,
                    "reset_date": reset_date.isoformat(),
                    "unlimited": limit == float("inf"),
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du quota pour {user_id}: {e}")
            # Retourner un quota par défaut en cas d'erreur
            return {
                "count": 0,
                "limit": PLAN_LIMITS["basic"],
                "plan": "basic",
                "month": PlanService.get_current_month_key(),
                "reset_date": None,
                "unlimited": False,
            }
    
    @staticmethod
    def can_perform_analysis(user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si l'utilisateur peut effectuer une analyse.
        
        Args:
            user_id: UUID utilisateur (JWT)
            
        Returns:
            Tuple (can_perform, error_message)
            - can_perform: True si l'utilisateur peut effectuer l'analyse
            - error_message: Message d'erreur si can_perform est False
        """
        if not BILLING_ENABLED:
            return True, None
        try:
            quota = PlanService.get_user_quota(user_id)
            
            # Plan enterprise = illimité
            if quota["unlimited"]:
                return True, None
            
            # Vérifier si la limite est atteinte
            if quota["count"] >= quota["limit"]:
                reset_date = datetime.fromisoformat(quota["reset_date"])
                days_until_reset = (reset_date - datetime.now()).days + 1
                
                error_message = (
                    f"Limite d'analyses atteinte ({quota['limit']}/{quota['limit']}). "
                    f"Le compteur sera réinitialisé dans {days_until_reset} jour(s). "
                    f"Passez au plan Pro ou Enterprise pour plus d'analyses."
                )
                return False, error_message
            
            return True, None
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du quota pour {user_id}: {e}")
            # En cas d'erreur, autoriser mais logger
            return True, None
    
    @staticmethod
    def increment_analysis_count(user_id: str) -> bool:
        """
        Incrémente le compteur d'analyses pour l'utilisateur.
        
        Args:
            user_id: UUID utilisateur (JWT)
            
        Returns:
            True si l'incrémentation a réussi
        """
        if not BILLING_ENABLED:
            return True
        try:
            db: Session = SessionLocal()
            try:
                user = _find_user(db, user_id)
                if not user:
                    logger.error(f"Utilisateur non trouvé: {user_id}")
                    return False
                
                current_month = PlanService.get_current_month_key()
                
                # Récupérer ou créer le quota du mois courant
                quota = db.query(Quota).filter(
                    and_(
                        Quota.user_id == user.id,
                        Quota.month == current_month
                    )
                ).first()
                
                if quota:
                    quota.count += 1
                    quota.last_updated = datetime.now()
                    logger.info(f"Compteur d'analyses incrémenté pour {user_id}: {quota.count}")
                else:
                    quota = Quota(
                        user_id=user.id,
                        month=current_month,
                        count=1
                    )
                    db.add(quota)
                    logger.info(f"Compteur d'analyses créé pour {user_id}: 1")
                
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"Erreur lors de l'incrémentation du compteur pour {user_id}: {e}")
                return False
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur lors de l'incrémentation du compteur pour {user_id}: {e}")
            return False
    
    @staticmethod
    def record_analysis(user_id: str, slug: str, analysis_data: Dict) -> bool:
        """
        Enregistre une analyse dans l'historique de l'utilisateur.
        
        Note: Les analyses sont maintenant stockées dans PostgreSQL via l'endpoint /analyser/
        Cette fonction est conservée pour compatibilité mais ne fait plus rien.
        
        Args:
            user_id: UUID utilisateur (JWT)
            slug: Slug de l'analyse
            analysis_data: Données de l'analyse
            
        Returns:
            True si l'enregistrement a réussi
        """
        try:
            # Les analyses sont maintenant sauvegardées directement dans PostgreSQL
            # via l'endpoint /analyser/ dans main.py
            logger.info(f"Analyse enregistrée (PostgreSQL): {user_id}/{slug}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'analyse pour {user_id}: {e}")
            return False
    
    @staticmethod
    def has_feature(user_id: str, feature: str) -> bool:
        """
        Vérifie si l'utilisateur a accès à une fonctionnalité.
        
        Args:
            user_id: UUID utilisateur (JWT)
            feature: Fonctionnalité à vérifier (pdf, excel, api)
            
        Returns:
            True si l'utilisateur a accès à la fonctionnalité
        """
        if not BILLING_ENABLED:
            return True
        try:
            plan = PlanService.get_user_plan(user_id)
            features = PLAN_FEATURES.get(plan, PLAN_FEATURES["basic"])
            return features.get(feature, False)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la fonctionnalité {feature} pour {user_id}: {e}")
            return False
    
    @staticmethod
    def reset_monthly_quotas() -> int:
        """
        Réinitialise les quotas mensuels (à appeler via une tâche cron).
        Note: Cette fonction devrait être appelée au début de chaque mois.
        
        Returns:
            Nombre de quotas réinitialisés
        """
        try:
            db: Session = SessionLocal()
            try:
                # Récupérer tous les quotas du mois précédent
                now = datetime.now()
                if now.month == 1:
                    previous_month = f"{now.year - 1}-12"
                else:
                    previous_month = f"{now.year}-{now.month - 1:02d}"
                
                quotas = db.query(Quota).filter(Quota.month == previous_month).all()
                count = len(quotas)
                
                # Les quotas sont conservés pour l'historique, mais on peut les marquer comme expirés
                # ou les supprimer si nécessaire
                logger.info(f"Quotas du mois {previous_month} trouvés: {count}")
                
                return count
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation des quotas: {e}")
            return 0
