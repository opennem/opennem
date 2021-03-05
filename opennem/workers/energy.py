import logging
from datetime import datetime, timedelta
from itertools import groupby
from textwrap import dedent
from typing import Dict, List, Optional

from pytz import FixedOffset

from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.energy import energy_sum, shape_energy_dataframe
from opennem.core.facility.fueltechs import load_fueltechs
from opennem.db import get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.diff.versions import CUR_YEAR, get_network_regions
from opennem.notifications.slack import slack_message
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.interval import get_human_interval

logger = logging.getLogger("opennem.workers.energy")

# For debugging queries
DRY_RUN = False


def get_generated_query(
    network_region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: Optional[str] = None,
) -> str:
    # @TODO support refresh energies for a single duid or station

    __sql = """
    select
        fs.trading_interval at time zone 'AEST' as trading_interval,
        fs.facility_code,
        fs.network_id,
        f.fueltech_id,
        generated
    from
        facility_scada fs
        left join facility f on fs.facility_code = f.code
    where
        fs.network_id='{network_id}'
        and f.network_region='{network_region}'
        and fs.trading_interval >= '{date_min}'
        and fs.trading_interval <= '{date_max}'
        and fs.is_forecast is False
        {fueltech_match}
        and fs.generated is not null
    order by fs.trading_interval asc, 2;
    """

    fueltech_match = ""

    if fueltech_id:
        fueltech_match = f"and f.fueltech_id = '{fueltech_id}'"

    query = __sql.format(
        network_id=network.code,
        network_region=network_region,
        date_min=date_min,
        date_max=date_max,
        fueltech_match=fueltech_match,
    )

    return dedent(query)


def get_flows_query(
    network_region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: str,
) -> str:
    if fueltech_id not in ["imports", "exports"]:
        raise Exception("Query only for improts or exports")

    # imports
    flow_direction = "<"

    if fueltech_id == "exports":
        flow_direction = ">"

    query = """
    select
        bs.trading_interval at time zone 'AEST' as trading_interval,
        {fueltech_id} as facility_code,
        bs.network_id,
        bs.network_region as facility_code,
        case when bs.net_interchange {flow_direction} 0 then
            bs.net_interchange
        else 0
        end as generated
    from balancing_summary bs
    where
        bs.network_id='{network_id}'
        and bs.network_region='{network_region}'
        and bs.trading_interval >= '{date_min}'
        and bs.trading_interval <= '{date_max}'
    order by trading_interval asc;
    """.format(
        fueltech_id=fueltech_id,
        flow_direction=flow_direction,
        network_id=network.code,
        network_region=network_region,
        date_min=date_min - timedelta(minutes=10),
        date_max=date_max + timedelta(minutes=10),
    )

    return dedent(query)


def get_generated(
    network_region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: Optional[str] = None,
) -> List[Dict]:
    """Gets generated values for a date range for a network and network region
    and optionally for a single fueltech"""

    # @TODO support refresh energies for a single duid or station

    query = get_generated_query(network_region, date_min, date_max, network, fueltech_id)

    engine = get_database_engine()

    results = []

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            try:
                results = list(c.execute(query))
            except Exception as e:
                logger.error(e)

    logger.debug("Got back {} rows".format(len(results)))

    return results


def get_flows(
    network_region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: str,
) -> List[Dict]:
    """Gets flows"""

    query = get_flows_query(network_region, date_min, date_max, network, fueltech_id)

    engine = get_database_engine()

    results = []

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            try:
                results = list(c.execute(query))
            except Exception as e:
                logger.error(e)

    logger.debug("Got back {} flow rows".format(len(results)))

    return results


def insert_energies(results: List[Dict], network: NetworkSchema) -> int:
    """Takes a list of generation values and calculates energies and bulk-inserts
    into the database"""

    # Get the energy sums as a dataframe
    esdf = energy_sum(results, network=network)

    # Add metadata
    esdf["created_by"] = "opennem.worker.energy"
    esdf["created_at"] = ""
    esdf["updated_at"] = datetime.now()
    esdf["generated"] = None
    esdf["is_forecast"] = False

    # reorder columns
    columns = [
        "created_by",
        "created_at",
        "updated_at",
        "network_id",
        "trading_interval",
        "facility_code",
        "generated",
        "eoi_quantity",
        "is_forecast",
    ]
    esdf = esdf[columns]

    records_to_store: List[Dict] = esdf.to_dict("records")

    if len(records_to_store) < 1:
        logger.error("No records returned from energy sum")
        return 0

    # dedupe records
    return_records_grouped = {}

    for pk_values, rec_value in groupby(
        records_to_store,
        key=lambda r: (
            r.get("trading_interval"),
            r.get("network_id"),
            r.get("facility_code"),
        ),
    ):
        if pk_values not in return_records_grouped:
            return_records_grouped[pk_values] = list(rec_value).pop()

    records_to_store = list(return_records_grouped.values())

    # Build SQL + CSV and bulk-insert
    sql_query = build_insert_query(FacilityScada, ["updated_at", "eoi_quantity"])
    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()

    csv_content = generate_csv_from_records(
        FacilityScada,
        records_to_store,
        column_names=records_to_store[0].keys(),
    )

    try:
        cursor.copy_expert(sql_query, csv_content)
        conn.commit()
    except Exception as e:
        logger.error("Error inserting records: {}".format(e))
        return 0

    logger.info("Inserted {} records".format(len(records_to_store)))

    return len(records_to_store)


