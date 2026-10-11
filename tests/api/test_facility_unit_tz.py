"""Unit datetime offsets follow the unit's own facility network (#694), regardless of serialisation order."""

import itertools
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from opennem.api.facilities.schema import APIV4FacilityResponseSchema, FacilityResponseSchema, UnitResponseSchema
from opennem.schema.unit import UnitFueltechType, UnitStatusType

OFFSETS = {"NEM": timedelta(hours=10), "WEM": timedelta(hours=8)}
NAIVE = datetime(2020, 1, 2, 3, 4, 5)
UTC_INSTANT = datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)


def _facility(network_id: str, code: str) -> FacilityResponseSchema:
    # mirrors the router: units built empty then assigned, facility built from unit instances
    unit = UnitResponseSchema(code=f"{code}1", fueltech_id=UnitFueltechType.coal_black, status_id=UnitStatusType.operating)
    unit.data_first_seen = NAIVE
    unit.data_last_seen = NAIVE
    unit.commencement_date = UTC_INSTANT
    unit.expected_closure_date = UTC_INSTANT
    return FacilityResponseSchema(code=code, name=code, network_id=network_id, network_region="X1", units=[unit])


def _serialise(facilities: list[FacilityResponseSchema]) -> list[FacilityResponseSchema]:
    """Router builds every facility first, then FastAPI re-validates the dumped response (units rebuilt from dicts)."""
    response = APIV4FacilityResponseSchema(success=True, data=facilities)
    return APIV4FacilityResponseSchema.model_validate(response.model_dump(mode="json")).data


def _assert_offsets(facility: FacilityResponseSchema) -> None:
    expected = OFFSETS[facility.network_id]
    for unit in facility.units:
        for field in ("data_first_seen", "data_last_seen", "commencement_date", "expected_closure_date"):
            value = getattr(unit, field)
            assert value.utcoffset() == expected, (facility.code, field, value)
            # seen fields keep the wall clock, CMS dates keep the instant
            if field.startswith("data_"):
                assert value.replace(tzinfo=None) == NAIVE
            else:
                assert value == UTC_INSTANT


def _run(order: list[str], prefix: str = "F") -> None:
    facilities = [_facility(n, f"{prefix}{i}") for i, n in enumerate(order)]
    for facility in _serialise(facilities):
        _assert_offsets(facility)


def test_wem_then_nem() -> None:
    _run(["WEM", "NEM"])


def test_nem_then_wem() -> None:
    _run(["NEM", "WEM"])


def test_mixed_list_repeated() -> None:
    for _ in range(5):
        _run(["NEM", "WEM", "WEM", "NEM", "WEM"])


def test_all_orders() -> None:
    for order in itertools.permutations(["NEM", "WEM", "NEM"]):
        _run(list(order))


def test_across_requests() -> None:
    _run(["WEM"], "A")
    _run(["NEM"], "B")
    _run(["WEM", "NEM"], "C")


def test_threads_interleaved() -> None:
    def work(i: int) -> None:
        for j in range(30):
            _run(["NEM", "WEM"] if (i + j) % 2 else ["WEM", "NEM"], f"T{i}_{j}_")

    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in [pool.submit(work, i) for i in range(8)]:
            future.result()


def test_no_shared_class_state() -> None:
    _run(["WEM", "NEM"])
    assert "context" not in UnitResponseSchema.model_config


def _unit_with(**fields: datetime) -> UnitResponseSchema:
    unit = UnitResponseSchema(code="U1", fueltech_id=UnitFueltechType.coal_black, status_id=UnitStatusType.operating)
    for name, value in fields.items():
        setattr(unit, name, value)
    return unit


def _iso(value: datetime | None) -> str:
    assert value is not None
    return value.isoformat()


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


@pytest.mark.parametrize(
    ("network", "field", "stored", "expected"),
    [
        ("NEM", "commencement_date", "2021-01-13T14:00:00", "2021-01-14T00:00:00+10:00"),
        ("NEM", "expected_closure_date", "2044-12-31T14:00:00", "2045-01-01T00:00:00+10:00"),
        ("WEM", "commencement_date", "2001-09-30T16:00:00", "2001-10-01T00:00:00+08:00"),
        ("NEM", "commencement_date", "1951-12-31T14:00:00", "1952-01-01T00:00:00+10:00"),
        ("NEM", "closure_date", "1978-12-31T14:00:00", "1979-01-01T00:00:00+10:00"),
        ("WEM", "expected_operation_date", "2026-07-25T16:00:00", "2026-07-26T00:00:00+08:00"),
        ("NEM", "data_first_seen", "2020-12-15T01:05:00", "2020-12-15T01:05:00+10:00"),
        ("WEM", "data_first_seen", "2006-09-20T00:00:00", "2006-09-20T00:00:00+08:00"),
        ("NEM", "data_last_seen", "2024-06-30T23:55:00", "2024-06-30T23:55:00+10:00"),
    ],
)
def test_reference_values(network: str, field: str, stored: str, expected: str) -> None:
    unit = _unit_with(**{field: _utc(stored)})
    unit.apply_network_timezone(network)
    assert _iso(getattr(unit, field)) == expected


def test_unit_without_seen_fields_gets_offsets() -> None:
    unit = _unit_with(commencement_date=_utc("2021-01-13T14:00:00"), closure_date=_utc("1978-12-31T14:00:00"))
    unit.apply_network_timezone("NEM")
    assert _iso(unit.commencement_date) == "2021-01-14T00:00:00+10:00"
    assert _iso(unit.closure_date) == "1979-01-01T00:00:00+10:00"
    assert unit.data_first_seen is None and unit.data_last_seen is None


def test_none_fields_stay_none() -> None:
    unit = _unit_with()
    unit.apply_network_timezone("WEM")
    assert unit.commencement_date is None and unit.data_first_seen is None


def test_idempotent_on_revalidation() -> None:
    unit = _unit_with(commencement_date=_utc("2021-01-13T14:00:00"), data_first_seen=_utc("2020-12-15T01:05:00"))
    unit.apply_network_timezone("NEM")
    unit.apply_network_timezone("NEM")
    assert _iso(unit.commencement_date) == "2021-01-14T00:00:00+10:00"
    assert _iso(unit.data_first_seen) == "2020-12-15T01:05:00+10:00"
