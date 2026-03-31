import logging

from opennem import settings
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db.clickhouse import get_clickhouse_client
from opennem.utils.dates import fmt_clickhouse_dt

logger = logging.getLogger("opennem.controllers.flows")


async def power_flows_per_interval(
    time_series: OpennemExportSeries,
    network_region_code: str,
) -> OpennemDataSet | None:
    """Gets power flows per interval from CH market_summary."""
    ch_client = get_clickhouse_client()
    unit_power = get_unit("power")
    date_range = time_series.get_range()

    query = f"""
    SELECT
        interval, network_region,
        power_imports, power_exports,
        emissions_imports, emissions_exports,
        mv_imports, mv_exports,
        if(abs(power_imports) > 0, emissions_imports / abs(power_imports / 12), 0) as ef_imports,
        if(power_exports > 0, emissions_exports / (power_exports / 12), 0) as ef_exports
    FROM (
        SELECT
            toStartOfFiveMinutes(toDateTime(interval)) as interval,
            network_region,
            coalesce(sum(energy_imports) * 12, 0) as power_imports,
            coalesce(sum(energy_exports) * 12, 0) as power_exports,
            coalesce(sum(emissions_imports), 0) as emissions_imports,
            coalesce(sum(emissions_exports), 0) as emissions_exports,
            coalesce(sum(market_value_imports), 0) as mv_imports,
            coalesce(sum(market_value_exports), 0) as mv_exports
        FROM market_summary FINAL
        WHERE network_id = '{time_series.network.code}'
            AND network_region = '{network_region_code}'
            AND toDateTime(interval) >= toDateTime('{fmt_clickhouse_dt(date_range.start)}')
            AND toDateTime(interval) <= toDateTime('{fmt_clickhouse_dt(date_range.end)}')
        GROUP BY 1, 2
    )
    ORDER BY 1 DESC
    """

    rows = ch_client.execute(query)

    if not rows:
        logger.warning(f"No flow results for {network_region_code}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[2], group_by="imports") for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[3], group_by="exports") for i in rows]
    emissions_imports = [DataQueryResult(interval=i[0], result=i[4], group_by="imports") for i in rows]
    emissions_exports = [DataQueryResult(interval=i[0], result=i[5], group_by="exports") for i in rows]
    ef_imports = [DataQueryResult(interval=i[0], result=i[8], group_by="imports") for i in rows]
    ef_exports = [DataQueryResult(interval=i[0], result=i[9], group_by="exports") for i in rows]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        return None

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )
    result.append_set(result_exports)

    result.append_set(
        stats_factory(
            emissions_imports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions"),
            region=network_region_code,
            fueltech_group=True,
        )
    )
    result.append_set(
        stats_factory(
            emissions_exports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions"),
            region=network_region_code,
            fueltech_group=True,
        )
    )

    if settings.show_emission_factors_in_power_outputs:
        result.append_set(
            stats_factory(
                ef_imports,
                network=time_series.network,
                interval=time_series.interval,
                units=get_unit("emissions_factor"),
                region=network_region_code,
                fueltech_group=True,
            )
        )
        result.append_set(
            stats_factory(
                ef_exports,
                network=time_series.network,
                interval=time_series.interval,
                units=get_unit("emissions_factor"),
                region=network_region_code,
                fueltech_group=True,
            )
        )

    return result
