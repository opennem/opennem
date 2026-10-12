"""Early rejection middleware: dead stats routes (#649) and unknown facility/unit codes (#646)."""

import json
import time
from typing import Any

import pytest

from opennem.api import known_codes
from opennem.api.early_reject import EarlyRejectMiddleware, is_dead_stats_path
from opennem.utils.sentry import _sentry_before_send_transaction

pytestmark = pytest.mark.asyncio


async def _run(
    path: str, query: bytes = b"", method: str = "GET", auth: str | None = "Bearer on_dev_some_other_key_123"
) -> tuple[list[dict[str, Any]], list[str]]:
    sent: list[dict[str, Any]] = []
    called: list[str] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        called.append(scope["path"])

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg: dict[str, Any]) -> None:
        sent.append(msg)

    await EarlyRejectMiddleware(inner)(
        {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": query,
            "headers": [(b"authorization", auth.encode())] if auth else [],
        },
        receive,
        send,
    )
    return sent, called


@pytest.fixture
def loaded_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(known_codes._state, "facilities", frozenset({"BANGOWF", "ERARING"}))
    monkeypatch.setattr(known_codes._state, "units", frozenset({"BANGOWF1", "ERARING1"}))
    monkeypatch.setattr(known_codes._state, "loaded_at", time.monotonic())
    monkeypatch.setattr(known_codes, "_schedule_refresh", lambda: None)
    from opennem.api import security

    monkeypatch.setattr(security.settings, "api_dev_key", "on_dev_some_other_key_123")


@pytest.mark.parametrize(
    "path",
    [
        "/stats/flow/network/NEM",
        "/v3/stats/flow/network/NEM",
        "/v4/stats/price/network/NEM/NSW1",
        "/v4/stats/au/NEM/NSW1/price/latest",
        "/stats/au/nem/price/1d/current",
        "/stats/power/nem",
        "/stats/air/nem",
        "/v3/stats/power/station/NEM/BANGOWF",
        "/stats",
    ],
)
async def test_dead_stats_paths_410_without_calling_app(path: str) -> None:
    sent, called = await _run(path)
    assert not called
    assert sent[0]["status"] == 410
    body = json.loads(sent[1]["body"])
    assert body["success"] is False
    assert "v4" in body["error"]


@pytest.mark.parametrize(
    "path",
    [
        "/v4/stats/power/station/NEM/BANGOWF",
        "/stats/energy/station/NEM/BANGOWF",
        "/v4/data/network/NEM",
        "/v4/metrics",
        "/statsfoo",
    ],
)
async def test_live_paths_pass_through(path: str) -> None:
    sent, called = await _run(path)
    assert called == [path]
    assert not sent


def test_is_dead_stats_path_live_v4_station() -> None:
    assert not is_dead_stats_path("/v4/stats/power/station/NEM/X")
    assert is_dead_stats_path("/v3/stats/energy/station/NEM/X")


async def test_unknown_facility_404_before_app(loaded_codes: None) -> None:
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&facility_code=NOPE&facility_code=ALSONOPE")
    assert not called
    assert sent[0]["status"] == 404
    assert json.loads(sent[1]["body"])["error"] == (
        "No data available for facility=['NOPE', 'ALSONOPE'] in the specified time range"
    )


async def test_unknown_unit_404(loaded_codes: None) -> None:
    sent, called = await _run("/data/facilities/NEM", b"metrics=energy&facility_code=BANGOWF&unit_code=NOPE1")
    assert not called
    assert sent[0]["status"] == 404
    assert "facility=['BANGOWF'], unit=['NOPE1']" in json.loads(sent[1]["body"])["error"]


@pytest.mark.parametrize(
    "query",
    [
        b"metrics=energy",
        b"metrics=energy&facility_code=BANGOWF",
        b"metrics=energy&facility_code=NOPE&facility_code=ERARING",  # partial match still queries
        b"metrics=energy&unit_code=BANGOWF1",
        b"",
    ],
)
async def test_valid_facility_requests_pass_through(loaded_codes: None, query: bytes) -> None:
    sent, called = await _run("/v4/data/facilities/NEM", query)
    assert called
    assert not sent


async def test_fails_open_when_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(known_codes._state, "loaded_at", None)
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&facility_code=NOPE")
    assert called
    assert not sent


async def test_stale_set_miss_passes_through_and_refreshes(loaded_codes: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(known_codes._state, "loaded_at", time.monotonic() - 120)
    scheduled: list[bool] = []
    monkeypatch.setattr(known_codes, "_schedule_refresh", lambda: scheduled.append(True))
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&facility_code=NEWFAC")
    assert called
    assert scheduled == [True]


async def test_tz_aware_dates_400(loaded_codes: None) -> None:
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&date_start=2024-01-01T00:00:00%2B10:00")
    assert not called
    assert sent[0]["status"] == 400
    assert json.loads(sent[1]["body"])["error"] == "Date start must be timezone naive and in network time"


async def test_unparseable_dates_pass_through(loaded_codes: None) -> None:
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&date_start=garbage")
    assert called


async def test_options_not_intercepted() -> None:
    sent, called = await _run("/v4/stats/flow/network/NEM", method="OPTIONS")
    assert called


async def test_refresh_keeps_previous_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(known_codes._state, "facilities", frozenset({"A"}))

    async def empty() -> tuple[frozenset[str], frozenset[str]]:
        return frozenset(), frozenset()

    monkeypatch.setattr(known_codes, "_load_codes", empty)
    await known_codes.refresh_known_codes()
    assert known_codes._state.facilities == frozenset({"A"})


def test_sentry_drops_404_410_transactions() -> None:
    ev = {"contexts": {"trace": {"data": {"http.response.status_code": 410}}}}
    assert _sentry_before_send_transaction(ev, {}) is None
    assert _sentry_before_send_transaction({"contexts": {"trace": {"data": {"http.response.status_code": 200}}}}, {})
    assert _sentry_before_send_transaction({}, {}) == {}


# ---- full app: rejected before any auth / ClickHouse call ----


@pytest.fixture
def app_client(loaded_codes: None, monkeypatch: pytest.MonkeyPatch) -> Any:
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    from opennem.api import security
    from opennem.api.app import app
    from opennem.api.data import router as data_router
    from opennem.db.clickhouse import get_clickhouse_dependency

    fetch_user = AsyncMock(side_effect=AssertionError("auth called"))
    execute = AsyncMock(return_value=[])
    monkeypatch.setattr(security, "_fetch_user", fetch_user)
    monkeypatch.setattr(data_router, "execute_async", execute)
    monkeypatch.setattr(security.settings, "api_dev_key", "on_dev_some_other_key_123")
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend())
    app.dependency_overrides[get_clickhouse_dependency] = lambda: object()
    try:
        yield TestClient(app, raise_server_exceptions=False), fetch_user, execute
    finally:
        app.dependency_overrides.pop(get_clickhouse_dependency, None)


