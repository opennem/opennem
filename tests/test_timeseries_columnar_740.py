# ruff: noqa: E501
"""Columnar timeseries fast path (#740): series-array rows must give the exact row-path response."""

import random
from datetime import datetime, timedelta
from typing import Any

import orjson
import pytest

from opennem.api.queries import QueryType, columnar_supported, get_timeseries_query
from opennem.api.timeseries import format_timeseries_columnar, rows_to_timeseries_list
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval

_START = datetime(2026, 10, 1)
_STEP = {Interval.INTERVAL: timedelta(minutes=5), Interval.HALF_HOUR: timedelta(minutes=30), Interval.DAY: timedelta(days=1)}


def _rows(
    interval: Interval, regions: list[str | None], fueltechs: list[str | None], n: int, seed: int, gap_prob: float
) -> list[tuple[Any, ...]]:
    """Per-interval rows as clickhouse returns them: interval DESC, then key columns ascending."""
    rnd = random.Random(seed)
    rows: list[tuple[Any, ...]] = []
    for i in range(n):
        ts = _START + _STEP[interval] * i
        for r in regions:
            for ft in fueltechs:
                # each series starts/stops at a different point; some interior buckets are missing
                if i < (hash((r, ft)) % 7) or rnd.random() < gap_prob:
                    continue
                key = tuple(k for k in (r, ft) if k is not None)
                a = None if rnd.random() < 0.1 else round(rnd.random() * 1000, 6)
                rows.append((ts, "NEM", *key, a, round(rnd.random(), 6)))
    rows.sort(key=lambda x: (-x[0].timestamp(), *x[2:-2]))
    return rows


def _to_series_rows(rows: list[tuple[Any, ...]], n_keys: int, n_metrics: int, suffix: str) -> list[tuple[Any, ...]]:
    """What the wrapped clickhouse query returns, computed in python."""
    series: dict[tuple[Any, ...], list[tuple[Any, ...]]] = {}
    for row in rows:
        series.setdefault(row[2 : 2 + n_keys], []).append(row)
    ordered = sorted(series.items(), key=lambda kv: (-max(r[0] for r in kv[1]).timestamp(), kv[0]))
    out = []
    for key, rs in ordered:
        rs = sorted(rs, key=lambda r: r[0])
        out.append(
            (
                *key,
                [r[0].strftime("%Y-%m-%dT%H:%M:%S") + suffix for r in rs],
                *([r[2 + n_keys + m] for r in rs] for m in range(n_metrics)),
            )
        )
    return out


