"""Alertes métier — le webhook Make.com n'est jamais exposé au navigateur."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import MAKE_WEBHOOK_SECRET, MAKE_WEBHOOK_URL
from app.core.permissions import get_current_user
from app.models.organizations import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class HighRiskAlert(BaseModel):
    entreprise: str
    risque: str
    score: Optional[Union[float, int]] = None
    rcs: str = ""


def _post_webhook(payload: dict, headers: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = Request(MAKE_WEBHOOK_URL, data=data, headers=headers, method="POST")
    with urlopen(request, timeout=5) as response:
        if response.status >= 400:
            raise RuntimeError(f"webhook HTTP {response.status}")


@router.post("/high-risk")
async def notify_high_risk(
    body: HighRiskAlert,
    user: User = Depends(get_current_user),
):
    if not MAKE_WEBHOOK_URL:
        return {"sent": False, "reason": "webhook_disabled"}
    payload = {
        "entreprise": body.entreprise,
        "risque": body.risque,
        "score": body.score,
        "rcs": body.rcs,
        "email": user.email,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "date": datetime.now(timezone.utc).isoformat(),
    }
    headers = {"Content-Type": "application/json"}
    if MAKE_WEBHOOK_SECRET:
        headers["X-DocAnalyse-Secret"] = MAKE_WEBHOOK_SECRET
    try:
        await asyncio.to_thread(_post_webhook, payload, headers)
        return {"sent": True}
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
        logger.warning("Webhook alerte non envoyé: %s", exc)
        return {"sent": False, "reason": "webhook_failed"}
    except Exception as exc:
        logger.warning("Webhook alerte non envoyé: %s", exc)
        return {"sent": False, "reason": "webhook_failed"}
