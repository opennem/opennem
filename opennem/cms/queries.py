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
from opennem.schema.facility import FacilityPhotoOutputSchema, FacilitySchema
from opennem.schema.unit import UnitSchema

logger = logging.getLogger("opennem.cms.queries")


class CMSQueryError(Exception):
    """Error querying the CMS"""

    pass


def get_cms_owners() -> list[dict]:
    query = """*[_type == "owner"  && !(_id in path("drafts.**"))] {
        _id,
        _createdAt,
        _updatedAt,
        name,
        legal_name,
        website,
        wikipedia
    }"""

    res = sanity_client.query(query)

    if not res or not isinstance(res, dict) or "result" not in res or not res["result"]:
        raise CMSQueryError("No owners found")

    return res["result"]


def get_cms_unit(unit_code: str) -> UnitSchema:
    """
    Get units from the CMS
    """

    query = f"""*[_type == "unit" && code == '{unit_code}' && !(_id in path("drafts.**"))] {{
        _id,
        _createdAt,
        _updatedAt,
        code,
        dispatch_type,
        "fueltech_id": fuel_technology->code,
        "status_id": status,
        capacity_registered,
        emissions_factor_co2
    }}"""

    res = sanity_client.query(query)

    logger.debug(res)

    if not res or not isinstance(res, dict) or "result" not in res or not res["result"]:
        raise CMSQueryError(f"No unit found for {unit_code}")
    return UnitSchema(**res["result"][0])


def get_unit_factors() -> list[dict]:
    """
    Get unit factors from the CMS
    """
    query = """*[_type == "facility" && !(_id in path("drafts.**"))] {
        _id,
        _createdAt,
        _updatedAt,
        code,
        name,
        "network_id": upper(network->code),
        "network_region": upper(region->code),
        units[]-> {
            code,
            "fueltech_id": fuel_technology->code,
            "emissions_factor_co2": emissions_factor_co2,
            "emissions_factor_source": emissions_factor_source
        }
    }"""

    res = sanity_client.query(query)

    return res["result"]


def get_cms_facilities(facility_code: str | None = None) -> list[FacilitySchema]:
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
        photos[] {{
            "url": asset->url,
            "url_source": url,
            "caption": caption,
            "attribution": attribution,
            "alt": alt,
            "metadata": asset->metadata
        }},
        owners[]-> {{
            name,
            website,
            wikipedia
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

        if facility.get("photos", None):
            facility_photos = facility.get("photos", [])

            # clear the photos list
            facility["photos"] = []

            for photo in facility_photos:
                if not photo:
                    continue

                if not photo.get("url"):
                    continue

                try:
                    photo_dict = {
                        "url": photo.get("url"),
                        "url_source": photo.get("url_source"),
                        "caption": photo.get("caption"),
                        "attribution": photo.get("attribution"),
                        "alt": photo.get("alt"),
                    }

                    if photo.get("metadata"):
                        metadata = photo.get("metadata", None)

                        if metadata:
                            photo_dict["width"] = metadata.get("dimensions", {}).get("width")
                            photo_dict["height"] = metadata.get("dimensions", {}).get("height")

                    photo_model = FacilityPhotoOutputSchema(**photo_dict)
                    facility["photos"].append(photo_model.model_dump())
                except Exception as e:
                    print(photo)
                    logger.error("Error adding photo")
                    print(e)

        try:
            result_models[facility["code"]] = FacilitySchema(**facility)
        except ValidationError as e:
            logger.error(f"Error creating facility model for {facility['code']}: {e}")
            logger.debug(facility)
            raise e

    return list(result_models.values())


def update_cms_record(facility: FacilitySchema) -> None:
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
    owners = get_cms_owners()
    logger.info(f"Found {len(owners)} owners")
    print(owners)
