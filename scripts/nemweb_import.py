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
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from pydantic import validator
from sqlalchemy.engine.base import Engine

from opennem.core.normalizers import clean_float, normalize_aemo_region
from opennem.db import db_connect, get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.schema.core import BaseConfig
from opennem.settings import settings  # noqa: F401

logger = logging.getLogger("opennem.importer.nemweb")

# These are from min/max SETTLEMENTDATE on nemweb DISPATCH_UNIT_SOLUTION_OLD
NEMWEB_DISPATCH_OLD_MIN_DATE = datetime.fromisoformat("1998-12-07 01:40:00")
NEMWEB_DISPATCH_OLD_MAX_DATE = datetime.fromisoformat("2014-08-01 00:00:00")


# Defines a schema for return results from DISPATHC_UNIT_SOLUTION_OLD
class DispatchUnitSolutionOld(BaseConfig):
    created_by: str = "opennem.importer.nemweb"
    created_at: datetime = datetime.now()
    updated_at: Optional[str]
    network_id: str = "NEM"
    trading_interval: datetime
    facility_code: str
    generated: Optional[float]
    eoi_quantity: Optional[float]
    is_forecast: bool = False
    # energy_quality_flag:

    _normalize_network_id = validator("network_id", pre=True, allow_reuse=True)(
        normalize_aemo_region
    )
    _normalize_facility_code = validator("facility_code", pre=True, allow_reuse=True)(
        normalize_aemo_region
    )
    _normalize_generated = validator("generated", pre=True, allow_reuse=True)(clean_float)
    _normalize_energy = validator("eoi_quantity", pre=True, allow_reuse=True)(clean_float)


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


def insert_scada_records(records: List[DispatchUnitSolutionOld]) -> int:
    """ Bulk insert the scada records """

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
        logger.error("Error inserting records: {}".format(e))
        return 0

    logger.info("Inserted {} records".format(len(records_to_store)))

    return len(records_to_store)


def import_nemweb_scada() -> None:
    engine_mysql = get_mysql_engine()
    logger.info("Connected to database.")

    year = NEMWEB_DISPATCH_OLD_MIN_DATE.year
    month = NEMWEB_DISPATCH_OLD_MIN_DATE.month

    query = get_scada_old_query(year=year, month=month)

    with engine_mysql.connect() as c:
        logger.debug(query)

        results_raw = list(c.execute(query))

        logger.info("Got {} rows for year {} and month {}".format(len(results_raw), year, month))

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


if __name__ == "__main__":
    import_nemweb_scada()
