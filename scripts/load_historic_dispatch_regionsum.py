#!/usr/bin/env python
""" Loads historic dispatch_regionsum data from AEMO's MMS service.
for the intervals from:


"""
import csv
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary
from opennem.utils.dates import get_today_nem, parse_date

logger = logging.getLogger("opennem.load_historic_dispatch_regionsum")


def persist_disaptch_regionsum(records: list[dict[str, Any]]) -> None:
    """Takes a lits of records and persists them to the database"""
    primary_keys = []
    records_to_store = []

    created_at = get_today_nem()

    for record in records:
        if not isinstance(record, dict):
            continue

        trading_interval = parse_date(record.get("SETTLEMENTDATE"))

        primary_key = {trading_interval, record["REGIONID"]}

        if primary_key in primary_keys:
            continue

        primary_keys.append(primary_key)

        if "DEMAND_AND_NONSCHEDGEN" not in record:
            raise Exception("bad value in dispatch_regionsum")

        records_to_store.append(
            {
                "created_by": "opennem.loader.dispatch_regionsum",
                "created_at": created_at,
                "updated_at": None,
                "network_id": "NEM",
                "trading_interval": trading_interval,
                "forecast_load": None,
                "generation_scheduled": None,
                "generation_non_scheduled": None,
                "generation_total": None,
                "price": None,
                "network_region": record["REGIONID"],
                "is_forecast": False,
                "net_interchange": record["NETINTERCHANGE"],
                "demand_total": record["DEMAND_AND_NONSCHEDGEN"],
                "price_dispatch": None,
                "net_interchange_trading": None,
                "demand": record["TOTALDEMAND"],
            }
        )

    bulkinsert_mms_items(BalancingSummary, records_to_store, ["net_interchange", "demand", "demand_total"])  # type: ignore

    return None


def gen_chunks(reader: csv.DictReader, chunksize: int = 10000) -> Iterable[list[dict[str, Any]]]:
    """
    Chunk generator. Take a CSV `reader` and yield
    `chunksize` sized slices.
    """
    chunk: list[dict[str, Any]] = []
    for index, line in enumerate(reader, 0):
        if index % chunksize == 0 and index > 0:
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield chunk


def import_dispatch_regionsum() -> None:
    """Reads the historic dispatch_regionsum data from a local CSV and stores
    it in the database."""

    source_path = Path(__file__).parent.parent / "data" / "historical-dispatch-regionsum.csv"

    if not source_path.exists():
        raise Exception(f"Not a path: {source_path}")

    records: list[dict[str, Any]] = []

    with source_path.open("r") as fh:
        reader = csv.DictReader(fh)

        for chunk in gen_chunks(reader=reader, chunksize=50000):
            records.extend(chunk)
            logger.info(f"Got {len(records)} records")
            persist_disaptch_regionsum(records)
            records = []


if __name__ == "__main__":
    import_dispatch_regionsum()
