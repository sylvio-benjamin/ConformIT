"""
Webhook Stripe pour gérer les événements de paiement (PostgreSQL).
"""

from fastapi import Request, HTTPException, APIRouter
import stripe
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.organizations import User
from app.config import STRIPE_WEBHOOK_SECRET
from app.services.plan_service import PlanService, _find_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    from app.config import BILLING_ENABLED

    if not BILLING_ENABLED:
        raise HTTPException(status_code=404, detail="Facturation désactivée")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Signature Stripe manquante")
    
    if not STRIPE_WEBHOOK_SECRET or STRIPE_WEBHOOK_SECRET == "your_stripe_webhook_secret":
        raise HTTPException(
            status_code=500,
            detail="Configuration Stripe incomplète. STRIPE_WEBHOOK_SECRET doit être défini."
        )
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # Payload invalide
        raise HTTPException(status_code=400, detail=f"Payload invalide: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        # Signature invalide - tentative de fraude
        raise HTTPException(status_code=400, detail=f"Signature invalide: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de vérification: {str(e)}")

    # Traiter les événements
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Validation des métadonnées
        metadata = session.get("metadata", {}) or {}
        organization_id = metadata.get("organization_id")
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")
        price_id = metadata.get("price_id")
        
        if not organization_id and not user_id:
            raise HTTPException(status_code=400, detail="organization_id manquant dans les métadonnées")
        
        # Si le plan n'est pas dans les métadonnées, essayer de le déterminer depuis le price_id
        if not plan and price_id:
            from app.stripe_routes import PRICE_TO_PLAN
            if price_id in PRICE_TO_PLAN:
                plan = PRICE_TO_PLAN[price_id]
            else:
                # Essayer de récupérer depuis Stripe
                try:
                    price = stripe.Price.retrieve(price_id)
                    plan = price.metadata.get("plan", "pro")
                except:
                    plan = "pro"  # Fallback
        
        if not plan:
            raise HTTPException(status_code=400, detail="plan manquant dans les métadonnées")
        
        # Normaliser le plan (support des anciens noms)
        if plan == "premium":
            plan = "pro"
        
        # Valider que le plan est valide
        valid_plans = ["basic", "pro", "enterprise"]
        if plan not in valid_plans:
            logger.warning(f"Plan invalide reçu: {plan}, utilisation de 'pro' par défaut")
            plan = "pro"
        
        try:
            # Mettre à jour le plan de l'utilisateur dans PostgreSQL
            db: Session = SessionLocal()
            try:
                from app.models.organizations import Organization

                org = None
                if organization_id:
                    org = db.query(Organization).filter(Organization.id == organization_id).first()
                user = _find_user(db, user_id) if user_id else None
                if not org and user:
                    org = user.organization
                if not org and not user:
                    raise HTTPException(status_code=404, detail="Organisation introuvable")
                if org:
                    org.plan = plan
                if user:
                    user.abonnement = plan
                db.commit()
                logger.info("Plan mis à jour org=%s user=%s plan=%s", organization_id, user_id, plan)
            except HTTPException:
                db.rollback()
                raise
            except Exception as e:
                db.rollback()
                logger.error(f"Erreur PostgreSQL lors de la mise à jour du plan: {e}")
                raise HTTPException(status_code=500, detail=f"Erreur PostgreSQL: {str(e)}")
            finally:
                db.close()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du plan: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    # Gérer les événements de souscription (annulation, mise à jour, etc.)
    elif event["type"] in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        
        # Récupérer le user_id depuis les métadonnées du client Stripe
        try:
            customer = stripe.Customer.retrieve(customer_id)
            user_id = customer.metadata.get("user_id")
            
            if user_id:
                if event["type"] == "customer.subscription.deleted":
                    # Abonnement annulé, revenir au plan basic
                    plan = "basic"
                else:
                    # Abonnement mis à jour, récupérer le plan actuel
                    # Vous pouvez récupérer le plan depuis la subscription
                    plan = "basic"  # Par défaut
                
                # Mettre à jour dans PostgreSQL
                db: Session = SessionLocal()
                try:
                    user = _find_user(db, user_id)
                    
                    if user:
                        user.abonnement = plan
                        db.commit()
                        logger.info(f"Statut d'abonnement mis à jour pour user {user_id}: {plan}")
                    else:
                        logger.warning(f"Utilisateur non trouvé pour mise à jour d'abonnement: {user_id}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Erreur lors du traitement de l'événement de souscription: {e}")
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement de souscription: {e}")

    return {"status": "ok"}
