"""Deterministic ordering of GET /v4/facilities/: facilities by name (code tiebreak), units by code."""

import random
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from opennem.api.facilities.router import get_facilities
from opennem.db.models.opennem import Facility


def _unit(code: str) -> SimpleNamespace:
    return SimpleNamespace(
        code=code,
        code_display=None,
        fueltech_id="wind",
        status_id="retired",
        approved=True,
        interconnector=False,
        capacity_registered=None,
        capacity_maximum=None,
        capacity_storage=None,
        emissions_factor_co2=None,
        data_first_seen=None,
        data_last_seen=None,
        dispatch_type=None,
        commencement_date=None,
        closure_date=None,
        expected_operation_date=None,
        expected_closure_date=None,
        construction_start_date=None,
        project_approval_date=None,
        project_approval_lodgement_date=None,
        commencement_date_specificity=None,
        closure_date_specificity=None,
        expected_operation_date_specificity=None,
        expected_closure_date_specificity=None,
        construction_start_date_specificity=None,
        project_approval_date_specificity=None,
        cms_created_at=None,
        cms_updated_at=None,
        max_generation=None,
        max_generation_interval=None,
    )


def _facility(code: str, name: str, unit_codes: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        code=code,
        code_display=None,
        name=name,
        network_id="NEM",
        network_region="NSW1",
        description=None,
        npi_id=None,
        osm_way_id=None,
        location=None,
        boundary=None,
        units=[_unit(c) for c in unit_codes],
        cms_created_at=datetime(2024, 1, 1),
        cms_updated_at=datetime(2024, 1, 1),
    )


FACILITIES = [
    ("AAA", "Alpha", ["AAA1", "AAA2", "AAA10", "AAA3"]),
    ("BAYSW", "Bayswater", ["BAYSW4", "BAYSW1", "BAYSW3", "BAYSW2"]),
    ("BBATT", "Bungala Battery", ["BBATTERY", "BBATTERY1"]),
    ("ZED", "Zed", ["ZED2", "ZED1"]),
]


async def _call(seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    rows = [_facility(c, n, list(u)) for c, n, u in FACILITIES]
    rng.shuffle(rows)
    for r in rows:
        rng.shuffle(r.units)

    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows

    async def _execute(*_a: object, **_k: object) -> MagicMock:
        return result

    session.execute = _execute

    cm = MagicMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = False

    unwrapped: Any = get_facilities
    unwrapped = unwrapped.__wrapped__

    with patch("opennem.api.facilities.router.get_read_session", return_value=cm):
        resp = await unwrapped(user=None)
    return resp.model_dump(mode="json")


@pytest.mark.asyncio
async def test_units_sorted_by_code_within_facility() -> None:
    body = await _call(1)
    for fac in body["data"]:
        codes = [u["code"] for u in fac["units"]]
        assert codes == sorted(codes)


@pytest.mark.asyncio
async def test_facilities_sorted_by_name() -> None:
    body = await _call(2)
    assert [f["code"] for f in body["data"]] == ["AAA", "BAYSW", "BBATT", "ZED"]


@pytest.mark.asyncio
async def test_identical_across_row_orders() -> None:
    bodies = [await _call(seed) for seed in range(6)]
    assert all(b == bodies[0] for b in bodies)


def test_unit_relationship_ordered_by_code() -> None:
    order_by = Facility.units.property.order_by
    assert [str(c) for c in order_by] == ["units.code"]