CASES = [
    # (interval, regions, fueltechs, primary, secondary, metrics, gap_prob)
    (Interval.INTERVAL, [None], [None], PrimaryGrouping.NETWORK, None, [Metric.PRICE, Metric.DEMAND], 0.0),
    (Interval.INTERVAL, [None], [None], PrimaryGrouping.NETWORK, None, [Metric.PRICE], 0.3),
    (Interval.INTERVAL, ["NSW1", "VIC1", "TAS1"], [None], PrimaryGrouping.NETWORK_REGION, None, [Metric.PRICE, Metric.DEMAND], 0.1),
    (Interval.INTERVAL, [None], ["coal_black", "solar_utility", "wind"], PrimaryGrouping.NETWORK, [SecondaryGrouping.FUELTECH], [Metric.POWER, Metric.EMISSIONS], 0.0),
    (Interval.HALF_HOUR, ["NSW1", "QLD1"], ["gas_ccgt", "wind", "battery_discharging"], PrimaryGrouping.NETWORK_REGION, [SecondaryGrouping.FUELTECH], [Metric.POWER], 0.2),
    (Interval.DAY, ["NSW1", "SA1"], ["gas_ocgt", "hydro"], PrimaryGrouping.NETWORK_REGION, [SecondaryGrouping.FUELTECH_GROUP], [Metric.POWER, Metric.POWER], 0.15),
]  # fmt: skip


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_columnar_matches_row_path(case: tuple[Any, ...], seed: int) -> None:
    interval, regions, fueltechs, primary, secondary, metrics, gap_prob = case
    n_keys = int(regions != [None]) + int(fueltechs != [None])
    key_names = [c for c, used in (("network_region", regions != [None]), ("fueltech", fueltechs != [None])) if used]
    if secondary == [SecondaryGrouping.FUELTECH_GROUP]:
        key_names = [k.replace("fueltech", "fueltech_group") for k in key_names]
    names = list(dict.fromkeys(m.value.lower() for m in metrics))
    # row path metric columns follow the request (repeats included); use distinct values for 2 columns
    rows = _rows(interval, regions, fueltechs, 80, seed, gap_prob)
    if len(names) == 1:
        rows = [(*r[:-2], r[-2]) for r in rows]
    suffix = get_api_network_from_code("NEM").get_offset_string()

    row_cols = ["interval", "network", *key_names, *names]
    kw = {
        "network": "NEM", "metrics": metrics, "interval": interval,
        "primary_grouping": primary, "secondary_groupings": secondary,
    }  # fmt: skip
    expected = rows_to_timeseries_list(row_cols, rows, **kw)

    series_rows = _to_series_rows(rows, n_keys, len(names), suffix)
    got = format_timeseries_columnar([*key_names, "ts", *names], series_rows, **kw)

    assert orjson.dumps(got) == orjson.dumps(expected)


def test_columnar_empty_rows() -> None:
    assert format_timeseries_columnar(["ts", "price"], [], network="NEM", metrics=[Metric.PRICE], interval=Interval.INTERVAL,
                                      primary_grouping=PrimaryGrouping.NETWORK, secondary_groupings=None) == []  # fmt: skip


def test_columnar_supported_matrix() -> None:
    D, M = QueryType.DATA, QueryType.MARKET
    N, R = PrimaryGrouping.NETWORK, PrimaryGrouping.NETWORK_REGION
    assert columnar_supported(D, N, None)
    assert columnar_supported(D, R, [SecondaryGrouping.FUELTECH])
    assert columnar_supported(D, R, [SecondaryGrouping.FUELTECH_GROUP])
    assert columnar_supported(M, R, None)
    assert not columnar_supported(D, R, [SecondaryGrouping.STATUS])
    assert not columnar_supported(D, R, [SecondaryGrouping.RENEWABLE])
    assert not columnar_supported(D, R, [SecondaryGrouping.FUELTECH, SecondaryGrouping.RENEWABLE])
    assert not columnar_supported(QueryType.FACILITY, N, None)
    assert not columnar_supported(D, N, None, facility_code=["X"])


def test_columnar_query_shape() -> None:
    sql, params, cols = get_timeseries_query(
        QueryType.DATA,
        get_api_network_from_code("NEM"),
        [Metric.POWER, Metric.EMISSIONS, Metric.POWER],
        Interval.INTERVAL,
        datetime(2026, 10, 1),
        datetime(2026, 10, 8),
        PrimaryGrouping.NETWORK_REGION,
        [SecondaryGrouping.FUELTECH],
        columnar=True,
    )
    assert cols == ["network_region", "fueltech", "ts", "power", "emissions"]
    assert "%%Y-%%m-%%dT%%H:%%i:%%S" in sql and "'+10:00'" in sql
    assert "ORDER BY max(iv) DESC, network_region, fueltech" in sql
    assert "ORDER BY interval DESC" not in sql
    assert "date_start" in params

    with pytest.raises(ValueError):
        get_timeseries_query(
            QueryType.DATA, get_api_network_from_code("NEM"), [Metric.POWER], Interval.INTERVAL,
            datetime(2026, 10, 1), datetime(2026, 10, 8), PrimaryGrouping.NETWORK, [SecondaryGrouping.STATUS], columnar=True,
        )  # fmt: skip
