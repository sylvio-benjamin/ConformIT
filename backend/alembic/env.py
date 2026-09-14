from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import DIRECT_DATABASE_URL
from app.database import Base
import app.models  # noqa: F401 — enregistre les tables existantes

if not DIRECT_DATABASE_URL or "localhost" in DIRECT_DATABASE_URL or "127.0.0.1" in DIRECT_DATABASE_URL:
    raise RuntimeError(
        "Alembic n'a pas d'URL Neon. Crée backend/.env.local avec "
        "DATABASE_URL et DIRECT_DATABASE_URL (connexion directe, pas le pooler). "
        "Modèle : .env.example à la racine du repo."
    )

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", DIRECT_DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DIRECT_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
