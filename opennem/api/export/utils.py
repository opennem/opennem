"""
Utility functions for API exporter

"""

import logging

from pydantic.main import BaseModel

from opennem.api.stats.schema import OpennemDataSet
from opennem.exporter.local import write_to_local
from opennem.exporter.storage_bucket import cloudflare_uploader

logger = logging.getLogger(__name__)


async def write_output(
    path: str,
    stat_set: BaseModel,
    is_local: bool = False,
    exclude_unset: bool = True,
) -> int:
    """Writes output of stat sets either locally or to s3"""
    write_content = stat_set.model_dump_json(exclude_unset=exclude_unset)

    byte_count = 0

    if is_local:
        byte_count = write_to_local(path, write_content)
    elif isinstance(stat_set, str):
        byte_count = await cloudflare_uploader.upload_content(stat_set, path, "application/json")
    elif isinstance(stat_set, OpennemDataSet):
        byte_count = await cloudflare_uploader.upload_content(write_content, path, "application/json")
    elif isinstance(stat_set, BaseModel):
        byte_count = await cloudflare_uploader.upload_content(write_content, path, "application/json")

    return byte_count
