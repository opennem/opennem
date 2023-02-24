import logging
from datetime import datetime, timedelta
from itertools import groupby
from textwrap import dedent

from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.schema import ExportDatetimeRange, OpennemExportSeries
from opennem.core.energy import energy_sum, shape_energy_dataframe
from opennem.core.flows import FlowDirection, fueltech_to_flow, generated_flow_station_id
from opennem.core.fueltechs import ALL_FUELTECH_CODES
from opennem.core.network_regions import get_network_regions
from opennem.db import get_database_engine
from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
from opennem.db.models.opennem import FacilityScada
from opennem.queries.utils import duid_to_case
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.settings import settings
from opennem.utils.dates import DATE_CURRENT_YEAR, get_last_complete_day_for_network
from opennem.utils.interval import get_human_interval
from opennem.workers.facility_data_ranges import get_facility_seen_range

logger = logging.getLogger("opennem.workers.energy")

# For debugging queries
DRY_RUN = settings.dry_run
YEAR_EARLIEST = 2010

NEMWEB_DISPATCH_OLD_MIN_DATE = datetime.fromisoformat("1998-12-07 01:40:00")


def get_generated_query(
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    network_region: str | None = None,
    fueltech_id: str | None = None,
    facility_codes: list[str] | None = None,
) -> str:
    # @TODO support refresh energies for a single duid or station

    __sql = """
    select
        fs.trading_interval at time zone '{timezone}' as trading_interval,
        fs.facility_code,
        fs.network_id,
        f.fueltech_id,
        generated
    from
        facility_scada fs
        left join facility f on fs.facility_code = f.code
    where
        f.network_id='{network_id}'
        {network_region_query}
        and fs.trading_interval >= '{date_min}'
        and fs.trading_interval <= '{date_max}'
        and fs.is_forecast is False
        {fueltech_match}
        {facility_match}
        and fs.generated is not null
    order by fs.trading_interval asc, 2
    """

    fueltech_match = ""
    facility_match = ""
    network_region_query = ""

    if fueltech_id:
        fueltech_match = f"and f.fueltech_id = '{fueltech_id}'"

    if facility_codes:
        facility_match = f"and f.code in ({duid_to_case(facility_codes)})"

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = __sql.format(
        timezone=network.timezone_database,
        network_id=network.code,
        network_region=network_region,
        network_region_query=network_region_query,
        date_min=date_min.replace(tzinfo=network.get_fixed_offset()),
        date_max=(date_max + timedelta(minutes=5)).replace(tzinfo=network.get_fixed_offset()),
        fueltech_match=fueltech_match,
        facility_match=facility_match,
    )

    return dedent(query)


def get_clear_query(
    network_region: str,
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    fueltech_id: str | None = None,
) -> str:
    """Clear the energies for the range we're about to update"""

    __sql = """
    update facility_scada fs
    set
        eoi_quantity = NULL
    from facility f
    where
        f.code = fs.facility_code
        and f.network_id='{network_id}'
        and f.network_region='{network_region}'
        and fs.trading_interval >= '{date_min}'
        and fs.trading_interval <= '{date_max}'
        and fs.is_forecast is False
        {fueltech_match};
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
    flow: FlowDirection,
) -> str:
    flow_direction = "<"

    if flow == FlowDirection.exports:
        flow_direction = ">"

    facility_code = generated_flow_station_id(NetworkNEM, network_region, flow)

    query = """
    select
        bs.trading_interval at time zone 'AEST' as trading_interval,
        '{facility_code}' as facility_code,
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
        facility_code=facility_code,
        flow_direction=flow_direction,
        network_id=network.code,
        network_region=network_region,
        date_min=date_min - timedelta(minutes=10),
        date_max=date_max + timedelta(minutes=10),
    )

    return dedent(query)


def get_generated(
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    run_clear: bool = False,
    network_region: str | None = None,
    fueltech_id: str | None = None,
    facility_codes: list[str] | None = None,
) -> list[dict]:
    """Gets generated values for a date range for a network and network region
    and optionally for a single fueltech"""

    # holy prop drill!
    query = get_generated_query(
        date_min,
        date_max,
        network,
        fueltech_id=fueltech_id,
        facility_codes=facility_codes,
        network_region=network_region,
    )

    query_clear = get_clear_query(network_region, date_min, date_max, network, fueltech_id)

    engine = get_database_engine()

    results = []

    with engine.connect() as c:
        if run_clear:
            logger.debug(query_clear)
            c.execute(query_clear)

        logger.debug(query)

        if not DRY_RUN:
            try:
                results = list(c.execute(query))
            except Exception as e:
                logger.error(e)

    logger.debug(f"Got back {len(results)} rows")

    return results


