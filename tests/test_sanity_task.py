"""Sanity webhook task runs the old sync logic (minus the in-request sleep)"""

from unittest.mock import AsyncMock

import pytest
from arq import Retry
from sanity.exceptions import SanityServerError
from sqlalchemy.exc import IntegrityError

from opennem.controllers import sanity as sanity_ctl
from opennem.tasks import tasks


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    m = {
        "update": AsyncMock(),
        "export": AsyncMock(),
        "parent": AsyncMock(return_value="fac-1"),
    }
    monkeypatch.setattr(sanity_ctl, "update_database_facilities_from_cms", m["update"])
    monkeypatch.setattr(sanity_ctl, "export_facilities_static", m["export"])
    monkeypatch.setattr(sanity_ctl, "get_facility_cms_id_by_unit_cms_id", m["parent"])
    return m


@pytest.mark.asyncio
async def test_facility_syncs_and_exports(mocks: dict[str, AsyncMock]) -> None:
    await tasks.task_sanity_webhook({"job_try": 1}, "facility", "abc")
    mocks["update"].assert_awaited_once_with(cms_id="abc", send_slack=False)
    mocks["export"].assert_awaited_once()


@pytest.mark.asyncio
async def test_unit_syncs_parent_facility(mocks: dict[str, AsyncMock]) -> None:
    await tasks.task_sanity_webhook({"job_try": 1}, "unit", "u1")
    mocks["parent"].assert_awaited_once_with("u1")
    mocks["update"].assert_awaited_once_with(cms_id="fac-1", send_slack=False)
    mocks["export"].assert_awaited_once()


@pytest.mark.asyncio
async def test_unit_without_parent_skips(mocks: dict[str, AsyncMock]) -> None:
    mocks["parent"].return_value = None
    await tasks.task_sanity_webhook({"job_try": 1}, "unit", "u1")
    mocks["update"].assert_not_awaited()
    mocks["export"].assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_type_still_exports(mocks: dict[str, AsyncMock]) -> None:
    await tasks.task_sanity_webhook({"job_try": 1}, "other", "x")
    mocks["update"].assert_not_awaited()
    mocks["export"].assert_awaited_once()


@pytest.mark.asyncio
async def test_integrity_error_swallowed(mocks: dict[str, AsyncMock]) -> None:
    mocks["update"].side_effect = IntegrityError("stmt", {}, Exception("dup"))
    await tasks.task_sanity_webhook({"job_try": 1}, "facility", "abc")
    mocks["export"].assert_not_awaited()


@pytest.mark.asyncio
async def test_cms_down_retries(mocks: dict[str, AsyncMock]) -> None:
    mocks["update"].side_effect = SanityServerError("cdn down")
    with pytest.raises(Retry):
        await tasks.task_sanity_webhook({"job_try": 1}, "facility", "abc")


@pytest.mark.asyncio
async def test_other_errors_propagate(mocks: dict[str, AsyncMock]) -> None:
    mocks["update"].side_effect = ValueError("boom")
    with pytest.raises(ValueError):
        await tasks.task_sanity_webhook({"job_try": 1}, "facility", "abc")


def test_task_registered_on_worker() -> None:
    from opennem.tasks.app import WorkerSettings

    names = {getattr(f, "name", getattr(f, "__name__", None)) for f in WorkerSettings.functions}
    assert "task_sanity_webhook" in names
