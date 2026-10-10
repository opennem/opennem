"""ensure_materialized_views_exist looks up every view in one system.tables query (BACKEND-61Y).

It runs on every 5-minute MV refresh, and used to issue two system.tables queries per view.
"""

from typing import Any

import pytest

from opennem.db.clickhouse import materialized_views as mv
from opennem.db.clickhouse.views import CLICKHOUSE_MATERIALIZED_VIEWS


class _FakeClient:
    """Answers the system.tables lookup from ``tables`` and records every query."""

    def __init__(self, tables: dict[str, str]) -> None:
        self.tables = tables
        self.queries: list[tuple[str, dict[str, Any] | None]] = []

    def execute(self, query: str, params: dict[str, Any] | None = None) -> list[tuple[str, str]]:
        self.queries.append((query, params))
        if "system.tables" in query:
            assert params is not None
            return [(name, engine) for name, engine in self.tables.items() if name in params["names"]]
        return []


def _install(monkeypatch: pytest.MonkeyPatch, tables: dict[str, str]) -> _FakeClient:
    fake = _FakeClient(tables)
    monkeypatch.setattr(mv, "get_clickhouse_client", lambda *a, **k: fake)
    return fake


def _system_tables_queries(fake: _FakeClient) -> list[str]:
    return [q for q, _ in fake.queries if "system.tables" in q]


def test_all_views_present_is_a_single_query(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _install(monkeypatch, dict.fromkeys(CLICKHOUSE_MATERIALIZED_VIEWS, "MaterializedView"))

    mv.ensure_materialized_views_exist()

    assert len(fake.queries) == 1
    assert fake.queries[0][1] == {"names": tuple(CLICKHOUSE_MATERIALIZED_VIEWS)}


def test_missing_view_is_created(monkeypatch: pytest.MonkeyPatch) -> None:
    views = list(CLICKHOUSE_MATERIALIZED_VIEWS.values())
    missing = views[0]
    fake = _install(monkeypatch, {v.name: "MaterializedView" for v in views[1:]})

    mv.ensure_materialized_views_exist(views)

    assert len(_system_tables_queries(fake)) == 1
    assert [q for q, _ in fake.queries[1:]] == [missing.schema]


def test_engine_mismatch_drops_and_recreates(monkeypatch: pytest.MonkeyPatch) -> None:
    view = next(iter(CLICKHOUSE_MATERIALIZED_VIEWS.values()))
    assert "CREATE MATERIALIZED VIEW" in view.schema.upper()
    fake = _install(monkeypatch, {view.name: "SummingMergeTree"})

    mv.ensure_materialized_views_exist([view])

    assert [q for q, _ in fake.queries[1:]] == [f"DROP TABLE IF EXISTS {view.name}", view.schema]


def test_repeated_view_is_created_once(monkeypatch: pytest.MonkeyPatch) -> None:
    view = next(iter(CLICKHOUSE_MATERIALIZED_VIEWS.values()))
    fake = _install(monkeypatch, {})

    mv.ensure_materialized_views_exist([view, view])

    assert [q for q, _ in fake.queries[1:]] == [view.schema]


def test_no_views_issues_no_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _install(monkeypatch, {})

    mv.ensure_materialized_views_exist([])

    assert fake.queries == []
