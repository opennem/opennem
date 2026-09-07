"""market_summary must only aggregate declared network regions.

The `regions` CTE used to be `SELECT DISTINCT network_id, network_region FROM balancing_summary`,
which pulled in every label the table happens to carry. Two of them are not markets of their own:

- WEM/WEMDE — the WEMDE dispatch feed, filed under the WEM network with its own region label over
  2023-10 to 2024-11. Demand for it is joined from the network-wide `wem_generation` CTE, so it
  emitted an exact duplicate of the WEM/WEM series and doubled every network-level WEM sum in that
  window (a 2024-02-19 daily demand energy milestone came out at precisely 2x).
- NEM/WEM — long-standing bad data with null demand.

The filter is on the PAIR. Filtering network_id and network_region independently still admits the
cross product, which is how NEM/WEM survived.
"""

from opennem.aggregates import market_summary as market_summary_mod
from opennem.schema.network import NetworkNEM, NetworkWEM


def test_declared_regions_cover_every_schema_region() -> None:
    pairs = market_summary_mod._declared_network_regions()

    for region in NetworkNEM.regions or []:
        assert ("NEM", region) in pairs

    for region in NetworkWEM.regions or []:
        assert ("WEM", region) in pairs


def test_declared_regions_exclude_the_duplicate_and_bad_pairs() -> None:
    pairs = market_summary_mod._declared_network_regions()

    assert ("WEM", "WEMDE") not in pairs
    assert ("NEM", "WEM") not in pairs
    assert ("WEM", "NSW1") not in pairs


def test_declared_regions_keep_retired_snowy1() -> None:
    """SNOWY1 was a real NEM region until July 2008 and still holds ~50 MW of demand in
    balancing_summary. It is absent from NetworkNEM.regions, so an allowlist built from the schema
    alone would silently drop a decade of NEM network-level demand."""
    assert ("NEM", "SNOWY1") in market_summary_mod._declared_network_regions()


def test_values_sql_renders_every_pair() -> None:
    values_sql = market_summary_mod._declared_network_regions_values_sql()

    for network_id, network_region in market_summary_mod._declared_network_regions():
        assert f"('{network_id}', '{network_region}')" in values_sql

    assert "WEMDE" not in values_sql
    # No bind-parameter markers: the surrounding query is an f-string over ':name' binds, and a
    # stray colon here would be parsed as one more bind by SQLAlchemy.
    assert ":" not in values_sql
