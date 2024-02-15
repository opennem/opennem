"""
OpenNEM API Reactor Initial State Records

Generates records for the OpenNEM API Reactor Backfill project and will
run queries for all records back to a date defined as a parameter.


"""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones, MilestoneType

logger = logging.getLogger("opennem.recordreactor.initstate")

BACKFILL_FILE_PATH = Path(__file__).parent / "state" / "power.csv"


class ReactorBackfillRecord(BaseModel):
    network_id: str
    network_region: str | None = None
    fueltech_id: str
    fueltech_label: str
    highest_output: float | int | None = None
    lowest_output: float | int | None = None
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


def get_aware_interval_for_record(record: ReactorBackfillRecord, record_type: MilestoneType) -> datetime:
    """Get an aware interval for a record"""
    milestone_type_attribute = "highest_output_interval" if record_type == MilestoneType.high else "lowest_output_interval"

    if not hasattr(record, milestone_type_attribute):
        raise Exception(f"Record does not have attribute {milestone_type_attribute}")

    if record.network_id != "WEM":
        interval = getattr(record, milestone_type_attribute).astimezone(ZoneInfo("Australia/Sydney"))
        interval += timedelta(hours=10)
    else:
        interval = getattr(record, milestone_type_attribute).astimezone(ZoneInfo("Australia/Perth"))
        interval += timedelta(hours=8)

    return interval


def backfill_records_to_milestones(backfill_records: list[ReactorBackfillRecord]) -> list[Milestones]:
    """Converts backfill records to milestones"""

    milestones: list[Milestones] = []

    for record in backfill_records:
        if record.highest_output:
            record_id = f"{record.network_id}.{record.network_region}.{record.fueltech_id}.high".lower()

            if not record.highest_output_interval:
                continue

            interval = get_aware_interval_for_record(record, MilestoneType.high)

            milestones.append(
                Milestones(
                    record_id=record_id,
                    interval=interval,
                    record_type=MilestoneType.high,
                    significance=8,
                    value=record.highest_output,
                    network_id=record.network_id,
                    network_region=record.network_region,
                    fueltech_group_id=record.fueltech_id,
                )  #  type: ignore
            )

        if record.lowest_output:
            record_id = f"{record.network_id}.{record.network_region}.{record.fueltech_id}.low".lower()

            if not record.lowest_output_interval:
                continue

            interval = get_aware_interval_for_record(record, MilestoneType.low)

            milestones.append(
                Milestones(
                    record_id=record_id,
                    interval=interval,
                    record_type=MilestoneType.low,
                    significance=1,
                    value=record.highest_output,
                    network_id=record.network_id,
                    network_region=record.network_region,
                    fueltech_group_id=record.fueltech_id,
                )  #  type: ignore
            )

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
