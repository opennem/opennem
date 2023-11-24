#!/usr/bin/env python
"""
Import nemweb data from v2 mysql instance

run as ./scripts/nemweb_import.py --help
"""
import logging
import os
from datetime import datetime
from itertools import groupby
from textwrap import dedent

from datetime_truncate import truncate as date_trunc
from dateutil.relativedelta import relativedelta
from pydantic import validator
from sqlalchemy.engine.base import Engine

from opennem import settings  # noqa: F401
from opennem.core.normalizers import clean_float, string_to_upper
from opennem.db import db_connect, get_database_engine
from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records  # type: ignore
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import date_series

logger = logging.getLogger("opennem.importer.nemweb")

# These are from min/max SETTLEMENTDATE on nemweb DISPATCH_UNIT_SOLUTION_OLD
NEMWEB_DISPATCH_OLD_MIN_DATE = datetime.fromisoformat("1998-12-07 01:40:00")
NEMWEB_DISPATCH_OLD_MAX_DATE = datetime.fromisoformat("2009-08-01 00:00:00")
# NEMWEB_DISPATCH_OLD_MAX_DATE = datetime.fromisoformat("2014-08-01 00:00:00")

# TRADING_PRICE min date (going back from)
NEMWEB_TRADING_PRICE_MIN_DATE = datetime.fromisoformat("2009-07-01 00:00:00")


def _trading_interval_timezone(dt: datetime) -> datetime:
    return dt.replace(tzinfo=NetworkNEM.get_timezone())  # type: ignore


# Defines a schema for return results from DISPATHC_UNIT_SOLUTION_OLD
class DispatchUnitSolutionOld(BaseConfig):
    created_by: str = "opennem.importer.nemweb"
    created_at: datetime = datetime.now()
    updated_at: str | None
    network_id: str = "NEM"
    trading_interval: datetime
    facility_code: str
    generated: float | None
    eoi_quantity: float | None
    is_forecast: bool = False
    energy_quality_flag: int = 0

    _trading_interval_timezone = validator("trading_interval", pre=True, allow_reuse=True)(_trading_interval_timezone)

    _normalize_network_id = validator("network_id", pre=True, allow_reuse=True)(string_to_upper)
    _normalize_facility_code = validator("facility_code", pre=True, allow_reuse=True)(string_to_upper)
    _normalize_generated = validator("generated", pre=True, allow_reuse=True)(clean_float)
    _normalize_energy = validator("eoi_quantity", pre=True, allow_reuse=True)(clean_float)


class BalancingSummaryImport(BaseConfig):
    created_by: str = "opennem.importer.nemweb"
    created_at: datetime = datetime.now()
    updated_at: str | None
    network_id: str = "NEM"
    trading_interval: datetime
    forecast_load: float | None
    generation_scheduled: float | None
    generation_non_scheduled: float | None
    generation_total: float | None
    price: float | None
    network_region: str
    is_forecast: bool = False
    net_interchange: float | None
    demand_total: float | None
    price_dispatch: float | None
    net_interchange_trading: float | None

    _trading_interval_timezone = validator("trading_interval", pre=True, allow_reuse=True)(_trading_interval_timezone)
    _normalize_price = validator("price", pre=True, allow_reuse=True)(clean_float)
    _normalize_net_interchange = validator("net_interchange", pre=True, allow_reuse=True)(clean_float)
    _normalize_net_interchange_trading = validator("net_interchange_trading", pre=True, allow_reuse=True)(clean_float)
    _normalize_demand_total = validator("demand_total", pre=True, allow_reuse=True)(clean_float)


def get_mysql_engine() -> Engine:
    """Get a database connection to the mysql database, requires mysqlclient

    $ pip install mysqlclient

    and a connection string with the driver set as:

    ```mysql+pymysql://```
    """
    dbconnstr = os.environ.get("NEMWEB_MIGRATE_DB")

    if not dbconnstr:
        raise Exception("Require a db connection string set at NEMWEB_MIGRATE_DB")

    engine = db_connect(db_conn_str=dbconnstr)

    return engine


def get_scada_old_query(year: int, month: int) -> str:
    """Join DISPATCH_UNIT_SOLUTION_OLD with duid data broken down in chunks
    of a month

    Limit is used in dev to save query time
    """

    #
    __query = """
    select
        duso.SETTLEMENTDATE,
        d.DUID,
        duso.INITIALMW
    from DISPATCH_UNIT_SOLUTION_OLD duso
    left join DUID d on duso.DUID = d.ID
    where duso.SETTLEMENTDATE between '{date_min}' and '{date_max}'
    order by duso.SETTLEMENTDATE asc;
    """

    # One month blocks
    date_min = datetime(year, month, 1)
    date_max = date_min + relativedelta(months=1)

    query = __query.format(date_min=date_min, date_max=date_max)

    return dedent(query)


