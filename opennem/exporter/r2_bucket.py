"""
OpenNEM R2 Bucket Module

Writes OpennemDataSet's to AWS R2 buckets
"""

import logging

from aioboto3.session import Session
from opennem import settings
from opennem.api.stats.schema import OpennemDataSet
from opennem.utils.numbers import compact_json_output_number_series
from typing import Any

logger = logging.getLogger("opennem.exporter.r2_bucket")

class OpennemDataSetSerialize:
    session: Session
    bucket: Any
    bucket_name: str
    debug: bool = False
    exclude_unset: bool = False

    def __init__(self, bucket_name: str, exclude_unset: bool = False, debug: bool = False) -> None:
        self.session = Session()
        self.bucket = None
        self.debug = settings.debug
        self.bucket_name = bucket_name
        self.exclude_unset = exclude_unset

        if debug:
            self.debug = debug

    async def get_or_create_S3_bucket(self):
        if self.bucket == None:
            async with self.session.resource("s3", endpoint_url=settings.s3_endpoint_url) as s3:
                try:
                    self.bucket = await s3.Bucket(self.bucket_name)
                except Exception as e:
                    print(e)

    async def dump(self, key: str, stat_set: OpennemDataSet, exclude: set | None = None) -> Any:
        indent = None

        if settings.debug:
            indent = 4

        stat_set_content = stat_set.model_dump_json(exclude_unset=self.exclude_unset, indent=indent, exclude=exclude)

        if settings.compact_number_ouput_in_json:
            logger.debug(f"Applying compact number output to {key}")

            if settings.compact_number_ouput_in_json:
                stat_set_content = compact_json_output_number_series(stat_set_content)

        try:
            obj_to_write = await self.bucket.Object(Key = key)
            write_result = await obj_to_write.put(Body=stat_set_content, ContentType="application/json")
        except Exception as e:
            print(e)

        write_result["length"] = len(stat_set_content)

        return write_result
    