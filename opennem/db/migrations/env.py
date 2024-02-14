# pylint: disable=no-member
import logging
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any, Dict, List, Optional

from alembic import context
from sqlalchemy.schema import SchemaItem

BASE_DIR = str(Path(__file__).parent.parent.parent.parent)

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from opennem import settings  # noqa: E402
from opennem.db import db_connect  # noqa: E402
from opennem.db.models import opennem  # noqa: E402

config = context.config  # type: ignore
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")
config.transaction_per_migration = True # type: ignore

config.set_main_option("sqlalchemy.url", str(settings.db_url))


target_metadata = [opennem.metadata]


def exclude_tables_from_config(config_: dict[str, Any]) -> list[str]:
    """Read list of tables to exclude from config section and return as a list"""
    tables = []
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


exclude_tables = exclude_tables_from_config(config.get_section("alembic:exclude"))


def include_object(object: SchemaItem, name: str, type_: str, reflected: bool, compare_to: SchemaItem | None) -> bool:
    """Pluggable include object method to support skipping some migration tables"""
    if type_ == "table" and name in exclude_tables:
        return False
    else:
        return True


def run_migrations_offline() -> None:
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
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
            transaction_per_migration=True
        )

        connection.execution_options(isolation_level="AUTOCOMMIT")

        try:
            with context.begin_transaction():
                context.run_migrations()
        finally:
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
