"""
Update CMS record value on sanity
"""

import logging

from portabletext_html import PortableTextRenderer
from pydantic import ValidationError

from opennem.cms.client import sanity_client
from opennem.schema.facility import CMSFacilitySchema

logger = logging.getLogger("opennem.cms.update")


def get_cms_facilities(facility_code: str | None = None) -> list[CMSFacilitySchema]:
    filter_query = ""

    if facility_code:
        filter_query += f" && code == '{facility_code}'"

    query = f"""*[_type == "facility"{filter_query} && !(_id in path("drafts.**"))] {{
        _id,
        _createdAt,
        _updatedAt,
        code,
        name,
        website,
        description,
        "network_id": upper(network->code),
        "network_region": upper(region->code),
        photos,
        wikipedia,
        location,
        units[]-> {{
            code,
            dispatch_type,
            "status_id": status,
            "network_id": upper(network->code),
            "network_region": upper(network_region->code),
            "fueltech_id": fuel_technology->code,
            capacity_registered,
            capacity_maximum,
            storage_capacity,
            emissions_factor_co2,
            expected_closure_date,
            commencement_date,
            closure_date
        }}
    }}"""

    res = sanity_client.query(query)

    if not res or not isinstance(res, dict) or "result" not in res or not res["result"]:
        logger.error("No facilities found")
        return []

    result_models = {}

    # compile the facility description to html
    for facility in res["result"]:
        if facility.get("description") and isinstance(facility["description"], list):
            rendered_description = ""
            for block in facility["description"]:
                rendered_description += PortableTextRenderer(block).render()
            if rendered_description:
                facility["description"] = rendered_description

        if facility.get("_id"):
            facility["id"] = facility["_id"]

        if facility["_updatedAt"]:
            facility["updated_at"] = facility["_updatedAt"]

        if facility["code"] in result_models:
            logger.warning(
                f"Duplicate facility code {facility['code']} sanity. {facility['_id']}"
                # f" existing {result_models[facility['code']].id}"
            )
            continue

        try:
            result_models[facility["code"]] = CMSFacilitySchema(**facility)
        except ValidationError as e:
            logger.error(f"Error creating facility model for {facility['code']}: {e}")
            logger.debug(facility)
            raise e

    return list(result_models.values())


def update_cms_record(facility: CMSFacilitySchema) -> None:
    transactions = [
        {
            "createOrUpdate": {
                "id": facility.code,
                "data": facility.model_dump(),
            }
        }
    ]
    res = sanity_client.mutate(
        transactions=transactions,
        return_documents=True,
    )

    logger.info(f"Updated facility {facility.code} on sanity: {res}")
