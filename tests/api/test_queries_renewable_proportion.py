"""Lock the renewable-proportion SQL to emit NULL (not 0) when demand_gross is absent.

Regression for opennem#575: the freshest/settling interval could be served before
demand_gross landed, and the old `if(sum(dg) > 0, ..., 0)` fallback produced a spurious
0% renewable_proportion that "healed" on the next poll. The proportion must instead
return NULL so it serialises to `null` ("not yet available"), never a non-physical 0%.
"""

from datetime import datetime

import pytest

from opennem.api.queries import QueryType, get_timeseries_query
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM


@pytest.mark.parametrize("metric", [Metric.RENEWABLE_PROPORTION, Metric.RENEWABLE_WITH_STORAGE_PROPORTION])
def test_proportion_returns_null_not_zero_when_demand_gross_absent(metric):
    """The else-branch of the proportion guard must be NULL, never a literal 0."""
    sql, _, _ = get_timeseries_query(
        query_type=QueryType.MARKET,
        network=NetworkNEM,
        metrics=[metric],
        interval=Interval.INTERVAL,
        date_start=datetime(2026, 6, 16, 0, 0),
        date_end=datetime(2026, 6, 17, 0, 0),
        network_region="VIC1",
    )
    out = f"{metric.value.lower()}"
    # guarded division still present
    assert "if(sum(dg_sum_inner) > 0," in sql
    # else-branch is NULL, and the metric column is emitted
    assert f", NULL) AS {out}" in sql
    # the old spurious-0 fallback must be gone
    assert f", 0), 2) AS {out}" not in sql
