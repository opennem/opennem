"""
OpenNEM API Reactor Backfill Records

Generates records for the OpenNEM API Reactor Backfill project and will
run queries for all records back to a date defined as a parameter.

For testing on dev we run back ~6 months.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones, MilestoneType

logger = logging.getLogger("opennem.recordreactor.backfill")

BACKFILL_FILE_PATH = Path(__file__).parent / "backfill.csv"


class ReactorBackfillRecord(BaseModel):
    network_id: str
    network_region: str | None = None
    fueltech_id: str
    fueltech_label: str
    highest_output: float | int | None
    lowest_output: float | int | None
    highest_output_interval: datetime | None = None
    lowest_output_interval: datetime | None = None


def load_backfill_from_file(file_path: Path) -> list[ReactorBackfillRecord]:
    """Load backfill records from a csv file at file_path and returns a list of records"""

    column_names: list[str] = [
        "network_id",
        "network_region",
        "fueltech_id",
        "fueltech_label",
        "highest_output",
        "lowest_output",
        "highest_output_interval",
        "lowest_output_interval",
    ]

    models: list[ReactorBackfillRecord] = []

    with file_path.open() as fh:
        reader = csv.DictReader(fh, fieldnames=column_names)

        # skip header
        reader.__next__()

        for row in reader:
            if not row["highest_output_interval"]:
                del row["highest_output_interval"]

            if not row["lowest_output_interval"]:
                del row["lowest_output_interval"]

            try:
                model = ReactorBackfillRecord(**row)
            except Exception as e:
                logger.error(f"Error parsing row: {row}")
                raise e

            models.append(model)

    return models


def backfill_records_to_milestones(backfill_records: list[ReactorBackfillRecord]) -> list[Milestones]:
    """Converts backfill records to milestones"""

    milestones: list[Milestones] = []

    for record in backfill_records:
        if record.highest_output:
            record_id = f"{record.network_id}.{record.network_region}.{record.fueltech_id}.high"

            if not record.highest_output_interval:
                continue

            milestones.append(
                Milestones(
                    record_id=record_id,
                    dtime=record.highest_output_interval,
                    record_type=MilestoneType.high,
                    significance=1,
                    value=record.highest_output,
                    network_id=record.network_id,
                    network_region=record.network_region,
                    fueltech_group_id=record.fueltech_id,
                )  #  type: ignore
            )

        if record.lowest_output:
            record_id = f"{record.network_id}.{record.network_region}.{record.fueltech_id}.low"

            if not record.lowest_output_interval:
                continue

    return milestones


if __name__ == "__main__":
    logger.info("OpenNEM API Reactor Backfill")
    logger.info("Generating records for all facilities")

    # load from backfill file
    backfill_records = load_backfill_from_file(BACKFILL_FILE_PATH)
    milestone_records = backfill_records_to_milestones(backfill_records)

    with SessionLocal() as session:
        for record in milestone_records:
            logger.info(record)
            session.add(record)

        session.commit()
