#!/usr/bin/env python
""" Loads historic dispatch_regionsum data from AEMO's MMS service.
for the intervals from:


"""
import csv
import logging
from pathlib import Path
from typing import Any

from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import AEMOTableSchema, AEMOTableSet

logger = logging.getLogger("opennem.load_historic_dispatch_regionsum")


def import_dispatch_regionsum() -> None:
    """Reads the historic dispatch_regionsum data from a local CSV and stores
    it in the database."""

    source_path = Path(__file__).parent.parent / "data" / "historical-dispatch-regionsum.csv"

    if not source_path.exists():
        raise Exception(f"Not a path: {source_path}")

    with source_path.open("r") as fh:
        reader = csv.DictReader(fh)
        records: list[dict[str, Any]] = list(reader)

    # NEM processors expect lowercase fieldnames
    # @NOTE we should probably change that
    formatted_records = [{k.lower(): v for k, v in i.items()} for i in records]

    logger.info(f"Got {len(records)} records")

    fieldnames = [i.lower() for i in list(records[0].keys())]

    logger.info(formatted_records[0])

    table = AEMOTableSchema(name="REGIONSUM", namespace="DISPATCH", fieldnames=fieldnames, records=formatted_records)

    logger.info(f"Schema has {len(table.records)} records")

    ts = AEMOTableSet(tables=[table])

    rs = store_aemo_tableset(ts)

    if not rs:
        raise Exception("Insert error")
    logger.info(f"Stored {len(rs.inserted_records)} records")


if __name__ == "__main__":
    import_dispatch_regionsum()
