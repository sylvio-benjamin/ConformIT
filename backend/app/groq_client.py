"""Compatibilité : l'extraction IA passe par Mistral."""

from app.mistral_client import appel_api_securise_async, appel_groq_async, appel_mistral_async

__all__ = ["appel_api_securise_async", "appel_groq_async", "appel_mistral_async"]