def get_flows(
    date_min: datetime,
    date_max: datetime,
    network_region: str,
    network: NetworkSchema,
    flow: FlowDirection,
) -> list[dict]:
    """Gets flows"""

    query = get_flows_query(network_region, date_min, date_max, network, flow)

    engine = get_database_engine()

    results = []

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            try:
                results = list(c.execute(query))
            except Exception as e:
                logger.error(e)

    logger.debug(f"Got back {len(results)} flow rows")

    return results


def insert_energies(results: list[dict], network: NetworkSchema) -> int:
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
    esdf["energy_quality_flag"] = 0

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
        "energy_quality_flag",
    ]
    esdf = esdf[columns]

    records_to_store: list[dict] = esdf.to_dict("records")

    for record in records_to_store[:5]:
        logger.debug(record)

    if len(records_to_store) < 1:
        logger.warning("No records returned from energy sum")
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
        column_names=list(records_to_store[0].keys()),
    )

    try:
        cursor.copy_expert(sql_query, csv_content)
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting records: {e}")
        return 0

    logger.info(f"Inserted {len(records_to_store)} records")

    return len(records_to_store)


def get_date_range(network: NetworkSchema) -> ExportDatetimeRange:
    date_range = get_scada_range(network=NetworkNEM)

    time_series = OpennemExportSeries(
        start=date_range.start,
        end=date_range.end,
        interval=human_to_interval("1d"),
        period=human_to_period("all"),
        network=network,
    )

    return time_series.get_range()


def run_energy_calc(
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    region: str | None = None,
    fueltech_id: str | None = None,
    facility_codes: list[str] | None = None,
    run_clear: bool = False,
) -> int:
    """Runs the actual energy calc - believe it or not"""

    logger.info(
        f"Running energy calc for {network.code} region {region} fueltech {fueltech_id} and range {date_min} => {date_max}"
    )

    if settings.dry_run:
        return 0

    generated_results: list[dict] = []

    flow = None

    if fueltech_id:
        flow = fueltech_to_flow(fueltech_id)

    # @TODO get rid of the hard-coded networknem part
    if flow and region and network == NetworkNEM:
        generated_results = get_flows(date_min, date_max, network_region=region, network=network, flow=flow)
    else:
        generated_results = get_generated(
            date_min,
            date_max,
            network_region=region,
            network=network,
            fueltech_id=fueltech_id,
            run_clear=run_clear,
            facility_codes=facility_codes,
        )

    num_records = 0

    try:
        if len(generated_results) < 1:
            logger.warning(f"No results from get_generated query for {region} {date_max} {fueltech_id}")
            return 0

        generated_frame = shape_energy_dataframe(generated_results, network=network)

        num_records = insert_energies(generated_frame, network=network)

        logger.info(f"Done {region} for {date_min} => {date_max}")
    except Exception as e:
        error_traceback = e.with_traceback()

        if error_traceback:
            logger.error(error_traceback)
        else:
            logger.error(e)

    return num_records