def test_e2e_dead_route_410_no_auth(app_client: Any) -> None:
    client, fetch_user, _ = app_client
    for path in ("/stats/flow/network/NEM", "/v4/stats/au/NEM/NSW1/price/latest", "/v3/stats/price/NEM"):
        r = client.get(path, headers={"Authorization": "Bearer some_unknown_key_value"})
        assert r.status_code == 410, path
        assert r.json()["success"] is False
    fetch_user.assert_not_called()


def test_e2e_unknown_facility_404_validated_key_no_upstream(app_client: Any) -> None:
    client, fetch_user, execute = app_client
    r = client.get(
        "/v4/data/facilities/NEM",
        params={"metrics": "energy", "facility_code": "NOPE"},
        headers={"Authorization": "Bearer on_dev_some_other_key_123"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "No data available for facility=['NOPE'] in the specified time range"
    fetch_user.assert_not_called()
    execute.assert_not_called()


def test_e2e_cors_headers_on_early_reject(app_client: Any) -> None:
    client, _, _ = app_client
    r = client.get("/stats/flow/network/NEM", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 410
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")


def test_e2e_valid_facility_reaches_route(app_client: Any) -> None:
    """Known code passes the middleware; the dev key bypasses unkey and the route runs the (mocked) query."""
    client, fetch_user, execute = app_client
    r = client.get(
        "/v4/data/facilities/NEM",
        params={
            "metrics": "energy",
            "facility_code": "BANGOWF",
            "interval": "1d",
            "date_start": "2026-10-01T00:00:00",
            "date_end": "2026-10-05T00:00:00",
        },
        headers={"Authorization": "Bearer on_dev_some_other_key_123"},
    )
    assert r.status_code == 404  # mocked ClickHouse returns no rows: the in-route 404, proving it got past the middleware
    execute.assert_called_once()
    fetch_user.assert_not_called()  # dev key bypass


async def test_tz_check_uses_last_repeated_date(loaded_codes: None) -> None:
    q = b"metrics=energy&date_start=2024-01-01T00:00:00%2B10:00&date_start=2024-01-01T00:00:00"
    sent, called = await _run("/v4/data/facilities/NEM", q)
    assert called


async def test_miss_refresh_backs_off_after_recent_attempt(loaded_codes: None, monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    monkeypatch.undo()  # drop the _schedule_refresh stub from loaded_codes
    monkeypatch.setattr(known_codes._state, "facilities", frozenset({"A"}))
    monkeypatch.setattr(known_codes._state, "units", frozenset({"A1"}))
    monkeypatch.setattr(known_codes._state, "loaded_at", time.monotonic() - 120)
    monkeypatch.setattr(known_codes._state, "last_attempt", time.monotonic() - 5)
    monkeypatch.setattr(known_codes._state, "refresh_task", None)
    created: list[Any] = []
    monkeypatch.setattr(asyncio, "create_task", lambda *a, **k: created.append(1))
    assert known_codes.has_unknown_codes(["NOPE"], []) is False
    assert not created


@pytest.mark.parametrize("auth", [None, "Bearer never_validated_key_123", "Basic abc"])
async def test_unknown_code_not_revealed_to_unvalidated_callers(loaded_codes: None, auth: str | None) -> None:
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&facility_code=NOPE", auth=auth)
    assert called
    assert not sent


async def test_cached_valid_key_gets_early_404(loaded_codes: None, monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.api import security
    from opennem.users.plans import OpenNEMPlan
    from opennem.users.schema import OpenNEMUser

    key = "cached_valid_key_1234567"
    user = OpenNEMUser(id="u", owner_id="u", plan=OpenNEMPlan.COMMUNITY, roles=[])
    monkeypatch.setitem(security._user_cache, security._cache_key(key), (user, security._now()))
    sent, called = await _run("/v4/data/facilities/NEM", b"metrics=energy&facility_code=NOPE", auth=f"Bearer {key}")
    assert not called
    assert sent[0]["status"] == 404


def test_e2e_unknown_facility_unvalidated_key_goes_to_auth(app_client: Any) -> None:
    client, fetch_user, execute = app_client
    r = client.get(
        "/v4/data/facilities/NEM",
        params={"metrics": "energy", "facility_code": "NOPE"},
        headers={"Authorization": "Bearer some_unknown_key_value"},
    )
    assert r.status_code != 404
    execute.assert_not_called()
