"""
OpenNEM queries for renewable proportion

"""

import logging
from datetime import datetime

from sqlalchemy import text

from opennem.db import get_read_session
from opennem.queries.utils import list_to_case
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE
from opennem.utils.datatable import datatable_print

# Set up logging
logger = logging.getLogger(__name__)


async def get_renewable_energy_proportion(
    network: NetworkSchema,
    bucket_size: MilestonePeriod,
    start_date: datetime,
    end_date: datetime,
    network_region: str | None = None,
    group_by_region: bool = True,
    group_by_fueltech: bool = False,
    group_by_renewable: bool = False,
) -> list[dict]:
    """
    Get the renewable energy proportion for a given network region and date range

    Args:
        network: Network schema to query
        bucket_size: Time bucket size for aggregation
        start_date: Start date for query range
        end_date: End date for query range
        network_region: Optional network region filter
        group_by_region: Group results by network region
        group_by_fueltech: Group results by fuel tech
        group_by_renewable: Group results by renewable status

    Returns:
        List of dicts containing renewable proportion data
    """
    # Input validation
    assert group_by_fueltech or group_by_renewable, "one of group_by_fueltech or group_by_renewable must be true"

    rooftop_networks = ["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"]
    if network in [NetworkWEM, NetworkWEMDE]:
        rooftop_networks = ["APVI"]

    bucket_size_sql = get_bucket_interval(bucket_size)

    sql_query = text(f"""
    WITH generation_rooftop AS (
        SELECT
            time_bucket_gapfill('5 min', fs.interval) as interval,
            fs.network_region,
            CASE WHEN :group_by_fueltech THEN 'solar' ELSE NULL END as fueltech_id,
            locf(max(fs.generated)) as generation
        FROM at_facility_intervals fs
        WHERE fs.network_id IN ({list_to_case(rooftop_networks)})
            AND fs.fueltech_code = 'solar_rooftop'
            AND fs.interval >= :start_date
            AND fs.interval < :end_date
        GROUP BY 1, 2, 3
    ),
    generation AS (
        SELECT
            time_bucket_gapfill('5 min', fs.interval) as interval,
            fs.network_id,
            fs.network_region,
            CASE
                WHEN :group_by_fueltech THEN ftg.code
                WHEN :group_by_renewable THEN 'renewables'
                ELSE NULL
            END as fueltech_id,
            sum(fs.generated) as generation
        FROM at_facility_intervals fs
        JOIN fueltech ft ON ft.code = fs.fueltech_code
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE fs.network_id IN ('NEM', 'AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL')
            AND fs.fueltech_code != 'solar_rooftop'
            AND fs.interval >= :start_date
            AND fs.interval < :end_date
            AND (:group_by_renewable = false OR ft.renewable = true)
        GROUP BY 1, 2, 3, 4
    ),
    demand AS (
        SELECT
            time_bucket_gapfill('5 min', interval) as interval,
            network_region,
            locf(max(demand)) as demand_total
        FROM mv_balancing_summary
        WHERE network_id = 'NEM'
            AND interval >= :start_date
            AND interval < :end_date
        GROUP BY 1, 2
    )
    SELECT
        time_bucket('{bucket_size_sql}', g.interval) as interval,
        g.network_id,
        CASE WHEN :group_by_region THEN g.network_region ELSE NULL END as network_region,
        CASE
            WHEN :group_by_fueltech THEN g.fueltech_id
            WHEN :group_by_renewable THEN 'renewables'
            ELSE NULL
        END as fueltech_id,
        round(cast(max(g.generation) as numeric), 2) as generation,
        round(cast(max(gr.generation) as numeric), 2) as generation_rooftop,
        round(cast(avg(d.demand_total) as numeric), 2) as demand_total,
        CASE
            WHEN sum(d.demand_total) > 0 THEN
                round(cast(
                    (
                        (CASE WHEN NOT :group_by_fueltech
                            THEN sum(gr.generation)
                            ELSE 0
                        END + coalesce(sum(g.generation), 0)) /
                        cast((sum(d.demand_total) + coalesce(sum(gr.generation), 0)) as numeric)
                    ) * 100 as numeric
                ), 4)
            ELSE NULL
        END as proportion
    FROM generation g
    JOIN generation_rooftop gr ON gr.interval = g.interval
        AND gr.network_region = g.network_region
    JOIN demand d ON d.interval = g.interval
        AND d.network_region = g.network_region
    WHERE ({network_region or "NULL"} IS NULL OR d.network_region = {network_region or "NULL"})
    GROUP BY 1, 2, 3, 4
    ORDER BY 1, 2, 3, 4
    """)

    params = {
        "group_by_fueltech": group_by_fueltech,
        "start_date": start_date,
        "end_date": end_date,
        "group_by_renewable": group_by_renewable,
        "group_by_region": group_by_region,
    }

    async with get_read_session() as session:
        # Log the raw SQL with parameters
        compiled_query = sql_query.bindparams(**params).compile(compile_kwargs={"literal_binds": True})  # noqa: F841
        # logger.debug(dedent(str(compiled_query)))

        # Execute the query
        result = await session.execute(sql_query, params)
        rows = result.fetchall()
        column_names = result.keys()
        return [dict(zip(column_names, row, strict=False)) for row in rows]


if __name__ == "__main__":
    import asyncio

    # Set up logging for the main execution
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    async def main():
        results = await get_renewable_energy_proportion(
            network=NetworkNEM,
            bucket_size=MilestonePeriod.interval,
            start_date=datetime.fromisoformat("2024-08-01 12:00:00"),
            end_date=datetime.fromisoformat("2024-08-01 12:10:00"),
            group_by_region=True,
            group_by_fueltech=False,
            group_by_renewable=False,
        )
        datatable_print(results)

    asyncio.run(main())
