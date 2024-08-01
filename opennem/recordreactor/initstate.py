"""
OpenNEM API Reactor Initial State Records

Generates records for the OpenNEM API Reactor Backfill project and will
run queries for all records back to a date defined as a parameter.


"""

import csv
import logging
from datetime import datetime
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
        interval = getattr(record, milestone_type_attribute).astimezone(ZoneInfo("Australia/Brisbane"))
        # interval += timedelta(hours=10)
    else:
        interval = getattr(record, milestone_type_attribute).astimezone(ZoneInfo("Australia/Perth"))
        # interval += timedelta(hours=8)

    return interval


def get_network_id_map(network_id: str) -> str:
    """Get a network id map"""
    network_id_map = {
        "AEMO_ROOFTOP": "NEM",
        "APVI": "WEM",
    }

    if network_id not in network_id_map:
        return network_id

    return network_id_map[network_id]


def get_record_id(
    record: ReactorBackfillRecord,
    network_id: str,
    record_type: MilestoneType,
    record_unit: str | None = None,
    record_period: str | None = None,
) -> str:
    """Get a record id"""
    record_id_components = [
        "ms",
        network_id,
        record.network_region,
        record.fueltech_id,
        record_unit,
        record_period,
        record_type.value,
    ]

    # remove empty items from record id components list and join with a period
    record_id = ".".join(filter(None, record_id_components)).lower()

    return record_id


def get_record_description(
    record: ReactorBackfillRecord,
    network_id: str,
    record_type: MilestoneType,
    record_unit: str | None = None,
    record_period: str | None = None,
) -> str:
    """get a record description"""
    record_description_components = [
        f"{record_type.value.capitalize()} MW" if record_type else None,
        f"{record_unit}" if record_unit else None,
        f"for {record.fueltech_label}" if record.fueltech_label else None,
        record_period.lower() if record_period else None,
        "record for",
        network_id,
        f"in {record.network_region}" if record.network_region else None,
    ]

    # remove empty items from record id components list and join with a period
    record_description = " ".join(filter(None, record_description_components))

    return record_description


def backfill_records_to_milestones(backfill_records: list[ReactorBackfillRecord]) -> list[Milestones]:
    """Converts backfill records to milestones"""

    milestones: list[Milestones] = []

    for record in backfill_records:
        if record.network_region:
            if record.network_region.lower() == record.network_id.lower():
                record.network_region = None

        network_id = get_network_id_map(record.network_id)

        if record.highest_output:
            record_id = get_record_id(
                record=record, network_id=network_id, record_type=MilestoneType.high, record_unit="power", record_period="all"
            )

            description = get_record_description(
                record=record, network_id=network_id, record_type=MilestoneType.high, record_unit="power", record_period="all"
            )

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
                    network_id=network_id,
                    network_region=record.network_region,
                    fueltech_group_id=record.fueltech_id,
                    period="all",
                    description=description,
                )  #  type: ignore
            )

        if record.lowest_output:
            record_id = get_record_id(
                record=record, network_id=network_id, record_type=MilestoneType.low, record_unit="power", record_period="all"
            )

            description = get_record_description(
                record=record, network_id=network_id, record_type=MilestoneType.low, record_unit="power", record_period="all"
            )

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
                    network_id=network_id,
                    network_region=record.network_region,
                    fueltech_group_id=record.fueltech_id,
                    period="all",
                    description=description,
                )  #  type: ignore
            )

    return milestones


async def backfill_from_csv() -> None:
    logger.info("OpenNEM API Reactor Backfill")
    logger.info("Generating records for all facilities")

    # load from backfill file
    backfill_records = load_backfill_from_file(BACKFILL_FILE_PATH)
    milestone_records = backfill_records_to_milestones(backfill_records)

    async with SessionLocal() as session:
        for record in milestone_records:
            try:
                session.add(record)
                await session.commit()
            except Exception as e:
                logger.error(f"Error adding record: {e}")
                session.rollback()


if __name__ == "__main__":
    import asyncio

    asyncio.run(backfill_from_csv())
