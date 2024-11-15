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
