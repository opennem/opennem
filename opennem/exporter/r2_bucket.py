"""
OpenNEM R2 Bucket Module

Writes OpennemDataSet's to AWS R2 buckets
"""

import logging
from urllib.parse import urljoin

from aioboto3.session import Session
from aiohttp import ClientError
from httpx import Client
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
            raise RuntimeError("Error in inner function") from e

        write_result["length"] = len(stat_set_content)

        return write_result
    

async def write_stat_set_to_r2(stat_set: OpennemDataSet, file_path: str, exclude: set | None = None, exclude_unset: bool = False) -> int:
    r2_save_path = urljoin(f"https://{settings.s3_bucket_path}", file_path)

    if file_path.startswith("/"):
        file_path = file_path[1:]

    if not settings.s3_bucket_name:
        raise Exception("Require an R2 bucket to write to")
    
    r2_bucket = OpennemDataSetSerialize(settings.s3_bucket_name, exclude_unset=exclude_unset)
    write_response = None

    try:
        await r2_bucket.get_or_create_S3_bucket()
        write_response = await r2_bucket.dump(file_path, stat_set, exclude=exclude)
    except ClientError as e:
        logger.log(e)
        return 1
    
    if "ResponseMetadata" not in write_response:
        raise Exception(f"Error writing stat set to {file_path} invalid write response")

    if "HTTPStatusCode" not in write_response["ResponseMetadata"]:
        raise Exception(f"Error writing stat set to {file_path} invalid write response")

    if write_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise Exception(
            "Error writing stat set to {} - response code {}".format(
                file_path, write_response["ResponseMetadata"]["HTTPStatusCode"]
            )
        )

    logger.info("Wrote {} to {}".format(write_response["length"], r2_save_path))

    return write_response["length"]