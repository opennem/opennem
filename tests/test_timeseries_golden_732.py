# ruff: noqa: C408
"""Columnar timeseries formatter is byte-identical to the previous dict-per-row implementation (#732)."""

import copy
import json
import logging
import random
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

import pytest

from opennem.api.timeseries import (
    _build_label_key_and_labels,
    _fill_interior_gaps,
    format_timeseries_rows,
    rows_to_timeseries_list,
)
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval

logger = logging.getLogger("test.reference")


def reference_format(
    network: str,
    metrics: Sequence[Metric],
    interval: Interval,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[dict[str, Any]],
    facility_code: str | list[str] | None = None,
) -> list[dict[str, Any]]:
    """Verbatim copy of the pre-#732 format_timeseries_response."""
    network_obj = get_api_network_from_code(network)
    tz_offset = network_obj.get_fixed_offset()
    tz_offset_str = network_obj.get_offset_string()

    for row in results:
        iv = row["interval"]
        if isinstance(iv, datetime):
            row["interval"] = iv.replace(tzinfo=tz_offset)
        else:
            row["interval"] = datetime.combine(iv, datetime.min.time(), tzinfo=tz_offset)

    timeseries_list: list[dict[str, Any]] = []

    for metric in metrics:
        metric_name = metric.value.lower()
        meta = get_metric_metadata(metric)
        grouped: dict[str, dict[str, Any]] = {}

        for row in results:
            label_key, labels = _build_label_key_and_labels(row, primary_grouping, secondary_groupings, facility_code)
            if label_key not in grouped:
                grouped[label_key] = {"name": f"{metric_name}_{label_key}", "columns": labels, "data": []}
            value = None
            if metric_name in row and row[metric_name] is not None:
                value = float(row[metric_name])
            grouped[label_key]["data"].append((row["interval"], value))

        for g in grouped.values():
            g["data"].sort(key=lambda x: x[0])
        grouped = {k: v for k, v in grouped.items() if v["data"]}
        if not grouped:
            continue
        _fill_interior_gaps(grouped, interval)

        all_ts = [ts for g in grouped.values() for ts, _ in g["data"]]
        date_start = min(all_ts)
        date_end = max(all_ts)
        groupings: list[str] = []
        if secondary_groupings:
            groupings = [primary_grouping.value] + [g.value.lower() for g in secondary_groupings]

        result_dicts = []
        for g in grouped.values():
            data_out = [[ts.isoformat(), v] for ts, v in g["data"]]
            result_dicts.append(
                {
                    "name": g["name"],
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "columns": g["columns"],
                    "data": data_out,
                }
            )
        timeseries_list.append(
            {
                "network_code": network,
                "metric": metric_name,
                "unit": meta.unit,
                "interval": interval.value,
                "date_start": date_start.isoformat(),
                "date_end": date_end.isoformat(),
                "groupings": groupings,
                "results": result_dicts,
                "network_timezone_offset": tz_offset_str,
            }
        )
    return timeseries_list


_REGIONS = ["NSW1", "VIC1", "QLD1"]
_FUELTECHS = ["coal_black", "solar_utility", "wind", "gas_ccgt", "battery_discharging"]
_GROUPS = {"coal_black": "coal", "solar_utility": "solar", "wind": "wind", "gas_ccgt": "gas", "battery_discharging": "battery"}


def _rows(
    n_ts: int,
    *,
    step: timedelta,
    shape: str,
    metrics: list[str],
    drop: float = 0.0,
    seed: int = 1,
    as_date: bool = False,
) -> tuple[list[str], list[tuple[Any, ...]]]:
    rnd = random.Random(seed)
    start = datetime(2026, 1, 1)
    cols = ["interval"]
    if shape in ("region_ft", "region_group", "region"):
        cols.append("network_region")
    if shape == "region_ft":
        cols += ["fueltech", "fueltech_group"]
    elif shape == "region_group":
        cols += ["fueltech_group", "renewable"]
    elif shape == "ft":
        cols += ["fueltech"]
    elif shape == "unit":
        cols += ["unit_code"]
    cols += metrics

    rows: list[tuple[Any, ...]] = []
    for i in range(n_ts):
        ts = start + step * i
        if as_date:
            ts = ts.date()  # type: ignore[assignment]
        for region in _REGIONS if "region" in shape else [None]:
            for ft in _FUELTECHS if shape in ("region_ft", "region_group", "ft") else [None]:
                for unit in ["U1", "U2", "U3"] if shape == "unit" else [None]:
                    if rnd.random() < drop:
                        continue
                    vals: dict[str, Any] = {
                        "interval": ts,
                        "network_region": region,
                        "fueltech": ft,
                        "fueltech_group": _GROUPS.get(ft or ""),
                        "renewable": ft in ("wind", "solar_utility"),
                        "unit_code": unit,
                    }
                    for m in metrics:
                        r = rnd.random()
                        vals[m] = None if r < 0.1 else (rnd.randint(0, 900) if r < 0.2 else rnd.random() * 1000)
                    rows.append(tuple(vals.get(c) for c in cols))
    rnd.shuffle(rows)  # sort path must restore order identically
    return cols, rows


