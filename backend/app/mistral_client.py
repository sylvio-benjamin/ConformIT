"""Client Mistral pour l'extraction documentaire uniquement.

Le scoring reste déterministe : Mistral n'est pas dans la boucle de décision.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_API_URL = os.getenv(
    "MISTRAL_API_URL",
    "https://api.mistral.ai/v1/chat/completions",
).strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest").strip() or "mistral-small-latest"
MISTRAL_REQUEST_GAP = float(os.getenv("MISTRAL_REQUEST_GAP", "3.5"))
MISTRAL_MAX_RETRIES = int(os.getenv("MISTRAL_MAX_RETRIES", "2"))
MISTRAL_429_WAIT_CAP = float(os.getenv("MISTRAL_429_WAIT_CAP", "12"))

_lock = asyncio.Lock()
_last_call = 0.0


def _retry_wait(response: aiohttp.ClientResponse, attempt: int) -> float:
    raw = response.headers.get("Retry-After")
    if raw:
        try:
            return min(MISTRAL_429_WAIT_CAP, max(2.0, float(raw)))
        except ValueError:
            pass
    return min(MISTRAL_429_WAIT_CAP, 4.0 * (attempt + 1))


async def _throttle() -> None:
    global _last_call
    async with _lock:
        wait = MISTRAL_REQUEST_GAP - (time.monotonic() - _last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call = time.monotonic()


async def appel_mistral_async(
    prompt: str,
    max_retries: int = MISTRAL_MAX_RETRIES,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> Tuple[str, Optional[str]]:
    if not MISTRAL_API_KEY:
        return "", "MISTRAL_API_KEY manquante dans .env"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
    }
    payload = {
        "model": MISTRAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    for attempt in range(max_retries):
        await _throttle()
        try:
            logger.debug("Mistral API call (attempt %s/%s)", attempt + 1, max_retries)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    MISTRAL_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data["choices"][0]["message"]["content"]
                        return text, None
                    error_data = await response.text()
                    error_msg = f"HTTP {response.status}: {error_data}"
                    if response.status == 429:
                        wait = _retry_wait(response, attempt)
                        logger.warning("Mistral 429, pause %ss (tentative %s)", wait, attempt + 1)
                        if attempt == max_retries - 1:
                            return "", f"Erreur API Mistral: {error_msg}"
                        await asyncio.sleep(wait)
                        continue
                    logger.error("Mistral API error (attempt %s): %s", attempt + 1, error_msg)
                    if attempt == max_retries - 1:
                        return "", f"Erreur API Mistral: {error_msg}"
                    await asyncio.sleep(2 ** attempt)
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                return "", "Erreur API Mistral: timeout"
            await asyncio.sleep(2 ** attempt)
        except Exception as exc:
            logger.error("Mistral API error (attempt %s): %s", attempt + 1, exc)
            if attempt == max_retries - 1:
                return "", f"Erreur API Mistral: {exc}"
            await asyncio.sleep(2 ** attempt)

    return "", "Erreur : Max retries atteint"


appel_groq_async = appel_mistral_async
appel_api_securise_async = appel_mistral_async
