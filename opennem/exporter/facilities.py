"""
Exports all approved facilites to a static JSON file for use on the OpenNEM
and OpenElectricity websites on the facilities page.

"""

import asyncio
import logging

from opennem import settings
from opennem.api.schema import APIV4ResponseSchema
from opennem.clients.slack import slack_message
from opennem.cms.importer import get_cms_facilities
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.schema.unit import UnitDispatchType, UnitFueltechType
from opennem.utils.dates import get_today_opennem
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.exporter.facilities")


async def export_facilities_static() -> None:
    """Export facilities to a static JSON file"""

    # get all facilities
    facilities = get_cms_facilities()

    # remove 'battery' units
    facilities_clean = []

    for facility in facilities:
        units = [u for u in facility.units if u.fueltech_id != UnitFueltechType.battery]

        # sanity check the units are not empty
        if not units:
            logger.warning(f"Facility {facility.code} - {facility.name} has no units")
            continue

        # sanity check unit has required fields
        for unit in units:
            required_fields = ["code", "fueltech_id", "dispatch_type", "status_id"]
            for field in required_fields:
                if not getattr(unit, field):
                    message = f"Facility {facility.code} - {facility.name} has unit {unit.code} with missing field {field}"
                    await slack_message(webhook_url=settings.slack_hook_new_facilities, message=message)
                    logger.warning(message)
                    continue

            # check that battery dispatch types are correct
            if unit.fueltech_id == UnitFueltechType.battery_discharging:
                if unit.dispatch_type != UnitDispatchType.GENERATOR:
                    message = (
                        f"Facility {facility.code} - {facility.name} has"
                        f" unit {unit.code} with incorrect dispatch type for"
                        f" fueltech {unit.fueltech_id.value}: {unit.dispatch_type.value}"
                    )
                    await slack_message(webhook_url=settings.slack_hook_new_facilities, message=message)
                    logger.warning(message)

            if unit.fueltech_id == UnitFueltechType.battery_charging:
                if unit.dispatch_type != UnitDispatchType.LOAD:
                    message = (
                        f"Facility {facility.code} - {facility.name} has"
                        f" unit {unit.code} with incorrect dispatch type for"
                        f" fueltech {unit.fueltech_id.value}: {unit.dispatch_type.value}"
                    )
                    await slack_message(webhook_url=settings.slack_hook_new_facilities, message=message)
                    logger.warning(message)
        facility.units = units
        facilities_clean.append(facility)

    model_output = APIV4ResponseSchema(
        version=get_version(),
        created_at=get_today_opennem(),
        success=True,
        total_records=len(facilities_clean),
        data=facilities_clean,
    )

    await cloudflare_uploader.upload_content(
        model_output.model_dump_json(exclude_unset=True, exclude_none=True),
        "/v4/facilities/au_facilities.json",
        content_type="application/json",
    )


if __name__ == "__main__":
    asyncio.run(export_facilities_static())
