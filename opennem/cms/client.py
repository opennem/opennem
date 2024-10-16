import logging

from sanity import Client

from opennem import settings

logger = logging.getLogger(__name__)

sanity_client = Client(
    logger=logger,
    project_id=settings.sanity_project_id,
    dataset=settings.sanity_dataset_id,
    token=settings.sanity_api_key,
)
