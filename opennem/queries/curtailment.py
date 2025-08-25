"""
OpenElectricity curtailment queries

"""

from datetime import datetime

from opennem.db.utils import get_clickhouse_interval
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.dates import get_last_complete_day_for_network


def get_network_curtailment_energy_query_analytics(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    interval: TimeInterval | None = None,
    network_region_code: str | None = None,
) -> str:
    """
    Get curtailment energy (total, solar and wind) from ClickHouse market_summary table.

    Args:
        network: Network schema (NEM, WEM, or AU)
        date_min: Start date
        date_max: End date (optional)
        interval: Time interval for aggregation (optional)
        network_region_code: Specific network region (optional)

    Returns:
        str: ClickHouse SQL query returning curtailment energy in MWh

    Note:
        Only NEM supports curtailment data. WEM has no curtailment data.
        For AU network, only NEM data is queried since WEM has no curtailment.
        Energy values are stored and returned in MWh.
    """
    if network != NetworkNEM:
        raise ValueError(f"Curtailment data is only supported on the NEM network. Got {network.code}")

    # If only a single interval with date_min set date_max to last complete NEM day
    if not date_max:
        date_max = get_last_complete_day_for_network(network)

    # If no interval provided get the default from the network
    if not interval:
        interval = network.get_interval()

    time_bucket = get_clickhouse_interval(interval)

    # network regions query and grouping
    network_regions_query = ""
    select_region = "'NEM' as network_region,"
    group_by_region = ""
    order_by_region = ""

    if network_region_code:
        network_regions_query = f"AND network_region = '{network_region_code.upper()}'"
        select_region = "network_region,"
        group_by_region = "network_region,"
        order_by_region = ", network_region"

    # strip timezone from date_min and date_max
    date_min = date_min.replace(tzinfo=None)
    date_max = date_max.replace(tzinfo=None)

    query = f"""
        SELECT
            {time_bucket}(interval) AS interval,
            network_id,
            {select_region}
            sum(curtailment_energy_total) AS curtailment_energy_total,
            sum(curtailment_energy_solar_total) AS curtailment_energy_solar_total,
            sum(curtailment_energy_wind_total) AS curtailment_energy_wind_total
        FROM market_summary FINAL
        WHERE
            network_id = 'NEM'
            AND interval >= parseDateTimeBestEffort('{date_min}')
            AND interval <= parseDateTimeBestEffort('{date_max}')
            {network_regions_query}
        GROUP BY
            interval,
            network_id{group_by_region and f", {group_by_region.rstrip(',')}" or ""}
        ORDER BY interval desc, network_id{order_by_region}
    """

    return query
