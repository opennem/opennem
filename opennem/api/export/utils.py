"""
Utility functions for API exporter

"""

import logging

from pydantic.main import BaseModel

from opennem import settings
from opennem.api.stats.schema import OpennemDataSet
from opennem.exporter.aws import write_statset_to_s3, write_to_s3
from opennem.exporter.local import write_to_local
from opennem.exporter.r2_bucket import write_content_to_r2, write_stat_set_to_r2

logger = logging.getLogger(__name__)


def write_output(
    path: str,
    stat_set: BaseModel,
    is_local: bool = False,
    exclude_unset: bool = True,
) -> int:
    """Writes output of stat sets either locally or to s3"""
    if settings.export_local:
        is_local = True

    write_content = stat_set.model_dump_json(exclude_unset=exclude_unset)

    byte_count = 0

    if is_local:
        byte_count = write_to_local(path, write_content)
    elif isinstance(stat_set, str):
        byte_count = write_content_to_r2(stat_set, path, "application/json")
    elif isinstance(stat_set, OpennemDataSet):
        byte_count = write_stat_set_to_r2(stat_set, path, exclude_unset=exclude_unset)
    elif isinstance(stat_set, BaseModel):
        byte_count = write_content_to_r2(write_content, path, "application/json")
    else:
        raise Exception("Do not know how to write content of this type to output")

    return byte_count
