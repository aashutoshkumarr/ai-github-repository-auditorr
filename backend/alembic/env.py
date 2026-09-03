import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ensure backend package is importable
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# import the app metadata
from backend.app.core.database import Base
from backend.app.core.config import settings

# Provide target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Override sqlalchemy.url if provided via env
db_url = os.getenv('DATABASE_URL') or getattr(settings, 'DATABASE_URL', None)
if db_url:
    config.set_main_option('sqlalchemy.url', db_url)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode, supporting async engines."""
    from sqlalchemy.ext.asyncio import create_async_engine
    import asyncio

    db_url = config.get_main_option('sqlalchemy.url')
    if not db_url:
        raise RuntimeError('No sqlalchemy.url set for alembic')

    connectable = create_async_engine(db_url, poolclass=pool.NullPool)

    def do_run_migrations(sync_connection):
        context.configure(
            connection=sync_connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
