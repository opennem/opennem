"""
RecordReactor demand methods
"""

import logging
import uuid
from itertools import product

from sqlalchemy.exc import IntegrityError

from opennem.core.networks import network_from_network_code
from opennem.db import SessionLocalAsync
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.map import get_milestone_map_by_record_id
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestoneRecordSchema, MilestoneSchema
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new, get_record_description
from opennem.utils.dates import make_aware_for_network

logger = logging.getLogger("opennem.recordreactor.persistence")


async def persist_milestones(
    metrics: list[MilestoneMetric],
    aggregates: list[MilestoneAggregate],
    bucket_size: str,
    aggregated_data: list[dict],
):
    """ """

    milestone_state = await get_current_milestone_state()

    async with SessionLocalAsync() as session:
        for data in aggregated_data:
            # get the network
            network_id = data.get("network_id")

            if not network_id:
                raise ValueError(f"No network ID for {data}")

            network = network_from_network_code(network_id)

            # create mileston schemas
            milestone_schemas: list[MilestoneSchema] = []

            for metric, aggregate in product(metrics, aggregates):
                for milestone_record_id in [
                    f"au.{network.code.lower()}.{data['network_region'].lower()}.{metric.value}.{bucket_size}.{aggregate.value}",
                    f"au.{network.code.lower()}.{data['network_region'].lower()}.{data['fueltech_id'].lower()}.{metric.value}.{bucket_size}.{aggregate.value}"
                    if data.get("fueltech_id")
                    else None,
                ]:
                    try:
                        milestone_map = await get_milestone_map_by_record_id(milestone_record_id)

                        if milestone_map:
                            milestone_schemas.append(milestone_map)
                    except ValueError:
                        logger.warning(f"Invalid milestone record id: {milestone_record_id}")

            for milestone_schema in milestone_schemas:
                milestone_prev: MilestoneRecordSchema | None = None

                if milestone_schema.record_id in milestone_state:
                    milestone_prev = milestone_state[milestone_schema.record_id]

                if not milestone_prev or check_milestone_is_new(milestone_schema, milestone_prev, data):
                    data_key = f"{milestone_schema.metric.value}_{milestone_schema.aggregate.value}"
                    data_value = data.get(data_key)

                    if not data_value:
                        logger.warning(f"No data for {milestone_schema.record_id}")
                        continue

                    bucket = data.get("bucket")

                    if not bucket:
                        raise ValueError(f"No bucket data for {milestone_schema.record_id}")

                    interval = make_aware_for_network(bucket, network)

                    milestone_record_schema = MilestoneRecordSchema(
                        **milestone_schema.model_dump(),
                        interval=interval,
                        instance_id=uuid.uuid4(),
                        value=data_value,
                        significance=1,
                        network=network,
                    )

                    description = get_record_description(milestone_record_schema)

                    milestone_new = Milestones(
                        record_id=milestone_schema.record_id,
                        interval=interval,
                        aggregate=milestone_schema.aggregate.value,
                        metric=milestone_schema.metric.value,
                        period=bucket_size,
                        significance=1,
                        value=data_value,
                        value_unit=milestone_schema.unit.value,
                        network_id=network.code,
                        network_region=data.get("network_region"),
                        fueltech_id=data.get("fueltech_id"),
                        description=description,
                        previous_instance_id=milestone_prev.instance_id if milestone_prev else None,
                    )

                    try:
                        await session.merge(milestone_new)

                        # update state to point to this new milestone
                        milestone_state[milestone_schema.record_id] = milestone_record_schema

                        logger.info(
                            f"Added milestone for interval {data['bucket']} {milestone_schema.record_id} with value {data_value}"
                        )
                    except IntegrityError:
                        logger.warning(f"Milestone already exists: {milestone_schema.record_id} for interval {interval}")

            await session.commit()