def run_energy_update_archive(
    year: int | None = None,
    months: list[int] | None = None,
    days: int | None = None,
    regions: list[str] | None = None,
    fueltech: str | None = None,
    network: NetworkSchema = NetworkNEM,
    run_clear: bool = False,
) -> None:
    date_range = get_date_range(network=network)

    years: list[int] = []

    if not year:
        years = [i for i in range(YEAR_EARLIEST, DATE_CURRENT_YEAR + 1)]
    else:
        years = [year]

    if not months:
        months = list(range(1, 13))

    if not regions:
        regions = ["NSW1", "QLD1", "VIC1", "TAS1", "SA1"]

    # @TODO remove this and give APVI regions
    if network == NetworkAPVI:
        regions = ["WEM"]

    # list of fueltech codes to run
    fueltechs: list[str] = []

    if fueltech:
        fueltechs = [fueltech]
    elif network.fueltechs:
        fueltechs = network.fueltechs
    else:
        fueltechs = ALL_FUELTECH_CODES

    EXCLUDED_FUELTECHS_FROM_ENERGY = ["imports", "exports", "interconnector", "nuclear"]

    for excluded_fueltech_id in EXCLUDED_FUELTECHS_FROM_ENERGY:
        try:
            fueltechs.remove(excluded_fueltech_id)
        except ValueError:
            pass

    for y in years:
        for month in months:
            date_min = datetime(
                year=y,
                month=month,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=NetworkWEM.get_timezone(),
            )

            date_max = date_min + get_human_interval("1M")

            if days:
                date_max = datetime(
                    year=y,
                    month=month,
                    day=1 + days,
                    hour=0,
                    minute=0,
                    second=0,
                    tzinfo=NetworkWEM.get_timezone(),
                )

            date_min = date_min - timedelta(minutes=10)
            date_max = date_max + timedelta(minutes=10)

            if date_max > date_range.end:
                date_max = date_range.end

            if date_min > date_max:
                logger.debug(f"Reached end of archive {date_min} {date_max}")
                break

            for region in regions:
                for fueltech_id in fueltechs:
                    run_energy_calc(
                        date_min,
                        date_max,
                        region=region,
                        fueltech_id=fueltech_id,
                        network=network,
                        run_clear=run_clear,
                    )


def run_energy_update_days(
    networks: list[NetworkSchema] | None = None,
    days: int = 1,
    fueltech: str = None,
    region: str = None,
) -> None:
    """Run energy sum update for yesterday. This task is scheduled
    in scheduler/db"""

    if not networks:
        networks = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop]

    for network in networks:
        # This is Sydney time as the data is published in local time
        today_midnight = get_last_complete_day_for_network(network)

        date_max = today_midnight
        date_min = today_midnight - timedelta(days=days)

        regions = [i.code for i in get_network_regions(network)]

        if region:
            regions = [region.upper()]

        if network == NetworkAPVI:
            regions = ["WEM"]

        for ri in regions:
            run_energy_calc(
                date_min,
                date_max,
                network=network,
                fueltech_id=fueltech,
                run_clear=False,
                region=ri,
            )


def run_energy_update_all(network: NetworkSchema = NetworkNEM, fueltech: str | None = None, run_clear: bool = False) -> None:
    """Runs energy update for all regions and all years for one-off
    inserts"""
    if not network.data_first_seen:
        raise Exception(f"Require a data_first_seen attribute for network {network.code}")

    for year in range(DATE_CURRENT_YEAR, network.data_first_seen.year, -1):
        run_energy_update_archive(year=year, fueltech=fueltech, network=network, run_clear=run_clear)


def run_energy_update_facility(facility_codes: list[str], network: NetworkSchema = NetworkNEM) -> None:
    facility_seen_range = None

    # catch me if you can
    facility_seen_range = get_facility_seen_range(facility_codes)

    if not facility_seen_range or not facility_seen_range.date_max or not facility_seen_range.date_min:
        raise Exception("run_energy_update_facility requires a facility seen range")

    run_energy_calc(
        facility_seen_range.date_min,
        facility_seen_range.date_max,
        facility_codes=facility_codes,
        network=network,
    )


def _test_case() -> None:
    """Run a test case so we can attach debugger"""
    run_energy_calc(
        date_min=datetime.fromisoformat("2020-12-31 23:50:00+10:00"),
        date_max=datetime.fromisoformat("2021-02-01 00:10:00+10:00"),
        network=NetworkNEM,
        region="NSW1",
        fueltech_id="coal_black",
    )


def run_energy_worker_for_year(year: int) -> None:
    date_min = datetime.fromisoformat(f"{year}-01-01T00:00:00+10:00")
    date_max = date_min + timedelta(days=1)

    while True:
        logger.info(f"Running for {date_min} => {date_max}")

        if date_max > datetime.fromisoformat(f"{year + 1}-01-01T00:00:00+10:00"):
            logger.info("Done")
            break

        run_energy_calc(
            date_min,
            date_max,
            network=NetworkNEM,
            run_clear=False,
        )

        date_min += timedelta(days=1)
        date_max += timedelta(days=1)


# debug entry point
if __name__ == "__main__":
    run_energy_update_all(network=NetworkNEM)
