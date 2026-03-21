"""Price + demand queries — ClickHouse only"""

from datetime import datetime

from opennem.db.utils import get_clickhouse_interval
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval


def get_network_price_demand_query_analytics(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    interval: TimeInterval | None = None,
    network_region_code: str | None = None,
) -> str:
    """Price, demand and curtailment from ClickHouse market_summary."""
    if not date_max:
        date_max = date_min

    if not interval:
        interval = network.get_interval()

    time_bucket = get_clickhouse_interval(interval)

    network_regions_query = ""
    network_region_grouping = f"'{network.code}' as network_region,"

    if network_region_code:
        network_regions_query = f"and network_region = '{network_region_code.upper()}'"
        network_region_grouping = "network_region,"

    date_min = date_min.replace(tzinfo=None)
    date_max = date_max.replace(tzinfo=None)

    return f"""
        SELECT
            {time_bucket}(interval) AS interval,
            network_id,
            {network_region_grouping}
            avg(price) AS price,
            sum(demand) AS demand,
            sum(demand_total) AS demand_total,
            sum(curtailment_total) AS curtailment_total,
            sum(curtailment_solar_total) AS curtailment_solar_utility_total,
            sum(curtailment_wind_total) AS curtailment_wind_total
        FROM market_summary
        WHERE network_id = '{network.code}'
            AND interval >= parseDateTimeBestEffort('{date_min}')
            AND interval <= parseDateTimeBestEffort('{date_max}')
            {network_regions_query}
        GROUP BY 1, 2, 3
        ORDER BY 1 DESC, 2, 3
    """
