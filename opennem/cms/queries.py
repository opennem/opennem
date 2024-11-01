"""
Client query library to get facility and other data from the CMS.

The CMS is a Sanity.io instance.

For documentation on the CMS API see https://www.sanity.io/docs/query-cheat-sheet

The sanity python client is an unofficial client and may not be maintained up to date with the latest Sanity.io API.

For the official client see https://github.com/OmniPro-Group/sanity-python
"""

import logging

from portabletext_html import PortableTextRenderer
from pydantic import ValidationError

from opennem.cms.client import sanity_client
from opennem.schema.facility import CMSFacilitySchema

logger = logging.getLogger("opennem.cms.update")


def get_cms_facilities(facility_code: str | None = None) -> list[CMSFacilitySchema]:
    """
    Get facilities from the CMS

    :param facility_code: Filter by facility code
    :return: List of facilities
    """
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
        photos[0]-> {{
            "url": asset->url,
            caption,
            attribution
        }},
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


if __name__ == "__main__":
    facilities = get_cms_facilities()
    from pprint import pprint

    # get all unit codes
    for facility in facilities:
        for unit in facility.units:
            if unit.code == "LYGS1":
                pprint(unit)
                print(facility.code)