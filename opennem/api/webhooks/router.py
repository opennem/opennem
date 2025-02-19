import logging
from typing import Literal

from fastapi import APIRouter, Request
from fastapi_versionizer.versionizer import api_version
from pydantic import BaseModel, EmailStr
from starlette.exceptions import HTTPException

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.controllers.sanity import parse_sanity_webhook_request

logger = logging.getLogger("opennem.api.webhooks.router")

router = APIRouter(tags=["Webhooks"], include_in_schema=False)


class ClerkEmailAddress(BaseModel):
    """Clerk email address model"""

    email_address: EmailStr
    id: str
    verification: dict
    object: Literal["email_address"]
    linked_to: list


class ClerkUserData(BaseModel):
    """Clerk user data model"""

    id: str
    email_addresses: list[ClerkEmailAddress]
    first_name: str
    last_name: str
    created_at: int


class ClerkWaitlistData(BaseModel):
    """Clerk waitlist data model"""

    id: str
    email_address: EmailStr
    created_at: int
    status: Literal["pending"]
    object: Literal["waitlist_entry"]


class ClerkWebhookEvent(BaseModel):
    """Clerk webhook event model"""

    data: ClerkUserData | ClerkWaitlistData
    object: Literal["event"]
    type: str
    timestamp: int


@api_version(4)
@router.post(
    "/sanity/{webhook_secret}",
    response_model_exclude_unset=True,
    description="Webhooks",
)
async def webhook_sanity_update(webhook_secret: str, request: Request) -> str:
    """
    Sanity webhook endpoint
    """

    if webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=404, detail="Not Found")

    if "Content-Type" not in request.headers:
        raise HTTPException(status_code=400, detail="Invalid request no Content-Type header present")

    if request.headers["Content-Type"] != "application/json":
        raise HTTPException(status_code=400, detail="Invalid request Content-Type is not application/json")

    if request.headers["sanity-project-id"] != settings.sanity_project_id:
        raise HTTPException(status_code=400, detail="Invalid request sanity-project-id does not match")

    request_json = await request.json()

    if "_type" not in request_json:
        raise HTTPException(status_code=400, detail="Invalid request no _type field present")

    try:
        await parse_sanity_webhook_request(request_json)
    except Exception as e:
        logger.error(f"Error parsing sanity webhook: {e}")
        raise HTTPException(status_code=500, detail="Server Error") from e

    return "OK"


@api_version(4)
@router.post(
    "/clerk/{webhook_secret}",
    response_model_exclude_unset=True,
    description="Clerk webhook endpoint",
)
async def webhook_clerk_update(webhook_secret: str, request: Request) -> str:
    """
    Clerk webhook endpoint that handles user signups and waitlist entries
    """

    # only run on prod
    if not settings.is_prod:
        raise HTTPException(status_code=404, detail="Not Found")

    if webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=404, detail="Not Found")

    if "Content-Type" not in request.headers:
        raise HTTPException(status_code=400, detail="Invalid request no Content-Type header present")

    if request.headers["Content-Type"] != "application/json":
        raise HTTPException(status_code=400, detail="Invalid request Content-Type is not application/json")

    request_json = await request.json()

    try:
        event = ClerkWebhookEvent.model_validate(request_json)
    except Exception as e:
        logger.error(f"Error parsing clerk webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid request payload") from e

    if event.type == "waitlistEntry.created":
        waitlist_data = event.data
        if not isinstance(waitlist_data, ClerkWaitlistData):
            raise HTTPException(status_code=400, detail="Invalid waitlist data")

        logger.info(f"New waitlist signup: {waitlist_data.email_address}")

        # Send slack notification
        await slack_message(
            webhook_url=settings.slack_hook_platform_alerts,
            message=f"New waitlist signup: {waitlist_data.email_address}",
        )

    elif event.type == "user.created":
        user_data = event.data
        if not isinstance(user_data, ClerkUserData):
            raise HTTPException(status_code=400, detail="Invalid user data")

        email = user_data.email_addresses[0].email_address if user_data.email_addresses else None
        logger.info(f"New user signup: {user_data.first_name} {user_data.last_name} ({email})")

        # Send slack notification
        await slack_message(
            webhook_url=settings.slack_hook_platform_alerts,
            message=f"New user signup: {user_data.first_name} {user_data.last_name} ({email})",
        )

    return "OK"
