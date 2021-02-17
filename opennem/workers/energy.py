import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pytz import FixedOffset

from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.compat.energy import energy_sum_compat
from opennem.db import get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.notifications.slack import slack_message
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import NetworkNEM

logger = logging.getLogger("opennem.workers.energy")

DRY_RUN = False


def get_generated(
    network_region: str, date_min: datetime, date_max: datetime, fueltech_id: Optional[str] = None
) -> List[Dict]:
    __sql = """
    select
        fs.trading_interval at time zone 'AEST' as trading_interval,
        fs.facility_code,
        fs.network_id,
        generated
    from
        facility_scada fs
        left join facility f on fs.facility_code = f.code
    where
        fs.network_id='NEM'
        and f.network_region='{network_region}'
        and fs.trading_interval >= '{date_min}'
        and fs.trading_interval <= '{date_max}'
        and fs.is_forecast is False
        and f.fueltech_id not in ('solar_rooftop', 'imports', 'exports')
        and f.interconnector is False
        {fueltech_match}
    order by fs.trading_interval asc, 2;
    """

    fueltech_match = ""

    if fueltech_id:
        fueltech_match = f"and f.fueltech_id = '{fueltech_id}'"

    query = __sql.format(
        network_region=network_region,
        date_min=date_min,
        date_max=date_max,
        fueltech_match=fueltech_match,
    )

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


def insert_energies(results: List[Dict]) -> int:
    # Get the energy sums
    energy_sum = energy_sum_compat(results)

    # Add metadata
    energy_sum["created_by"] = "opennem.worker.energy"
    energy_sum["created_at"] = ""
    energy_sum["updated_at"] = datetime.now()
    energy_sum["generated"] = None
    energy_sum["is_forecast"] = False

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
    energy_sum = energy_sum[columns]

    records_to_store: List[Dict] = energy_sum.to_dict("records")

    # Build SQL + CSV and bulk-insert
    sql_query = build_insert_query(FacilityScada, ["updated_at", "eoi_quantity"])
    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()

    csv_content = generate_csv_from_records(
        FacilityScada,
        records_to_store,
        column_names=records_to_store[0].keys(),
    )

    cursor.copy_expert(sql_query, csv_content)
    conn.commit()

    logger.info("Inserted {} records".format(len(records_to_store)))

    return len(records_to_store)


def get_date_range() -> DatetimeRange:
    date_range = get_scada_range(network=NetworkNEM)

    time_series = TimeSeries(
        start=date_range.start,
        end=date_range.end,
        interval=human_to_interval("1d"),
        period=human_to_period("all"),
        network=NetworkNEM,
    )

    return time_series.get_range()


def run_energy_calc(
    region: str, date_min: datetime, date_max: datetime, fueltech_id: Optional[str] = None
) -> int:
    results = get_generated(region, date_min, date_max, fueltech_id)
    num_records = 0

    try:
        if len(results) < 1:
            raise Exception("No results from get_generated query")

        num_records = insert_energies(results)
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
    fueltech_id: Optional[str] = None,
) -> None:
    date_range = get_date_range()

    if not months:
        months = list(range(1, 12))

    if not regions:
        regions = ["QLD1", "NSW1", "VIC1", "TAS1", "SA1"]

    for month in months:
        date_min = datetime(
            year=year, month=month, day=1, hour=0, minute=0, second=0, tzinfo=FixedOffset(600)
        )

        date_max = datetime(
            year=year,
            month=month + 1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            tzinfo=FixedOffset(600),
        )

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

        date_max = date_max + timedelta(minutes=5)

        if date_max > date_range.end:
            date_max = date_range.end

        if date_min > date_max:
            slack_message("Reached end of energy archive")
            logger.debug("reached end of archive")
            break

        for region in regions:
            run_energy_calc(region, date_min, date_max, fueltech_id)


def run_energy_update() -> None:
    for region in ["QLD1", "NSW1", "VIC1", "TAS1", "SA1"]:
        now = datetime.now().replace(tzinfo=FixedOffset(600))
        date_min = now.replace(hour=0, minute=0, second=0)
        date_max = date_min + timedelta(days=1, minutes=5)

        results = get_generated(region, date_min, date_max)

        try:
            insert_energies(results)
        except Exception as e:
            logger.error(e)
            slack_message("Energy archive error: {}".format(e))


if __name__ == "__main__":
    run_energy_update_archive(year=2020)
    run_energy_update_archive(year=2019)
    run_energy_update_archive(year=2018)
    run_energy_update_archive(year=2017)
    run_energy_update_archive(year=2016)
