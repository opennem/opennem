import logging

import requests
from pydantic import ValidationError

from opennem.api.export.map import StatMetadata
from opennem.settings import settings
from opennem.utils.url import bucket_to_website, urljoin

logger = logging.getLogger(__name__)


def check_metadata_status() -> bool:
    metadata_path = bucket_to_website(
        urljoin(settings.s3_bucket_path, "metadata.json")
    )

    resp = requests.get(metadata_path)

    if resp.status_code != 200:
        logger.error("Error retrieving opennem metadata")
        return False

    resp_json = resp.json()

    metadata = None

    try:
        metadata = StatMetadata.parse_obj(resp_json)
    except ValidationError as e:
        logger.error("Validation error in metadata: {}".format(e))

    if not metadata:
        return False

    for resource in metadata.resources:
        if not resource.path:
            logger.info("Resource without path")
            continue

        resource_website_path = bucket_to_website(
            urljoin(settings.s3_bucket_path, resource.path)
        )

        r = requests.get(resource_website_path)

        if r.status_code != 200:
            logger.error(
                "Error with metadata resource: {}".format(
                    resource_website_path
                )
            )

    return True


if __name__ == "__main__":
    check_metadata_status()
