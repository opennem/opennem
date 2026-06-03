"""NEM/WEM price in the market_summary aggregate must locf with treat_null_as_missing.

Pre-2009 NEM balancing_summary has real 5-min rows (demand populated) with a
NULL price between the 30-min trading points. After time_bucket_gapfill('5
minutes', ...) these are NOT gapfill-created gaps, so:

  - plain avg(price)                                 -> NULL on 10/12 buckets
  - locf(avg(price))                                 -> still NULL (default locf
                                                        only fills gaps it made)
  - locf(avg(price), treat_null_as_missing => true)  -> carried forward, correct

Without the carry-forward, demand_market_value = demand_energy * price collapses
to ~1/6 (the #309 VWP bug: Jun-2008 demand price read $6.83 instead of ~$41).
This regressed twice (originally, then reintroduced by #542 which dropped locf
from the NEM path). This guards the price aggregation so it can't happen again.

Source-level guard (inspect.getsource) because the query is a local text() built
inside _get_market_summary_data and executed against a session, so there is no
returned SQL string to assert on without a TimescaleDB connection. Whitespace is
collapsed so the assertions survive reindentation / line-wrap changes.
"""

import inspect
import re

from opennem.aggregates.market_summary import _get_market_summary_data


def _query_source() -> str:
    """Function source with all runs of whitespace collapsed to single spaces."""
    return " ".join(inspect.getsource(_get_market_summary_data).split())


def test_nem_price_locf_with_treat_null_as_missing() -> None:
    src = _query_source()
    assert "locf(avg(CAST(price AS double precision)), treat_null_as_missing => true) as price_nem" in src, (
        "NEM price must be locf(avg(price), treat_null_as_missing => true) — plain avg/locf leaves pre-2009 "
        "in-data NULL prices unfilled and collapses the demand VWP to ~1/6 (#309, regressed by #542)"
    )


def test_wem_price_locf_with_treat_null_as_missing() -> None:
    src = _query_source()
    assert (
        "locf(avg(CAST(COALESCE(price_dispatch, price) AS double precision)), treat_null_as_missing => true) as price_wem"
    ) in src, "WEM price must also locf with treat_null_as_missing => true so 30-min trading prices fill the 5-min grid"


def test_price_nem_is_not_a_bare_avg() -> None:
    # The #542 regression form was exactly `avg(CAST(price AS double precision)) as price_nem`
    # (no locf wrapper). Assert that bare form is absent.
    src = _query_source()
    assert not re.search(r"(?<!locf\()avg\(CAST\(price AS double precision\)\) as price_nem", src), (
        "price_nem must not be a bare avg() — it has to be locf(avg(...), treat_null_as_missing => true) (#309/#542)"
    )