def get_trading_price_import_query(limit: int | None = None) -> str:
    """Join TRADING_PRICE with regionids and return from min date

    @NOTE all of these SETTLEMENTDATES come back in UTC+10 with no tzinfo
    """

    __query = """
    select
        tp.SETTLEMENTDATE,
        tp.RRP,
        ri.REGIONID
    from TRADING_PRICE tp
    left join REGIONID ri on ri.id = tp.REGIONID
    where tp.SETTLEMENTDATE  < '{date_min}'
    order by tp.SETTLEMENTDATE desc
    {limit_query}
    """

    limit_query = f"limit {limit}" if limit else ""

    query = __query.format(date_min=NEMWEB_TRADING_PRICE_MIN_DATE, limit_query=limit_query)

    return dedent(query)


def get_regionsum_import_query(limit: int | None = None) -> str:
    __query = """
    select
        trs.SETTLEMENTDATE,
        ri.REGIONID,
        trs.TOTALDEMAND,
        trs.NETINTERCHANGE
    from TRADING_REGIONSUM trs
    left join REGIONID ri on ri.id = trs.REGIONID
    where trs.SETTLEMENTDATE  < '{date_min}'
    order by trs.SETTLEMENTDATE desc
    {limit_query}
    """

    limit_query = f"limit {limit}" if limit else ""

    query = __query.format(date_min=NEMWEB_TRADING_PRICE_MIN_DATE, limit_query=limit_query)

    return dedent(query)


def insert_scada_records(records: list[DispatchUnitSolutionOld]) -> int:
    """Bulk insert the scada records"""

    records_to_store = [i.dict() for i in records]

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

    sql_query = build_insert_query(FacilityScada, ["updated_at", "generated"])
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
        logger.error(f"Error inserting records: {e}")
        return 0

    logger.info(f"Inserted {len(records_to_store)} records")

    return len(records_to_store)


def insert_balancing_summary_records(records: list[BalancingSummaryImport], update_fields: list[str] = ["price"]) -> int:
    """Bulk insert the balancing_summary records"""

    records_to_store = [i.dict() for i in records]

    # dedupe records
    return_records_grouped = {}

    # primary key protection for bulk insert
    for pk_values, rec_value in groupby(
        records_to_store,
        key=lambda r: (
            r.get("trading_interval"),
            r.get("network_id"),
            r.get("network_region"),
        ),
    ):
        if pk_values not in return_records_grouped:
            return_records_grouped[pk_values] = list(rec_value).pop()

    records_to_store = list(return_records_grouped.values())

    sql_query = build_insert_query(BalancingSummary, ["updated_at"] + update_fields)
    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()

    csv_content = generate_csv_from_records(
        BalancingSummary,
        records_to_store,
        column_names=records_to_store[0].keys(),
    )

    try:
        cursor.copy_expert(sql_query, csv_content)
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting records: {e}")
        return 0

    logger.info(f"Inserted {len(records_to_store)} records")

    return len(records_to_store)


def import_nemweb_scada() -> None:
    engine_mysql = get_mysql_engine()
    logger.info("Connected to database.")

    year = NEMWEB_DISPATCH_OLD_MIN_DATE.year
    month = NEMWEB_DISPATCH_OLD_MIN_DATE.month

    for dt in date_series(
        date_trunc(NEMWEB_DISPATCH_OLD_MAX_DATE, "month"),
        date_trunc(NEMWEB_DISPATCH_OLD_MIN_DATE, "month"),
        interval=relativedelta(months=1),
        reverse=True,
    ):
        query = get_scada_old_query(year=dt.year, month=dt.month)

        with engine_mysql.connect() as c:
            logger.debug(query)

            results_raw = list(c.execute(query))

            logger.info(f"Got {len(results_raw)} rows for year {year} and month {month}")

        results_schema = [
            DispatchUnitSolutionOld(
                trading_interval=i[0],
                facility_code=i[1],
                generated=i[2],
            )
            for i in results_raw
        ]

        insert_scada_records(results_schema)

    return None


def import_nemweb_price() -> None:
    engine_mysql = get_mysql_engine()
    logger.info("Connected to database.")

    query = get_trading_price_import_query()

    with engine_mysql.connect() as c:
        logger.debug(query)

        results_raw = list(c.execute(query))

        logger.info(f"Got {len(results_raw)} rows from TRADING_PRICE")

        results_schema = [
            BalancingSummaryImport(
                trading_interval=i[0],
                price=i[1],
                network_region=i[2],
            )
            for i in results_raw
        ]

        insert_balancing_summary_records(results_schema)


def import_nemweb_regionsum() -> None:
    engine_mysql = get_mysql_engine()
    logger.info("Connected to database.")

    query = get_regionsum_import_query()

    with engine_mysql.connect() as c:
        logger.debug(query)

        results_raw = list(c.execute(query))

        logger.info(f"Got {len(results_raw)} rows from REGIONSUM")

        results_schema = [
            BalancingSummaryImport(
                trading_interval=i[0],
                network_region=i[1],
                demand_total=i[2],
                net_interchange=i[3],
            )
            for i in results_raw
        ]

        insert_balancing_summary_records(results_schema, ["demand_total", "net_interchange"])


if __name__ == "__main__":
    import_nemweb_regionsum()
