import asyncio
import logging

import aioboto3
from botocore.exceptions import ClientError

from opennem import settings

logger = logging.getLogger(__name__)


class CloudflareR2Uploader:
    def __init__(self, region: str = "apac"):
        self.account_id = settings.s3_access_key_id
        self.access_key_id = settings.s3_access_key_id
        self.secret_access_key = settings.s3_secret_access_key
        self.endpoint_url = settings.s3_endpoint_url
        self.bucket_name = settings.s3_bucket_name
        self.region = region

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
    ) -> None:
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

        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await s3.upload_file(file_path, self.bucket_name, object_name, ExtraArgs=extra_args)
                logger.info(f"File {file_path} uploaded successfully to {self.bucket_name}/{object_name}")
            except ClientError as e:
                logger.error(f"An error occurred while uploading file: {e}")
                raise

    async def upload_content(
        self,
        content: str,
        object_name: str,
        content_type: str | None = None,
    ) -> None:
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
        async with await self._get_s3_client() as s3:  # type: ignore
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                await s3.put_object(Bucket=self.bucket_name, Key=object_name, Body=content, **extra_args)
                logger.info(f"Content uploaded successfully to {settings.s3_bucket_public_url}/{object_name}")
            except ClientError as e:
                logger.error(f"An error occurred while uploading content: {e}")
                raise


cloudflare_uploader = CloudflareR2Uploader(region="apac")


async def main():
    uploader = CloudflareR2Uploader(region="apac")

    # Example of uploading a file
    file_path = "settings.txt"
    logger.debug(f"Uploading {file_path} to {settings.s3_bucket_name}")
    await uploader.upload_file(file_path, content_type="text/plain")

    # Example of uploading content as a string
    content = "This is some example content."
    object_name = "example_content.txt"
    logger.debug(f"Uploading content to {settings.s3_bucket_name}/{object_name}")
    await uploader.upload_content(content, object_name, content_type="text/plain")


if __name__ == "__main__":
    asyncio.run(main())