def get_date_range(network: NetworkSchema) -> DatetimeRange:
    date_range = get_scada_range(network=NetworkNEM)

    time_series = TimeSeries(
        start=date_range.start,
        end=date_range.end,
        interval=human_to_interval("1d"),
        period=human_to_period("all"),
        network=network,
    )

    return time_series.get_range()


def run_energy_calc(
    region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: Optional[str] = None,
) -> int:
    generated_results: List[Dict] = []

    if fueltech_id in ["_imports", "_exports"]:
        generated_results = get_flows(
            region, date_min, date_max, network=network, fueltech_id=fueltech_id
        )
    else:
        generated_results = get_generated(
            region, date_min, date_max, network=network, fueltech_id=fueltech_id
        )

    num_records = 0

    try:
        if len(generated_results) < 1:
            logger.warn(
                "No results from get_generated query for {} {} {}".format(
                    region, date_max, fueltech_id
                )
            )
            return 0

        generated_frame = shape_energy_dataframe(generated_results)

        num_records = insert_energies(generated_frame, network=network)

        logger.info("Done {} for {} => {}".format(region, date_min, date_max))
    except Exception as e:
        logger.error(e)
        slack_message("Energy archive error: {}".format(e))

    return num_records


def run_energy_update_archive(
    year: int = 2021,
    months: Optional[List[int]] = None,
    days: Optional[int] = None,
    regions: Optional[List[str]] = None,
    fueltech: Optional[str] = None,
    network: NetworkSchema = NetworkNEM,
) -> None:

    date_range = get_date_range(network=network)

    if not months:
        months = list(range(1, 13))

    if not regions:
        regions = [i.code for i in get_network_regions(network)]

    fueltechs = [fueltech]

    if not fueltech:
        fueltechs = [i for i in load_fueltechs().keys()]

    for month in months:
        date_min = datetime(
            year=year, month=month, day=1, hour=0, minute=0, second=0, tzinfo=FixedOffset(600)
        )

        date_max = date_min + get_human_interval("1M")

        if days:
            date_max = datetime(
                year=year,
                month=month,
                day=1 + days,
                hour=0,
                minute=0,
                second=0,
                tzinfo=FixedOffset(600),
            )

        date_min = date_min - timedelta(minutes=10)
        date_max = date_max + timedelta(minutes=10)

        if date_max > date_range.end:
            date_max = date_range.end

        if date_min > date_max:
            slack_message("Reached end of energy archive")
            logger.debug("reached end of archive")
            break

        for region in regions:
            for fueltech_id in fueltechs:
                run_energy_calc(
                    region, date_min, date_max, fueltech_id=fueltech_id, network=network
                )


def run_energy_update_yesterday(
    network: NetworkSchema = NetworkNEM,
) -> None:
    """Run energy sum update for yesterday. This task is scheduled
    in scheduler/db

    This is NEM only atm"""

    # today_midnight in NEM time
    today_midnight = datetime.now().replace(
        tzinfo=network.get_fixed_offset(), microsecond=0, hour=0, minute=0, second=0
    )

    date_min = today_midnight - timedelta(days=1)
    date_max = date_min + timedelta(days=1, minutes=10)

    regions = [i.code for i in get_network_regions(network)]

    for region in regions:
        run_energy_calc(region, date_min, date_max, network=network)

    slack_message("Ran energy dailies for regions: {}".format(",".join(regions)))


def run_energy_update_all() -> None:
    """Runs energy update for all regions and all years for one-off
    inserts"""
    for year in range(CUR_YEAR, 2009, -1):
        run_energy_update_archive(year=year)


if __name__ == "__main__":
    # run_energy_update_archive(year=2021, regions=["NSW1"], fueltech="coal_black")
    run_energy_update_all()
    # run_energy_update_yesterday()
