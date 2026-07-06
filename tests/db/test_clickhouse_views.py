"""Tests for ClickHouse materialized view definitions."""

from opennem.db.clickhouse.views import (
    RENEWABLE_INTERVALS_DAILY_VIEW,
    RENEWABLE_INTERVALS_VIEW,
)

# Storage/load fueltechs must be excluded from the renewable MVs: they split generation into
# renewable (=1) vs fossils (=0) for the milestone records, and storage is neither. Batteries
# are renewable=0, so without this exclusion their charge+discharge energy pollutes the
# "fossils" bucket and inflates fossil records (GH #585).
_STORAGE_FUELTECHS = ("battery", "battery_charging", "battery_discharging", "pumps")


def test_renewable_mvs_exclude_storage_fueltechs() -> None:
    for view in (RENEWABLE_INTERVALS_VIEW, RENEWABLE_INTERVALS_DAILY_VIEW):
        for sql in (view.schema, view.backfill_query):
            for fueltech in _STORAGE_FUELTECHS:
                assert f"'{fueltech}'" in sql, f"{view.name} must exclude '{fueltech}' storage fueltech"
