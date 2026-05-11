"""Tests for check_unsplit_batteries — split-lag detection per side.

The function compares, per bidirectional battery, the neg/pos row counts in
facility_scada against the corresponding charge/discharge unit row counts.
It only flags a battery when one side has bidirectional activity AND the
matching split side has materially fewer rows.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opennem.core.battery import BatteryUnitMap


def _mk_session(bi_rows, chg_rows, dis_rows):
    """Build an AsyncMock SQLAlchemy session whose three .execute() calls
    return bi/chg/dis in that order."""
    session = AsyncMock()

    def _result(rows):
        r = MagicMock()
        r.fetchall.return_value = rows
        return r

    session.execute.side_effect = [_result(bi_rows), _result(chg_rows), _result(dis_rows)]
    return session


def _patched(session, battery_map):
    """Patch get_battery_unit_map and get_read_session for a single test."""
    map_patch = patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock)
    sess_patch = patch("opennem.core.battery.get_read_session")
    return map_patch, sess_patch


@pytest.mark.asyncio
async def test_no_activity_not_flagged():
    """Battery with zero bidirectional rows in window → never flagged."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    session = _mk_session([], [], [])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == []


@pytest.mark.asyncio
async def test_only_charged_not_flagged():
    """Bidirectional only had charging intervals AND charge split matches → OK."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    # bi: 288 neg, 0 pos.  chg: 288 rows.  dis: 0 rows (correct — nothing to split)
    session = _mk_session([("LVES1", 288, 0)], [("LVESL1", 288)], [])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == []


@pytest.mark.asyncio
async def test_only_discharged_not_flagged():
    """Bidirectional only discharged AND discharge split matches → OK."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    session = _mk_session([("LVES1", 0, 288)], [], [("LVESG1", 288)])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == []


@pytest.mark.asyncio
async def test_charge_split_missing_is_flagged():
    """Bidirectional has neg activity but charge unit has no rows → flagged."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    session = _mk_session([("LVES1", 100, 50)], [], [("LVESG1", 50)])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
        patch("opennem.core.battery.slack_message", new_callable=AsyncMock),
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == ["LVES1"]


@pytest.mark.asyncio
async def test_discharge_split_missing_is_flagged():
    """Bidirectional has pos activity but discharge unit lags → flagged."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    session = _mk_session([("LVES1", 50, 100)], [("LVESL1", 50)], [("LVESG1", 10)])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
        patch("opennem.core.battery.slack_message", new_callable=AsyncMock),
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == ["LVES1"]


@pytest.mark.asyncio
async def test_boundary_drift_within_tolerance_not_flagged():
    """1-2 row drift between bi and split sides is normal crawl-batch boundary noise."""
    battery_map = {"LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1")}
    session = _mk_session([("LVES1", 100, 100)], [("LVESL1", 99)], [("LVESG1", 98)])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        assert await check_unsplit_batteries() == []


@pytest.mark.asyncio
async def test_alias_triples_deduped():
    """Manual map aliases (e.g. DALNTH / DALNTH1 / DALNTH01) → one row only."""
    battery_map = {
        "DALNTH": BatteryUnitMap(unit="DALNTH", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),
        "DALNTH1": BatteryUnitMap(unit="DALNTH1", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),
        "DALNTH01": BatteryUnitMap(unit="DALNTH01", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),
    }
    session = _mk_session([("DALNTH", 100, 50)], [], [("DALNTHG1", 50)])

    with (
        patch("opennem.core.battery.get_battery_unit_map", new_callable=AsyncMock) as gm,
        patch("opennem.core.battery.get_read_session") as gs,
        patch("opennem.core.battery.slack_message", new_callable=AsyncMock),
    ):
        gm.return_value = battery_map
        gs.return_value.__aenter__.return_value = session
        from opennem.core.battery import check_unsplit_batteries

        flagged = await check_unsplit_batteries()
        assert flagged == ["DALNTH"]  # only the first alias in dict order
