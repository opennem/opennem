from sqlalchemy import TextClause, text

from opennem.api.stats.controllers import networks_to_in
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkSchema


def network_demand_query(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> TextClause:
    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
        select
            time_bucket_gapfill('{interval}', interval) as interval,
            network_id,
            avg(demand) as demand
        from mv_balancing_summary bs
        where
            bs.interval <= '{date_max}' and
            bs.interval >= '{date_min}' and
            {network_query}
            {network_region_query}
            1=1
        group by
            1, {groups_additional}
        order by 1 desc;
    """

    group_keys = ["network_id"]
    network_region_query = ""

    if network_region:
        group_keys.append("network_region")
        network_region_query = f"bs.network_region = '{network_region}' and "

    groups_additional = ", ".join(group_keys)

    network_query = f"bs.network_id IN ({networks_to_in(networks_query)}) and "

    # Get the time range using either the old way or the new v4 way
    time_series_range = time_series.get_range()
    date_max = time_series_range.end
    date_min = time_series_range.start

    query = __query.format(
        timezone=time_series.network.timezone_database,
        interval=time_series.interval.interval_sql,
        date_max=date_max,
        date_min=date_min,
        network_id=time_series.network.code,
        network_query=network_query,
        network_region_query=network_region_query,
        groups_additional=groups_additional,
    )

    return text(query)


def network_demand_clickhouse_query(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> TextClause:
    """Query demand data from ClickHouse market_summary table.

    This replaces the PostgreSQL at_network_demand query by using
    the market_summary table in ClickHouse which contains
    demand_energy and demand_market_value columns.

    Uses materialized views for daily and monthly aggregations for better performance.
    """
    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    # Parse interval for ClickHouse
    interval_sql = time_series.interval.interval_sql
    use_daily_mv = False
    use_monthly_mv = False

    if "1 day" in interval_sql:
        interval_size = 1
        interval_unit = "day"
        use_daily_mv = True
    elif "1 month" in interval_sql:
        interval_size = 1
        interval_unit = "month"
        use_monthly_mv = True
    elif "1 week" in interval_sql:
        interval_size = 1
        interval_unit = "week"
    elif "1 year" in interval_sql:
        interval_size = 1
        interval_unit = "year"
    else:
        # Default to day
        interval_size = 1
        interval_unit = "day"
        use_daily_mv = True

    # Use materialized views for daily and monthly queries
    if use_daily_mv:
        __query = """
            SELECT
                date AS interval,
                network_id,
                {network_region_select}
                round(demand_total_energy_daily, 4) as demand_energy,
                round(demand_total_market_value_daily * 1000, 4) as demand_market_value
            FROM market_summary_daily_mv
            WHERE
                date >= toDate('{date_min}')
                AND date <= toDate('{date_max}')
                AND network_id IN ({network_ids})
                {network_region_filter}
            ORDER BY date DESC
        """
    elif use_monthly_mv:
        __query = """
            SELECT
                month AS interval,
                network_id,
                {network_region_select}
                round(demand_total_energy_monthly, 4) as demand_energy,
                round(demand_total_market_value_monthly * 1000, 4) as demand_market_value
            FROM market_summary_monthly_mv
            WHERE
                month >= toStartOfMonth(toDate('{date_min}'))
                AND month <= toStartOfMonth(toDate('{date_max}'))
                AND network_id IN ({network_ids})
                {network_region_filter}
            ORDER BY month DESC
        """
    else:
        # Use base table for other intervals
        __query = """
            SELECT
                toStartOfInterval(interval, INTERVAL {interval_size} {interval_unit}) AS interval,
                network_id,
                {network_region_select}
                round(sum(demand_total_energy), 4) as demand_energy,
                round(sum(demand_total_market_value) * 1000, 4) as demand_market_value
            FROM market_summary FINAL
            WHERE
                interval >= toDateTime64('{date_min}', 3)
                AND interval <= toDateTime64('{date_max}', 3)
                AND network_id IN ({network_ids})
                {network_region_filter}
            GROUP BY
                interval,
                network_id
                {network_region_group}
            ORDER BY interval DESC
        """

    network_region_select = ""
    network_region_filter = ""
    network_region_group = ""

    if network_region:
        network_region_select = "network_region,"
        network_region_filter = f"AND network_region = '{network_region}'"
        network_region_group = ", network_region"

    # Get the time range - ClickHouse needs timezone-naive datetime strings
    time_series_range = time_series.get_range()

    # Remove timezone info for ClickHouse compatibility
    if hasattr(time_series_range.end, "replace"):
        date_max = time_series_range.end.replace(tzinfo=None)
        date_min = time_series_range.start.replace(tzinfo=None)
    else:
        # If they're already strings, strip timezone suffix
        date_max = str(time_series_range.end).split("+")[0].split("Z")[0]
        date_min = str(time_series_range.start).split("+")[0].split("Z")[0]

    network_ids = networks_to_in(networks_query)

    # Build the query based on whether we're using materialized views or not
    if use_daily_mv or use_monthly_mv:
        # Materialized views don't need interval_size and interval_unit
        query = __query.format(
            date_max=date_max,
            date_min=date_min,
            network_ids=network_ids,
            network_region_select=network_region_select,
            network_region_filter=network_region_filter,
        )
    else:
        # Base table query needs the full set of parameters
        query = __query.format(
            interval_size=interval_size,
            interval_unit=interval_unit,
            date_max=date_max,
            date_min=date_min,
            network_ids=network_ids,
            network_region_select=network_region_select,
            network_region_filter=network_region_filter,
            network_region_group=network_region_group,
        )

    return text(query)
