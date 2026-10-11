import asyncio
import json
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import Response
from fastapi_versionizer.versionizer import api_version
from pydantic import BaseModel, EmailStr
from starlette.exceptions import HTTPException

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.clients.slack_app import verify_slack_signature
from opennem.tasks.broker import get_redis_pool

logger = logging.getLogger("opennem.api.webhooks.router")

router = APIRouter(tags=["Webhooks"], include_in_schema=False)

SANITY_SYNC_DEFER_SECONDS = 60


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
    response_model_exclude_unset=False,
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

    if "sanity-project-id" not in request.headers:
        raise HTTPException(status_code=400, detail="Invalid request sanity-project-id header missing")

    if request.headers["sanity-project-id"] != settings.sanity_project_id:
        raise HTTPException(status_code=400, detail="Invalid request sanity-project-id does not match")

    request_json = await request.json()

    if "_type" not in request_json:
        raise HTTPException(status_code=400, detail="Invalid request no _type field present")

    if "_id" not in request_json:
        raise HTTPException(status_code=400, detail="Invalid request no _id field present")

    record_type = str(request_json["_type"]).lower()
    cms_id = str(request_json["_id"]).strip()

    # sanity is eventually consistent so the sync is deferred, and the job id dedupes bursts of
    # edits to the same document while a job is still queued
    try:
        redis = await get_redis_pool()
        try:
            await redis.enqueue_job(
                "task_sanity_webhook",
                record_type,
                cms_id,
                _defer_by=SANITY_SYNC_DEFER_SECONDS,
                _job_id=f"sanity:{record_type}:{cms_id}",
            )
        finally:
            await redis.close()
    except Exception as e:
        # 5xx so sanity retries the delivery
        logger.error(f"Could not enqueue sanity webhook {record_type}:{cms_id}: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable") from e

    return "OK"


@api_version(4)
@router.post(
    "/clerk/{webhook_secret}",
    response_model_exclude_unset=False,
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


@router.post(
    "/slack/interactive",
    include_in_schema=False,
)
async def slack_interaction(request: Request) -> Response:
    """Slack interaction webhook — handles social post Approve/Reject buttons.

    Slack sends form-encoded payload when a user clicks a Block Kit button.
    Must respond 200 within 3 seconds; heavy work runs async.
    """
    await verify_slack_signature(request)

    # Slack sends application/x-www-form-urlencoded with a "payload" field
    form = await request.form()
    try:
        payload = json.loads(form["payload"])
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid Slack interaction payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload") from e

    action = payload.get("actions", [{}])[0]
    action_id = action.get("action_id", "")
    callback_value = action.get("value", "")
    user = payload.get("user", {}).get("username", "unknown")

    # callback_value is the social post UUID
    try:
        post_id = UUID(callback_value)
    except (ValueError, TypeError):
        logger.error(f"Invalid callback value (not a UUID): {callback_value}")
        return Response(status_code=200)

    from opennem.social.pipeline import approve_social_post, reject_social_post

    if action_id == "weekly_approve":
        logger.info(f"Social post {post_id} approved by {user}")
        asyncio.create_task(approve_social_post(post_id, approved_by=user))

    elif action_id == "weekly_reject":
        logger.info(f"Social post {post_id} rejected by {user}")
        asyncio.create_task(reject_social_post(post_id, rejected_by=user))

    return Response(status_code=200)
