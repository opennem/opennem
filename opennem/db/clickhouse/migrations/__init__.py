"""
ClickHouse migration runner.

Drizzle-style numbered migrations with up/down functions, version tracked
in a `_ch_migrations` table inside ClickHouse itself.
"""

import importlib
import logging
import re
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from clickhouse_driver import Client

logger = logging.getLogger("opennem.db.clickhouse.migrations")

VERSIONS_DIR = Path(__file__).parent / "versions"

MIGRATIONS_TABLE = "_ch_migrations"

MIGRATIONS_TABLE_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
    version UInt32,
    name String,
    applied_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY (version)
"""

_MIGRATION_FILE_RE = re.compile(r"^(\d{4})_.+\.py$")

_TEMPLATE = textwrap.dedent('''\
    """
    {description}
    """

    from clickhouse_driver import Client

    REQUIRES_BACKFILL: list[str] = []


    def up(client: Client) -> None:
        pass


    def down(client: Client) -> None:
        pass
''')


@dataclass
class MigrationInfo:
    version: int
    name: str
    description: str
    requires_backfill: list[str]
    up: Callable[[Client], None]
    down: Callable[[Client], None]


@dataclass
class AppliedMigration:
    version: int
    name: str
    applied_at: datetime


class MigrationRunner:
    def __init__(self, client: Client) -> None:
        self.client = client

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def ensure_table(self) -> None:
        self.client.execute(MIGRATIONS_TABLE_SCHEMA)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def applied(self) -> list[AppliedMigration]:
        self.ensure_table()
        rows = self.client.execute(f"SELECT version, name, applied_at FROM {MIGRATIONS_TABLE} ORDER BY version")
        return [AppliedMigration(version=r[0], name=r[1], applied_at=r[2]) for r in rows]

    def discover(self) -> list[MigrationInfo]:
        migrations: list[MigrationInfo] = []

        for path in sorted(VERSIONS_DIR.glob("*.py")):
            if path.name.startswith("_"):
                continue
            m = _MIGRATION_FILE_RE.match(path.name)
            if not m:
                continue

            version = int(m.group(1))
            name = path.stem

            module_name = f"opennem.db.clickhouse.migrations.versions.{name}"
            mod = importlib.import_module(module_name)

            up_fn = getattr(mod, "up", None)
            down_fn = getattr(mod, "down", None)
            if up_fn is None or down_fn is None:
                raise ValueError(f"Migration {name} missing up() or down()")

            description = (mod.__doc__ or "").strip()
            requires_backfill = getattr(mod, "REQUIRES_BACKFILL", [])

            migrations.append(
                MigrationInfo(
                    version=version,
                    name=name,
                    description=description,
                    requires_backfill=requires_backfill,
                    up=up_fn,
                    down=down_fn,
                )
            )

        return migrations

    def pending(self) -> list[MigrationInfo]:
        applied_versions = {a.version for a in self.applied()}
        return [m for m in self.discover() if m.version not in applied_versions]

    # ------------------------------------------------------------------
    # Apply / rollback
    # ------------------------------------------------------------------

    def up(self, target: int | None = None) -> list[int]:
        self.ensure_table()
        applied_versions = {a.version for a in self.applied()}
        all_migrations = self.discover()

        # Consistency check: no gaps in applied versions
        if applied_versions:
            max_applied = max(applied_versions)
            expected = {m.version for m in all_migrations if m.version <= max_applied}
            missing = expected - applied_versions
            if missing:
                raise RuntimeError(
                    f"Migration history inconsistent: versions {sorted(missing)} "
                    f"not applied but later versions are. Fix manually."
                )

        to_apply = [m for m in all_migrations if m.version not in applied_versions]
        if target is not None:
            to_apply = [m for m in to_apply if m.version <= target]

        results: list[int] = []
        for migration in to_apply:
            logger.info(f"Applying migration {migration.name}: {migration.description}")
            migration.up(self.client)
            self.client.execute(
                f"INSERT INTO {MIGRATIONS_TABLE} (version, name) VALUES",
                [{"version": migration.version, "name": migration.name}],
            )
            results.append(migration.version)

            if migration.requires_backfill:
                views = ", ".join(migration.requires_backfill)
                view_args = " ".join(f"--view {v}" for v in migration.requires_backfill)
                logger.warning(
                    f"Migration {migration.name} requires FULL MV backfill for: {views}. "
                    f"Run with appropriate --days covering full history, e.g.: "
                    f"uv run python -m opennem.db.clickhouse.materialized_views --days 10000 {view_args}"
                )

        return results

    def down(self, count: int = 1) -> list[int]:
        self.ensure_table()
        applied = self.applied()
        all_migrations = {m.version: m for m in self.discover()}

        to_rollback = sorted(applied, key=lambda a: a.version, reverse=True)[:count]

        results: list[int] = []
        for entry in to_rollback:
            migration = all_migrations.get(entry.version)
            if migration is None:
                raise RuntimeError(f"Cannot rollback version {entry.version}: migration file not found")

            logger.info(f"Rolling back migration {migration.name}: {migration.description}")
            migration.down(self.client)
            self.client.execute(
                f"ALTER TABLE {MIGRATIONS_TABLE} DELETE WHERE version = %(v)s",
                {"v": entry.version},
            )
            results.append(entry.version)

            if migration.requires_backfill:
                views = ", ".join(migration.requires_backfill)
                logger.warning(f"Rollback of {migration.name} may require backfill for: {views}")

        return results

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> list[dict]:
        applied_map = {a.version: a for a in self.applied()}
        all_migrations = self.discover()

        rows: list[dict] = []
        for m in all_migrations:
            a = applied_map.get(m.version)
            rows.append(
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "applied": a is not None,
                    "applied_at": a.applied_at if a else None,
                }
            )

        return rows

    # ------------------------------------------------------------------
    # Scaffold
    # ------------------------------------------------------------------

    def create(self, description: str) -> Path:
        all_migrations = self.discover()
        next_version = max((m.version for m in all_migrations), default=0) + 1

        slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")
        filename = f"{next_version:04d}_{slug}.py"
        filepath = VERSIONS_DIR / filename

        filepath.write_text(_TEMPLATE.format(description=description))
        return filepath