_CASES: list[dict[str, Any]] = [
    dict(shape="none", primary=PrimaryGrouping.NETWORK, secondary=None, metrics=["power"], n=30, step=timedelta(minutes=5)),
    dict(
        shape="region",
        primary=PrimaryGrouping.NETWORK_REGION,
        secondary=None,
        metrics=["power", "energy"],
        n=30,
        step=timedelta(minutes=5),
    ),
    dict(
        shape="region_ft",
        primary=PrimaryGrouping.NETWORK_REGION,
        secondary=[SecondaryGrouping.FUELTECH],
        metrics=["power", "energy"],
        n=50,
        step=timedelta(minutes=5),
    ),
    dict(
        shape="region_ft",
        primary=PrimaryGrouping.NETWORK_REGION,
        secondary=[SecondaryGrouping.FUELTECH, SecondaryGrouping.FUELTECH_GROUP],
        metrics=["power"],
        n=40,
        step=timedelta(hours=1),
        drop=0.2,
    ),
    dict(
        shape="region_group",
        primary=PrimaryGrouping.NETWORK_REGION,
        secondary=[SecondaryGrouping.FUELTECH_GROUP, SecondaryGrouping.RENEWABLE],
        metrics=["energy", "power"],
        n=40,
        step=timedelta(days=1),
        drop=0.3,
    ),
    dict(
        shape="ft",
        primary=PrimaryGrouping.NETWORK,
        secondary=[SecondaryGrouping.FUELTECH],
        metrics=["energy"],
        n=20,
        step=timedelta(days=1),
        as_date=True,
    ),
    dict(
        shape="unit",
        primary=PrimaryGrouping.NETWORK,
        secondary=None,
        metrics=["power"],
        n=30,
        step=timedelta(minutes=30),
        facility="U1",
        drop=0.25,
    ),
    dict(
        shape="region_ft",
        primary=PrimaryGrouping.NETWORK_REGION,
        secondary=[SecondaryGrouping.FUELTECH],
        metrics=["power"],
        n=0,
        step=timedelta(minutes=5),
    ),
]


def _interval_for(step: timedelta) -> Interval:
    return {
        timedelta(minutes=5): Interval.INTERVAL,
        timedelta(minutes=30): Interval.HALF_HOUR,
        timedelta(hours=1): Interval.HOUR,
        timedelta(days=1): Interval.DAY,
    }[step]


@pytest.mark.parametrize("case", _CASES, ids=lambda c: f"{c['shape']}-{len(c['metrics'])}m-{c['n']}")
def test_golden_equivalence(case: dict[str, Any]) -> None:
    cols, rows = _rows(
        case["n"],
        step=case["step"],
        shape=case["shape"],
        metrics=case["metrics"],
        drop=case.get("drop", 0.0),
        as_date=case.get("as_date", False),
    )
    kw: dict[str, Any] = dict(
        network="NEM",
        metrics=[Metric(m) for m in case["metrics"]],
        interval=_interval_for(case["step"]),
        primary_grouping=case["primary"],
        secondary_groupings=case["secondary"],
        facility_code=case.get("facility"),
    )
    expected = reference_format(results=[dict(zip(cols, r, strict=True)) for r in copy.deepcopy(rows)], **kw)
    got = rows_to_timeseries_list(cols, rows, **kw)
    direct = format_timeseries_rows(cols, rows, **kw)

    dump = lambda x: json.dumps(x, separators=(",", ":"), default=str)  # noqa: E731
    assert dump(got) == dump(expected)
    assert dump(direct) == dump(expected)
    assert got == expected
