"""Demand queries — ClickHouse only"""

from sqlalchemy import TextClause, text

from opennem.api.stats.controllers import networks_to_in
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkSchema


def network_demand_clickhouse_query(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> TextClause:
    """Query demand data from ClickHouse market_summary table.

    Uses materialized views for daily and monthly aggregations.
    """
    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    interval_sql = time_series.interval.interval_sql
    use_daily_mv = interval_sql in ["1 day"] or "day" in interval_sql
    use_monthly_mv = "month" in interval_sql

    if use_daily_mv and not use_monthly_mv:
        __query = """
            SELECT date AS interval, network_id, {network_region_select}
                round(demand_total_energy_daily, 4) as demand_energy,
                round(demand_total_market_value_daily * 1000, 4) as demand_market_value
            FROM market_summary_daily_mv
            WHERE date >= toDate('{date_min}') AND date <= toDate('{date_max}')
                AND network_id IN ({network_ids}) {network_region_filter}
            ORDER BY date DESC
        """
    elif use_monthly_mv:
        __query = """
            SELECT month AS interval, network_id, {network_region_select}
                round(demand_total_energy_monthly, 4) as demand_energy,
                round(demand_total_market_value_monthly * 1000, 4) as demand_market_value
            FROM market_summary_monthly_mv
            WHERE month >= toStartOfMonth(toDate('{date_min}'))
                AND month <= toStartOfMonth(toDate('{date_max}'))
                AND network_id IN ({network_ids}) {network_region_filter}
            ORDER BY month DESC
        """
    else:
        __query = """
            SELECT toStartOfInterval(interval, INTERVAL {interval_size} {interval_unit}) AS interval,
                network_id, {network_region_select}
                round(sum(demand_total_energy), 4) as demand_energy,
                round(sum(demand_total_market_value) * 1000, 4) as demand_market_value
            FROM market_summary FINAL
            WHERE interval >= toDateTime64('{date_min}', 3)
                AND interval <= toDateTime64('{date_max}', 3)
                AND network_id IN ({network_ids}) {network_region_filter}
            GROUP BY interval, network_id {network_region_group}
            ORDER BY interval DESC
        """

    network_region_select = "network_region," if network_region else ""
    network_region_filter = f"AND network_region = '{network_region}'" if network_region else ""
    network_region_group = ", network_region" if network_region else ""

    time_series_range = time_series.get_range()
    end = time_series_range.end
    start = time_series_range.start
    date_max = end.replace(tzinfo=None) if hasattr(end, "replace") else end
    date_min = start.replace(tzinfo=None) if hasattr(start, "replace") else start

    network_ids = networks_to_in(networks_query)

    # Parse interval for non-MV path
    interval_size = 1
    interval_unit = "day"
    if "week" in interval_sql:
        interval_unit = "week"
    elif "year" in interval_sql:
        interval_unit = "year"

    query = __query.format(
        date_max=date_max,
        date_min=date_min,
        network_ids=network_ids,
        network_region_select=network_region_select,
        network_region_filter=network_region_filter,
        network_region_group=network_region_group,
        interval_size=interval_size,
        interval_unit=interval_unit,
    )

    return text(query)
