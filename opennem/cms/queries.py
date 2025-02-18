"""OpenNEM CMS Query Interface.

This module provides the interface between OpenNEM and the Sanity.io CMS, handling all
queries and data retrieval from the CMS. It includes functionality for:
- Retrieving facility and unit data
- Converting CMS data into OpenNEM schema models
- Caching frequently accessed data
- Handling CMS API errors and retries

The module uses the Sanity.io GROQ query language for all CMS queries. For more information
on GROQ, see https://www.sanity.io/docs/query-cheat-sheet

Note:
    The module uses an unofficial Python client for Sanity.io. For the official client,
    see https://github.com/OmniPro-Group/sanity-python

Technical Details:
    - Caching is implemented with a timed LRU cache (disabled in development)
    - Retries are implemented using the tenacity library
    - All CMS data is validated against Pydantic models
    - Rich text content (like descriptions) is rendered to HTML
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from time import timezone
from typing import TypeVar

from portabletext_html import PortableTextRenderer
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from opennem import settings
from opennem.cms.client import sanity_client
from opennem.schema.facility import FacilityPhotoOutputSchema, FacilitySchema
from opennem.schema.unit import UnitSchema

logger = logging.getLogger("opennem.cms.queries")


class CMSQueryError(Exception):
    """Error raised when querying the CMS fails.

    This exception is used to wrap any errors from the Sanity.io API or
    data validation errors when processing CMS responses.
    """

    pass


T = TypeVar("T")


def timed_lru_cache(seconds: int, maxsize: int = 128) -> Callable:
    """Create a cache that expires after the specified number of seconds.

    This decorator provides a time-based LRU cache that is disabled in development
    environments. The cache is automatically cleared when it expires.

    Args:
        seconds: Number of seconds before cache expires
        maxsize: Maximum size of cache (default: 128)

    Returns:
        Callable: Decorator function that can be applied to other functions

    Example:
        @timed_lru_cache(seconds=300)
        def my_function():
            # This function's results will be cached for 5 minutes
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Only use caching if not in development
        if settings.is_dev:
            return func

        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.now(timezone.utc) + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs) -> T:
            if datetime.now(timezone.utc) >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.now(timezone.utc) + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return decorator


def get_cms_owners() -> list[dict]:
    """Retrieve all owner records from the CMS.

    This function queries the CMS for all owner records, which contain information
    about facility owners including their legal names and contact details.

    Returns:
        list[dict]: List of owner records from the CMS

    Raises:
        CMSQueryError: If no owners are found or if there's an error querying the CMS
    """
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
    """Retrieve a single unit's data from the CMS.

    This function queries the CMS for a specific unit by its code and returns
    the data as a validated UnitSchema object.

    Args:
        unit_code: The unique identifier code for the unit

    Returns:
        UnitSchema: Validated unit data model

    Raises:
        CMSQueryError: If the unit is not found or if there's an error querying the CMS
        ValidationError: If the unit data doesn't match the expected schema
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
    """Retrieve emissions and other factor data for all units.

    This function queries the CMS for all facilities and their units, focusing on
    emissions factors and related metadata. This is used primarily for emissions
    calculations and reporting.

    Returns:
        list[dict]: List of facility records with their unit factors
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


@timed_lru_cache(seconds=300)  # 5 minute cache
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((CMSQueryError, ValidationError)),
    reraise=True,
)
def get_cms_facilities(facility_code: str | None = None) -> list[FacilitySchema]:
    """Retrieve facility data from the CMS with optional filtering.

    This is the primary function for retrieving facility data from the CMS. It includes
    comprehensive facility metadata, unit data, and related information. The function
    includes caching and retry logic for reliability.

    Features:
    - 5-minute cache in non-development environments
    - Retries up to 3 times with exponential backoff
    - Converts rich text descriptions to HTML
    - Validates all data against Pydantic models
    - Processes and validates facility photos

    Args:
        facility_code: Optional facility code to filter results

    Returns:
        list[FacilitySchema]: List of validated facility models

    Raises:
        CMSQueryError: If there's an error querying the CMS
        ValidationError: If the facility data doesn't match the expected schema

    Note:
        The function will retry on CMSQueryError and ValidationError, but will
        re-raise the error if all retries fail.
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
            logger.warning(f"Duplicate facility code {facility['code']} sanity. {facility['_id']}")
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
    """Update a facility record in the CMS.

    This function sends updates back to the CMS. It's used primarily for
    synchronizing data from the OpenNEM database back to the CMS when necessary.

    Args:
        facility: The facility data to update in the CMS

    Note:
        This is a less commonly used function as the CMS is typically
        the source of truth, but it's available for special cases where
        we need to update CMS data programmatically.
    """
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
