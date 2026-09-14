"""
Configuration de l'application via variables d'environnement.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env.local / .env
# config.py = backend/app/config.py → parents[1]=backend, parents[2]=racine repo
_repo_root = Path(__file__).resolve().parents[2]
_backend_root = Path(__file__).resolve().parents[1]
env_paths = [
    _backend_root / ".env.local",
    _repo_root / ".env.local",
    _backend_root / ".env",
    _repo_root / ".env",
    Path(__file__).resolve().parents[0] / ".env.local",
    Path.cwd().parent / ".env.local",
    Path.cwd() / ".env.local",
]

env_path = None
for path in env_paths:
    if path.exists():
        env_path = path
        break

if env_path:
    try:
        load_dotenv(dotenv_path=env_path, encoding='utf-8')
        print(f"[OK] Variables d'environnement chargees depuis: {env_path}")
    except UnicodeDecodeError:
        # Essayer avec l'encodage Windows
        try:
            load_dotenv(dotenv_path=env_path, encoding='latin-1')
            print(f"[OK] Variables d'environnement chargees depuis: {env_path} (encodage latin-1)")
        except Exception as e:
            print(f"[WARN] Erreur lors du chargement de .env.local: {e}")
            load_dotenv()  # Charger depuis l'environnement système
else:
    print("[WARN] ATTENTION: .env.local non trouve dans les chemins suivants:")
    for path in env_paths:
        print(f"   - {path}")
    # Charger quand même (peut être défini ailleurs)
    load_dotenv()

# Extraction IA uniquement (pas le scoring).
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest").strip()

# Configuration Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Initialiser Stripe si la clé est disponible
if STRIPE_SECRET_KEY:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

# Configuration PostgreSQL / Neon
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "grc_db")

def _normalize_pg_url(url: str) -> str:
    """psycopg2 + SQLAlchemy : driver explicite, sans channel_binding (souvent cassé hors libpq récent)."""
    if not url:
        return url
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    url = url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?")
    url = url.replace("?channel_binding=require", "")
    return url


# DATABASE_URL (Neon pooler) prime sur POSTGRES_URL / host local
_raw_database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if _raw_database_url:
    POSTGRES_URL = _normalize_pg_url(_raw_database_url)
else:
    POSTGRES_URL = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

DIRECT_DATABASE_URL = _normalize_pg_url(os.getenv("DIRECT_DATABASE_URL") or POSTGRES_URL)

# Billing conservé (Stripe, plans, quotas) mais déconnecté du métier par défaut.
BILLING_ENABLED = os.getenv("BILLING_ENABLED", "false").strip().lower() in ("1", "true", "yes")

# Auth FastAPI
from app.core.runtime_config import (
    parse_cors_origins,
    resolve_jwt_secret,
    validate_runtime_config,
    validate_storage_config,
)

ENV = os.getenv("ENV", "development").strip().lower() or "development"
IS_DEVELOPMENT = ENV == "development"
JWT_SECRET = resolve_jwt_secret(os.getenv("JWT_SECRET", ""), ENV)
JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", "15"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))
COOKIE_SECURE = ENV == "production"
BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()

# Configuration CORS — localhost seulement en development
CORS_ORIGINS = parse_cors_origins(os.getenv("CORS_ORIGINS", ""), ENV)

# Configuration Frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000" if IS_DEVELOPMENT else "")

# Chiffrement intégrations — pas de génération au boot si absente.
# En development, get_encryption_key() pourra créer une clé éphémère à la première utilisation.
_raw_encryption_key = os.getenv("ENCRYPTION_KEY", "").strip()
ENCRYPTION_KEY = _raw_encryption_key
ENCRYPTION_KEY_EPHEMERAL = bool(IS_DEVELOPMENT and not _raw_encryption_key)
if ENCRYPTION_KEY_EPHEMERAL:
    print("[WARN] ENCRYPTION_KEY absente : clé éphémère de développement au premier usage (non persistante)")

# Stockage : local = défaut dev ; r2 = cible go-live (API S3-compatible, noms S3_*).
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").strip().lower()
STORAGE_ROOT = os.getenv("STORAGE_ROOT", str(_repo_root / "data"))
STORAGE_CACHE = os.getenv("STORAGE_CACHE", "").strip()
S3_BUCKET = os.getenv("S3_BUCKET", "").strip()
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "").strip()
S3_REGION = os.getenv("S3_REGION", "us-east-1").strip() or "us-east-1"
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "").strip()
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "").strip()
S3_PREFIX = os.getenv("S3_PREFIX", "").strip()

# Rate limits
RATE_LIMIT_LOGIN_IP = int(os.getenv("RATE_LIMIT_LOGIN_IP", "8"))
RATE_LIMIT_LOGIN_EMAIL = int(os.getenv("RATE_LIMIT_LOGIN_EMAIL", "5"))
RATE_LIMIT_LOGIN_WINDOW = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "60"))
RATE_LIMIT_ANALYSE_IP = int(os.getenv("RATE_LIMIT_ANALYSE_IP", "30"))
RATE_LIMIT_ANALYSE_USER = int(os.getenv("RATE_LIMIT_ANALYSE_USER", "10"))
RATE_LIMIT_ANALYSE_ORG = int(os.getenv("RATE_LIMIT_ANALYSE_ORG", "20"))
RATE_LIMIT_ANALYSE_WINDOW = int(os.getenv("RATE_LIMIT_ANALYSE_WINDOW", "3600"))

if not MISTRAL_API_KEY:
    print("[WARN] MISTRAL_API_KEY n'est pas definie : l'extraction IA des questions sera indisponible")

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "").strip()
MAKE_WEBHOOK_SECRET = os.getenv("MAKE_WEBHOOK_SECRET", "").strip()

validate_runtime_config(
    env=ENV,
    jwt_secret=JWT_SECRET,
    encryption_key=ENCRYPTION_KEY,
    cors_origins=CORS_ORIGINS,
)
validate_storage_config(
    storage_backend=STORAGE_BACKEND,
    s3_bucket=S3_BUCKET,
    s3_access_key=S3_ACCESS_KEY,
    s3_secret_key=S3_SECRET_KEY,
    s3_endpoint=S3_ENDPOINT,
)

