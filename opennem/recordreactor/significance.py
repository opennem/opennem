"""
Descriptions related methods for all Milestones

"""

import logging
from enum import Enum

from pydantic import UUID4
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from opennem.api.milestones.queries import get_milestone_record
from opennem.db import get_write_session
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.controllers import map_milestone_output_records_from_db, map_milestone_output_schema_to_record
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.schema.network import NetworkNEM

logger = logging.getLogger("opennem.recordreactor.significance")


class MilestoneSignificanceWeights(Enum):
    PERIOD = 0.3
    METRIC = 0.25
    NETWORK = 0.1
    NETWORK_REGION = 0.15
    FUELTECH = 0.1
    AGGREGATE = 0.1


def calculate_milestone_significance(milestone: MilestoneRecordSchema) -> int:
    """Calculate the significance of a milestone"""

    # hacky manual significance for launch
    # each one of these has a significance of 10 for network wide and 9 for regional
    # *.[solar|wind|renewables|battery_discharging].[power.interval|energy.day].high
    # *.[fossil|coal|gas].[power.interval|energy.day].low
    # *.demand.[power.interval|energy.day].high
    # *.renewables.proportion.[interval|day|7d].high

    if milestone.metric in [MilestoneType.power, MilestoneType.energy] and milestone.period in [
        MilestonePeriod.interval,
        MilestonePeriod.day,
        MilestonePeriod.quarter,
        MilestonePeriod.year,
    ]:
        if (
            milestone.fueltech in ["solar", "wind", "renewables", "battery_discharging", "battery_charging"]
            and milestone.aggregate == MilestoneAggregate.high
        ):
            if milestone.network_region is None:
                return 10
            else:
                return 9  # @NOTE temporary

        if milestone.fueltech in ["fossil", "coal", "gas"] and milestone.aggregate == MilestoneAggregate.low:
            if milestone.network_region is None:
                return 10
            else:
                return 9  # @NOTE temporary

    if milestone.fueltech == MilestoneFueltechGrouping.demand and milestone.period in [
        MilestonePeriod.interval,
        MilestonePeriod.day,
    ]:
        if milestone.aggregate == MilestoneAggregate.high:
            if milestone.network_region is None:
                return 10
            else:
                return 9  # @NOTE temporary

    if (
        milestone.metric == MilestoneType.proportion
        and milestone.period
        in [
            MilestonePeriod.interval,
            MilestonePeriod.day,
            MilestonePeriod.week,
            MilestonePeriod.week_rolling,
        ]
        and milestone.aggregate == MilestoneAggregate.high
    ):
        if milestone.network_region is None:
            return 10
        else:
            return 9  # @NOTE temporary

    # renewable emissions doesn't make sense as a record
    if milestone.fueltech == MilestoneFueltechGrouping.renewables and milestone.metric == MilestoneType.emissions:
        return 0

    # END HACKS

    # Period significance
    period_scores = {
        MilestonePeriod.interval: 1,
        MilestonePeriod.day: 9,
        MilestonePeriod.week: 2,
        MilestonePeriod.week_rolling: 2,
        MilestonePeriod.month: 9,
        MilestonePeriod.quarter: 5,
        MilestonePeriod.season: 5,
        MilestonePeriod.year: 10,
        MilestonePeriod.financial_year: 4,
    }
    period_score = period_scores[milestone.period] * MilestoneSignificanceWeights.PERIOD.value

    # Metric significance
    metric_scores = {
        MilestoneType.demand: 8,
        MilestoneType.price: 6,
        MilestoneType.power: 1,
        MilestoneType.energy: 9,
        MilestoneType.emissions: 9,
        MilestoneType.proportion: 10,
    }
    metric_score = metric_scores[milestone.metric] * MilestoneSignificanceWeights.METRIC.value

    # Network significance
    network_score = 10 if milestone.network == NetworkNEM else 5
    network_score *= MilestoneSignificanceWeights.NETWORK.value

    # Network region significance
    region_score = 10 if milestone.network_region is None else 5
    region_score *= MilestoneSignificanceWeights.NETWORK_REGION.value

    # Fueltech group significance
    fueltech_score = 0
    if milestone.fueltech:
        # if it's renewable
        if milestone.fueltech.value in [
            "solar",
            "wind",
            "hydro",
            "bioenergy",
            "pumps",
            "battery_charging",
            "battery_discharging",
        ]:
            fueltech_score = 10 if milestone.aggregate == MilestoneAggregate.high else 3
        else:
            fueltech_score = 5
    fueltech_score *= MilestoneSignificanceWeights.FUELTECH.value

    # Aggregate significance
    aggregate_score = 10 if milestone.aggregate == MilestoneAggregate.high else 5
    aggregate_score *= MilestoneSignificanceWeights.AGGREGATE.value

    # some fueltechs that are dispatchable or we don't have about the lows since they're often 0
    if (
        milestone.fueltech
        and milestone.fueltech.value in ["distillate", "solar", "battery_charging", "battery_discharging", "hydro", "pumps"]
        and milestone.aggregate == MilestoneAggregate.low
    ):
        return 1

    # power metrics just follow network min/max boundaries so aren't significant
    if milestone.metric == MilestoneType.price:
        return 1

    # Calculate total score
    total_score = sum([period_score, metric_score, network_score, region_score, fueltech_score, aggregate_score])

    # Scale score
    scaled_score = 1 + (total_score - 1) * 7 / 7

    return round(scaled_score)


async def update_milestone_significance(session: AsyncSession, instance_id: UUID4, significance: int) -> None:
    """Updates the description of a milestone"""
    update_query = update(Milestones).where(Milestones.instance_id == instance_id)
    await session.execute(update_query.values(significance=significance))


async def refresh_milestone_significance(limit: int | None = None, instance_id: UUID4 | None = None) -> None:
    """Refreshes the milestone significance"""

    async with get_write_session() as session:
        if instance_id:
            record = await get_milestone_record(session=session, instance_id=instance_id)
            if record:
                records = [record]
            else:
                records = []
        else:
            query = select(Milestones).order_by(Milestones.interval.desc())
            records_scalars = (await session.execute(query)).scalars().all()
            # convert to list of dicts
            records = [rec.__dict__ for rec in records_scalars]

        logger.info(f"Refreshing {len(records)} milestone significance")

        record_schemas = map_milestone_output_records_from_db(records)

        tasks = []

        logger.info(f"Updating {len(record_schemas)} milestone significance")

        with tqdm(total=len(record_schemas), desc="Refreshing milestones") as pbar:
            for record in record_schemas:
                record_input = map_milestone_output_schema_to_record(record)
                update_significance = calculate_milestone_significance(record_input)

                tasks.append(
                    update_milestone_significance(
                        session=session, instance_id=record.instance_id, significance=update_significance
                    )
                )

                if len(tasks) >= 8:
                    await asyncio.gather(*tasks)
                    pbar.update(len(tasks))
                    tasks = []

            # exec remaining tasks
            if tasks:
                await asyncio.gather(*tasks)
                pbar.update(len(tasks))

        await session.commit()

    logger.info(f"Updated {len(record_schemas)} milestone significances")


if __name__ == "__main__":
    import asyncio
    import uuid

    test_instance = uuid.UUID("005c0159-fcb8-474e-aee8-61fc36c6bcac")

    asyncio.run(refresh_milestone_significance(limit=None))
