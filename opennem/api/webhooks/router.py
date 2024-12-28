import logging

from fastapi import APIRouter, Request
from fastapi_versionizer.versionizer import api_version
from starlette.exceptions import HTTPException

from opennem import settings
from opennem.controllers.sanity import parse_sanity_webhook_request

logger = logging.getLogger("opennem.api.webhooks.router")

router = APIRouter(tags=["Webhooks"], include_in_schema=False)


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
