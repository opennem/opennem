"""
    Utility functions for API exporter

"""
import json
import logging

from pydantic.main import BaseModel

from opennem.exporter.aws import write_to_s3
from opennem.exporter.local import write_to_local
from opennem.settings import settings

logger = logging.getLogger(__name__)


def write_output(
    path: str,
    stat_set: BaseModel,
    is_local: bool = False,
    exclude_unset: bool = True,
    exclude: set = None,
) -> int:

    if settings.export_local:
        is_local = True

    if hasattr(stat_set, "json"):
        indent = None

        if settings.debug:
            indent = 4

        write_content = stat_set.json(exclude_unset=exclude_unset, indent=indent, exclude=exclude)
    else:
        write_content = json.dumps(stat_set)

    byte_count = 0

    if is_local:
        byte_count = write_to_local(path, write_content)
    else:
        byte_count = write_to_s3(stat_set, path)

    return byte_count
