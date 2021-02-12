import logging
from datetime import datetime, timedelta
from typing import Dict, List

from pytz import FixedOffset

from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.compat.energy import energy_sum_compat
from opennem.db import get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.db.tasks import refresh_timescale_views
from opennem.notifications.slack import slack_message
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import NetworkNEM

logger = logging.getLogger(__name__)


def get_generated(network_region: str, date_min: datetime, date_max: datetime) -> List[Dict]:
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
    order by fs.trading_interval asc;
    """

    query = __sql.format(network_region=network_region, date_min=date_min, date_max=date_max)

    engine = get_database_engine()

    results = []

    with engine.connect() as c:
        logger.debug(query)
        results = list(c.execute(query))

    logger.debug("Got back {} rows".format(len(results)))

    return results


def insert_energies(results: List[Dict]) -> None:
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


def run_energy_update_archive() -> None:
    date_range = get_date_range()

    for year in [2020, 2021, 2019, 2018, 2017, 2016]:
        for month in range(1, 12):
            date_min = datetime(
                year=year, month=month, day=1, hour=0, minute=0, second=0, tzinfo=FixedOffset(600)
            ) - timedelta(minutes=5)
            date_max = datetime(
                year=year,
                month=month + 1,
                day=1,
                hour=0,
                minute=5,
                second=0,
                tzinfo=FixedOffset(600),
            )

            if date_max > date_range.end:
                date_max = date_range.end

            if date_min > date_max:
                slack_message("Reached end of energy archive")
                logger.debug("reached end of archive")
                break

            logger.debug("{} => {}".format(date_min, date_max))

            for region in ["QLD1", "NSW1", "VIC1", "TAS1", "SA1"]:
                results = get_generated(region, date_min, date_max)

                try:
                    insert_energies(results)
                except Exception as e:
                    logger.error(e)
                    slack_message("Energy archive error: {}".format(e))

        refresh_timescale_views()
        slack_message("Updated energies for {}".format(year))


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
    run_energy_update_archive()
    refresh_timescale_views()
    # run_energy_update()
