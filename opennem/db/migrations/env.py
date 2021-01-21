import logging
from logging.config import fileConfig
from typing import List

from alembic import context
from sqlalchemy import engine_from_config, pool

from opennem.db import db_connect
from opennem.db.models import opennem
from opennem.settings import settings

config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

config.set_main_option("sqlalchemy.url", settings.db_url)


target_metadata = opennem.metadata


def exclude_tables_from_config(config_: str) -> List[str]:
    tables = []
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


exclude_tables = exclude_tables_from_config(config.get_section("alembic:exclude"))


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in exclude_tables:
        return False
    else:
        return True


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
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section),
    #     prefix="sqlalchemy.",
    #     # poolclass=pool.Pool(),
    # )

    engine = db_connect(timeout=600)

    with engine.connect() as connection:
        context.configure(
            include_object=include_object,
            connection=connection,
            target_metadata=target_metadata,
        )

        try:
            with context.begin_transaction():
                context.run_migrations()
        finally:
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
