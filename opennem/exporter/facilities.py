"""
Exports all approved facilites to a static JSON file for use on the OpenNEM
and OpenElectricity websites on the facilities page.

"""

import asyncio

from opennem.api.schema import APIV4ResponseSchema
from opennem.cms.importer import get_cms_facilities
from opennem.exporter.storage_bucket import cloudflare_uploader


async def export_facilities_static() -> None:
    """Export facilities to a static JSON file"""

    # get all facilities
    facilities = get_cms_facilities()

    model_output = APIV4ResponseSchema(success=True, data=facilities, total_records=len(facilities))

    await cloudflare_uploader.upload_content(
        model_output.model_dump_json(exclude_unset=True, exclude_none=True),
        "/v4/facilities/au_facilities.json",
        content_type="application/json",
    )


if __name__ == "__main__":
    asyncio.run(export_facilities_static())
