#!/usr/bin/env python
"""
Storage bucket uploader module for OpenNEM

This module provides functionality to upload files to cloud storage buckets, specifically
Cloudflare R2 storage. It handles file uploads, content type detection, and provides
a consistent interface for storing OpenNEM data files.

The module supports:
 * Uploading files from disk
 * Uploading bytes from memory
 * Content type detection
 * Async operations using aioboto3
 * Error handling and logging
"""

import asyncio
import logging
import os

import aioboto3
from botocore.exceptions import ClientError

from opennem import settings
from opennem.utils.mime import mime_from_filename

logger = logging.getLogger(__name__)


class CloudflareR2Uploader:
    def __init__(self, region: str = "apac"):
        self.account_id = settings.s3_access_key_id
        self.access_key_id = settings.s3_access_key_id
        self.secret_access_key = settings.s3_secret_access_key
        self.endpoint_url = settings.s3_endpoint_url
        self.bucket_name = settings.s3_bucket_name
        self.region = region
        self.bucket_public_url = settings.s3_bucket_public_url

        if not self.bucket_public_url.endswith("/"):
            self.bucket_public_url += "/"

    async def _get_s3_client(self):
        """
        Create and return an S3 client session.

        Returns:
            An aioboto3 S3 client session.
        """
        session = aioboto3.Session()
        return session.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )

    async def upload_file(
        self,
        file_path: str,
        object_name: str | None = None,
        content_type: str | None = None,
    ) -> int:
        """
        Upload a file to a Cloudflare R2 bucket.

        Args:
            bucket_name (str): The name of the bucket to upload to.
            file_path (str): The path to the file to upload.
            object_name (Optional[str]): The object name in the bucket. If None, uses file_path.
            content_type (Optional[str]): The content type of the file.

        Raises:
            ClientError: If an error occurs during the upload process.
        """
        if object_name is None:
            object_name = file_path

        if object_name.startswith("/"):
            object_name = object_name[1:]

        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await s3.upload_file(file_path, self.bucket_name, object_name, ExtraArgs=extra_args)
                logger.info(f"File {file_path} uploaded successfully to {self.bucket_name}/{object_name}")
                return os.path.getsize(file_path)

            except ClientError as e:
                logger.error(f"An error occurred while uploading file: {e}")
                raise

    async def upload_bytes(
        self,
        content: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> int:
        """
        Upload bytes to a Cloudflare R2 bucket.

        Args:
            content: The content to upload.
            object_name: The object name in the bucket.
            content_type: The content type of the data.

        Raises:
            ClientError: If an error occurs during the upload process.
        """
        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await s3.put_object(Bucket=self.bucket_name, Key=object_name, Body=content, **extra_args)

                return len(content)
            except ClientError as e:
                logger.error(f"An error occurred while uploading content: {e}")
                raise

    async def upload_content(
        self,
        content: str,
        object_name: str,
        content_type: str | None = None,
    ) -> int:
        """
        Upload content as a string to a Cloudflare R2 bucket.

        Args:
            bucket_name (str): The name of the bucket to upload to.
            content (str): The content to upload.
            object_name (str): The object name in the bucket.
            content_type (Optional[str]): The content type of the data.

        Raises:
            ClientError: If an error occurs during the upload process.
        """

        if object_name.startswith("/"):
            object_name = object_name[1:]

        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await s3.put_object(Bucket=self.bucket_name, Key=object_name, Body=content, **extra_args)
                return len(content)
            except ClientError as e:
                logger.error(f"An error occurred while uploading content: {e}")
                raise


cloudflare_uploader = CloudflareR2Uploader(region="apac")


async def _main():
    import sys

    uploader = CloudflareR2Uploader(region="apac")

    if not sys.argv[1]:
        print("Please provide a file path to upload")
        return

    filepath = sys.argv[1]
    content_type = mime_from_filename(filepath)

    logger.info(f"Uploading file {filepath} with content type {content_type}")

    with open(filepath, "rb") as fh:
        content = fh.read()

    await uploader.upload_bytes(content, filepath, content_type="text/plain")


if __name__ == "__main__":
    asyncio.run(_main())
