"""Tests for the facility seen-range update query (BACKEND-51M/51N).

The facility_codes filter previously referenced an alias "f" that was never joined in the
query, so postgres raised `missing FROM-clause entry for table "f"` whenever the sanity
webhook created a new facility (see opennem/workers/facility_data_seen.py).
"""

import pytest

from opennem.workers.facility_data_seen import get_update_seen_query


def test_facility_codes_filter_uses_facility_scada_alias() -> None:
    query = str(get_update_seen_query(include_first_seen=True, facility_codes=["SMFBESS2"]))

    assert "f.code in" not in query
    assert "fs.facility_code in ('SMFBESS2')" in query


def test_no_facility_codes_filter_when_not_provided() -> None:
    query = str(get_update_seen_query(include_first_seen=True))

    assert "facility_code in" not in query


@pytest.mark.asyncio
async def test_first_seen_runs_in_chunks_and_retries_lost_connection(monkeypatch) -> None:
    from sqlalchemy.exc import DBAPIError

    from opennem.workers import facility_data_seen as fds

    codes = [f"U{i:03d}" for i in range(fds.FIRST_SEEN_CHUNK_SIZE + 5)]
    ran: list[str] = []
    calls = {"n": 0}

    async def fake_codes() -> list[str]:
        return codes

    async def fake_run(query, statement_timeout_s: int) -> None:
        assert statement_timeout_s == fds.FIRST_SEEN_STATEMENT_TIMEOUT_SECONDS
        calls["n"] += 1
        if calls["n"] == 1:
            raise DBAPIError("stmt", None, Exception("connection was closed in the middle of operation: query timeout"))
        ran.append(str(query))

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(fds, "_get_unit_codes", fake_codes)
    monkeypatch.setattr(fds, "_run_seen_update", fake_run)
    monkeypatch.setattr(fds.asyncio, "sleep", no_sleep)

    assert await fds.update_facility_seen_range(include_first_seen=True) is True
    # 2 chunks, first retried once after the dropped connection
    assert calls["n"] == 3
    assert len(ran) == 2
    assert "'U000'" in ran[0] and "'U044'" in ran[1]
