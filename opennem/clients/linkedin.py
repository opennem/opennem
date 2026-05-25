"""OpenElectricity LinkedIn client"""

import io
import logging

from opennem import settings
from opennem.utils.http import http_factory

logger = logging.getLogger("opennem.clients.linkedin")

LINKEDIN_API_BASE = "https://api.linkedin.com"

_http_client = http_factory(proxy=False, mimic_browser=False)


class LinkedInNotConfiguredError(RuntimeError):
    """LinkedIn credentials missing — caller should mark platform as skipped, not failed."""


def _get_headers() -> dict[str, str]:
    """Get auth headers for LinkedIn API."""
    return {
        "Authorization": f"Bearer {settings.linkedin_access_token}",
        "LinkedIn-Version": "202402",
        "X-Restli-Protocol-Version": "2.0.0",
    }


async def _upload_image(image: io.BytesIO) -> str | None:
    """Upload an image to LinkedIn and return the image URN.

    Three-step process:
    1. Initialize upload to get upload URL + image URN
    2. PUT binary data to upload URL
    3. Return image URN for use in post creation
    """
    org_urn = f"urn:li:organization:{settings.linkedin_organization_id}"

    # Step 1: Initialize upload
    init_resp = await _http_client.post(
        f"{LINKEDIN_API_BASE}/rest/images?action=initializeUpload",
        headers=_get_headers(),
        json={"initializeUploadRequest": {"owner": org_urn}},
    )

    if init_resp.status_code != 200:
        logger.error(f"LinkedIn image upload init failed: {init_resp.status_code}: {init_resp.text}")
        return None

    init_data = init_resp.json()
    upload_url = init_data["value"]["uploadUrl"]
    image_urn = init_data["value"]["image"]

    # Step 2: Upload binary
    image.seek(0)
    upload_resp = await _http_client.put(
        upload_url,
        headers={"Authorization": f"Bearer {settings.linkedin_access_token}"},
        content=image.read(),
    )

    if upload_resp.status_code not in (200, 201):
        logger.error(f"LinkedIn image upload failed: {upload_resp.status_code}: {upload_resp.text}")
        return None

    logger.info(f"Uploaded image to LinkedIn: {image_urn}")
    return image_urn


async def post_linkedin(text: str, image: io.BytesIO | None = None) -> dict:
    """Post to LinkedIn organization page with optional image.

    Args:
        text: Post text content
        image: Optional image as BytesIO

    Returns:
        {"platform_post_id": ugc_post_id, "permalink": LinkedIn URL} on success.
    """
    if not settings.linkedin_access_token or not settings.linkedin_organization_id:
        # TODO: revert to logger.error + critical-path behaviour once LINKEDIN_ACCESS_TOKEN is set in prod
        logger.warning("LinkedIn credentials not configured. Skipping post.")
        raise LinkedInNotConfiguredError("LinkedIn credentials not configured")

    org_urn = f"urn:li:organization:{settings.linkedin_organization_id}"

    # Upload image if provided
    image_urn = None
    if image:
        image_urn = await _upload_image(image)
        if not image_urn:
            logger.warning("Image upload failed, posting without image")

    # Build post payload
    post_payload: dict = {
        "author": org_urn,
        "lifecycleState": "PUBLISHED",
        "visibility": "PUBLIC",
        "commentary": text,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
    }

    if image_urn:
        post_payload["content"] = {
            "media": {
                "id": image_urn,
                "title": "Weekly Energy Summary",
            }
        }

    resp = await _http_client.post(
        f"{LINKEDIN_API_BASE}/rest/posts",
        headers={**_get_headers(), "Content-Type": "application/json"},
        json=post_payload,
    )

    if resp.status_code not in (200, 201):
        msg = f"LinkedIn post failed: {resp.status_code}: {resp.text}"
        logger.error(msg)
        raise RuntimeError(msg)

    # LinkedIn returns the new post URN in the `x-restli-id` header
    post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
    permalink = None
    if post_id and post_id.startswith("urn:li:share:"):
        share_id = post_id.split(":")[-1]
        permalink = f"https://www.linkedin.com/feed/update/urn:li:share:{share_id}/"
    elif post_id and post_id.startswith("urn:li:ugcPost:"):
        ugc_id = post_id.split(":")[-1]
        permalink = f"https://www.linkedin.com/feed/update/urn:li:ugcPost:{ugc_id}/"

    logger.info(f"Successfully posted to LinkedIn: {permalink or post_id or 'no id returned'}")
    return {"platform_post_id": post_id, "permalink": permalink}
