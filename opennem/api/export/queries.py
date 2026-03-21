"""Export queries — PostgreSQL interconnector + stats only"""

import logging
from textwrap import dedent

from sqlalchemy import sql, text
from sqlalchemy.sql.elements import TextClause

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.stats import StatTypes

logger = logging.getLogger("opennem.api.export.queries")


def interconnector_power_flow(time_series: OpennemExportSeries, network_region: str) -> TextClause:
    """Get interconnector region flows from balancing_summary."""
    ___query = """
    select
        time_bucket_gapfill(INTERVAL '5 minutes', bs.interval) as interval,
        bs.network_region,
        case when max(bs.net_interchange) < 0 then max(bs.net_interchange) else 0 end as imports,
        case when max(bs.net_interchange) > 0 then max(bs.net_interchange) else 0 end as exports
    from balancing_summary bs
    where
        bs.network_id = '{network_id}' and
        bs.network_region= '{region}' and
        bs.trading_interval <= '{date_end}' and
        bs.trading_interval >= '{date_start}'
    group by 1, 2
    order by interval desc;
    """

    time_series_range = time_series.get_range()
    return text(
        ___query.format(
            network_id=time_series.network.code,
            region=network_region,
            date_start=time_series_range.start,
            date_end=time_series_range.end,
        )
    )


def interconnector_flow_network_regions_query(time_series: OpennemExportSeries, network_region: str | None = None) -> TextClause:
    """Get interconnector flows by region from facility_scada."""
    __query = """
    select
        t.trading_interval at time zone '{timezone}' as trading_interval,
        t.flow_region,
        t.network_region,
        t.interconnector_region_to,
        coalesce(sum(t.flow_power), NULL) as flow_power
    from
    (
        select
            time_bucket_gapfill('{interval_size}', fs.trading_interval) as trading_interval,
            f.network_region || '->' || f.interconnector_region_to as flow_region,
            f.network_region,
            f.interconnector_region_to,
            sum(fs.generated) as flow_power
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where
            f.interconnector is True
            and f.network_id='{network_id}'
            and fs.trading_interval <= '{date_end}'
            and fs.trading_interval >= '{date_start}'
            {region_query}
        group by 1, 2, 3, 4
    ) as t
    group by 1, 2, 3, 4
    order by 1 desc, 2 asc
    """

    region_query = f"and f.network_region='{network_region}'" if network_region else ""
    time_series_range = time_series.get_range()

    return text(
        __query.format(
            timezone=time_series.network.timezone_database,
            interval_size=time_series.interval.interval_sql,
            network_id=time_series.network.code,
            region_query=region_query,
            date_start=time_series_range.start,
            date_end=time_series_range.end,
        )
    )


def country_stats_query(stat_type: StatTypes, country: str = "au") -> TextClause:
    return sql.text(
        dedent("""
            select s.stat_date, s.value, s.stat_type
            from stats s
            where s.stat_type = :stat_type and s.country= :country
            order by s.stat_date desc
        """)
    ).bindparams(stat_type=str(stat_type), country=country)
