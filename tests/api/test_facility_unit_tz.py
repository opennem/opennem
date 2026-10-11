"""Unit datetime offsets follow the unit's own facility network (#694), regardless of serialisation order."""

import itertools
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from opennem.api.facilities.schema import APIV4FacilityResponseSchema, FacilityResponseSchema, UnitResponseSchema
from opennem.schema.unit import UnitFueltechType, UnitStatusType

OFFSETS = {"NEM": timedelta(hours=10), "WEM": timedelta(hours=8)}
NAIVE = datetime(2020, 1, 2, 3, 4, 5)


def _facility(network_id: str, code: str) -> FacilityResponseSchema:
    # mirrors the router: units built empty then assigned, facility built from unit instances
    unit = UnitResponseSchema(code=f"{code}1", fueltech_id=UnitFueltechType.coal_black, status_id=UnitStatusType.operating)
    unit.data_first_seen = NAIVE
    unit.data_last_seen = NAIVE
    unit.commencement_date = NAIVE
    unit.expected_closure_date = NAIVE
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
            assert value.replace(tzinfo=None) == NAIVE


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
