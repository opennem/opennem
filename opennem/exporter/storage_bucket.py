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
 * Directory listing and file information retrieval
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime

import aioboto3
from botocore.exceptions import ClientError
from humanize import naturalsize, naturaltime

from opennem import settings

logger = logging.getLogger("opennem.storage_bucket")


@dataclass
class BucketFile:
    """
    Represents a file stored in the cloud storage bucket.

    Attributes:
        name (str): The name of the file without the path
        full_path (str): The complete path of the file in the bucket
        size (int): Size of the file in bytes
        last_modified (datetime): Last modification timestamp of the file
    """

    name: str
    file_path: str
    size: int
    last_modified: datetime

    @property
    def file_name(self) -> str:
        return os.path.basename(self.file_path)

    @property
    def size_human(self) -> str:
        return naturalsize(self.size, binary=True)

    @property
    def last_modified_human(self) -> str:
        return naturaltime(self.last_modified)

    @property
    def url(self) -> str:
        return f"{settings.s3_bucket_public_url}{self.file_path}"


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

    async def list_directory(self, prefix: str = "") -> list[BucketFile]:
        """
        Get a listing of files in the bucket under the specified prefix.

        Args:
            prefix: The directory prefix to list (e.g., "data/2024/")

        Returns:
            A list of BucketFile objects containing file information

        Raises:
            ClientError: If an error occurs while accessing the bucket
        """
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                paginator = s3.get_paginator("list_objects_v2")
                file_list: list[BucketFile] = []

                async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                    if "Contents" not in page:
                        continue

                    for obj in page["Contents"]:
                        # Skip directory markers
                        if obj["Key"].endswith("/"):
                            continue

                        logger.info(f"Listing {obj['Key']} with size {obj['Size']}")

                        file_list.append(
                            BucketFile(
                                name=os.path.basename(obj["Key"]),
                                file_path=obj["Key"],
                                size=obj["Size"],
                                last_modified=obj["LastModified"],
                            )
                        )

                return sorted(file_list, key=lambda x: x.last_modified, reverse=True)

            except ClientError as e:
                logger.error(f"Error listing directory {prefix}: {e}")
                raise


cloudflare_uploader = CloudflareR2Uploader(region="apac")


async def _main():
    uploader = CloudflareR2Uploader(region="apac")

    dir_listings = await uploader.list_directory("archive/nem/")

    for dir_listing in dir_listings:
        print(f"{dir_listing.file_name} - {dir_listing.size_human} - {dir_listing.last_modified_human} - {dir_listing.url}")


if __name__ == "__main__":
    asyncio.run(_main())
