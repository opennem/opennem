"""Module to upload images to cloudflare. Requires settings.cloudflare_api_key and settings.cloudflare_account_id"""

import logging
from datetime import datetime
from io import BytesIO

from pydantic import BaseModel

from opennem import settings
from opennem.utils.http import http_factory

logger = logging.getLogger("opennem.clients.cfimage")

CF_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"


class CloudflareImageException(Exception):
    pass


class CloudflareImageResponse(BaseModel):
    filename: str
    uploaded: datetime
    variants: list[str]

    @property
    def url(self) -> str | None:
        return self.variants.pop() if self.variants else None


async def save_image_to_cloudflare(image: bytes | BytesIO) -> CloudflareImageResponse:
    if not settings.cloudflare_api_key or not settings.cloudflare_account_id:
        raise CloudflareImageException("API not configured with account id and key")

    async with http_factory(proxy=False, mimic_browser=False) as http:
        headers = {"Authorization": f"Bearer {settings.cloudflare_api_key}"}

        cfimage_url = CF_URL.format(account_id=settings.cloudflare_account_id)

        response = await http.post(cfimage_url, headers=headers, files={"file": image})

        response.raise_for_status()

        if not response.is_success:
            logger.debug(response.text)
            raise CloudflareImageException(f"Response error: {response.status_code}. {response.text}")

        try:
            json_response = response.json()
        except ValueError as e:
            raise CloudflareImageException("Bad response json") from e

    if not json_response:
        raise CloudflareImageException("No json response")

    if "errors" in json_response and json_response["errors"]:
        err_msg = "\n".join(json_response["errors"])
        raise CloudflareImageException(f"Response errors: {err_msg}")

    if "success" not in json_response:
        raise CloudflareImageException("Bad response no success")

    if not json_response["success"]:
        raise CloudflareImageException("Bad response no success")

    try:
        model = CloudflareImageResponse(**json_response["result"])
    except Exception as e:
        raise CloudflareImageException("Bad response model") from e

    logger.info(f"Uploaded to cf and got {len(model.variants)} varianes: {','.join(model.variants)}")

    return model
