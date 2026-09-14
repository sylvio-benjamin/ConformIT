"""Checkout Stripe — monté uniquement si BILLING_ENABLED=true."""
import stripe
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from app.config import BILLING_ENABLED, FRONTEND_URL, STRIPE_SECRET_KEY
from app.core.permissions import get_current_user
from app.models.organizations import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

PRICE_TO_PLAN = {
    "price_1Rc3QoRoX6cVFKbCwlZwv9C0": "basic",
    "price_1Rc3SrRoX6cVFKbCgYeQOlRB": "pro",
    "price_1Rc3SrRoX6cVFKbCzoGZPRgj": "pro",
    "price_1Rc3TaRoX6cVFKbCsZnt4paC": "enterprise",
    "price_1Rc3U4RoX6cVFKbCYNYIDQ6s": "enterprise",
}

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class CheckoutBody(BaseModel):
    plan_id: str
    plan: Optional[str] = None


@router.post("/create-checkout-session/")
async def create_checkout_session(
    body: CheckoutBody,
    user: User = Depends(get_current_user),
):
    if not BILLING_ENABLED:
        raise HTTPException(status_code=404, detail="Facturation désactivée")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")

    plan_id = body.plan_id
    plan_name = body.plan
    if not plan_name and plan_id in PRICE_TO_PLAN:
        plan_name = PRICE_TO_PLAN[plan_id]
    elif not plan_name:
        plan_name = "pro"
    if plan_name not in {"basic", "pro", "enterprise"}:
        plan_name = "pro"

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": plan_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{FRONTEND_URL}/abonnement/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/abonnement/cancelled",
            metadata={
                "organization_id": str(user.organization_id),
                "user_id": str(user.id),
                "plan": plan_name,
                "price_id": plan_id,
            },
        )
        logger.info(
            "Session Stripe créée org=%s user=%s plan=%s",
            user.organization_id,
            user.id,
            plan_name,
        )
        return JSONResponse({"url": checkout_session.url})
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=500, detail=f"Erreur Stripe: {exc}") from exc
