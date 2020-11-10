"""
    Utility functions for API exporter

"""
import logging

from opennem.api.stats.schema import OpennemDataSet
from opennem.exporter.aws import write_to_s3
from opennem.exporter.local import write_to_local
from opennem.settings import settings

logger = logging.getLogger(__name__)


def write_output(
    path: str, stat_set: OpennemDataSet, is_local: bool = False
) -> None:

    if settings.export_local:
        is_local = True

    write_func = write_to_local if is_local else write_to_s3
    byte_count = write_func(path, stat_set.json(exclude_unset=True))

    logger.info("Wrote {} bytes to {}".format(byte_count, path))

    return byte_count
