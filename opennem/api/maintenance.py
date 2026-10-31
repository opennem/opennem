"""API maintenance gate and public state endpoint (#782). Contract documented in opennem/core/maintenance.py.

The gate is pure ASGI and makes no DB, ClickHouse or Redis call. It sits inside CORSMiddleware so browsers can
read the 503 body, and short-circuits before routing, so neither fastapi-cache nor the response cache sees
(or stores) a maintenance answer.
"""

import json
import logging
import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.types import ASGIApp, Receive, Scope, Send

from opennem.core.maintenance import (
    NO_STORE_HEADERS,
    is_maintenance_mode,
    maintenance_error_body,
    maintenance_state,
    retry_after_seconds,
)

logger = logging.getLogger("opennem.api.maintenance")

_VERSION_PREFIX = re.compile(r"^/v\d+(?=/|$)")

# matched after the /vN prefix is stripped, so /health and /v4/health are both exempt
_EXEMPT_EXACT = frozenset(
    {
        "/health",
        "/maintenance",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/robots.txt",
        "/favicon.ico",
    }
)
_EXEMPT_PREFIXES = ("/admin/", "/docs/", "/static/")


def is_exempt_path(path: str) -> bool:
    """Routes that keep working in maintenance: health (DO must not restart the app), the state endpoint, docs, admin."""
    normalised = _VERSION_PREFIX.sub("", path, count=1).rstrip("/") or "/"
    if normalised in _EXEMPT_EXACT or normalised == "/admin":
        return True
    return normalised.startswith(_EXEMPT_PREFIXES)


class MaintenanceModeMiddleware:
    """Pure ASGI maintenance gate: 503 + Retry-After + no-store JSON for every non-exempt http request while on."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not is_maintenance_mode() or is_exempt_path(scope["path"]):
            await self.app(scope, receive, send)
            return

        body = json.dumps(maintenance_error_body(), separators=(",", ":")).encode()
        headers: list[tuple[bytes, bytes]] = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            (b"retry-after", str(retry_after_seconds()).encode()),
            *((k.lower().encode(), v.encode()) for k, v in NO_STORE_HEADERS.items()),
        ]
        await send({"type": "http.response.start", "status": 503, "headers": headers})
        await send({"type": "http.response.body", "body": b"" if scope.get("method") == "HEAD" else body})


class MaintenanceState(BaseModel):
    maintenance: bool = Field(description="True while the API and data pipeline are in maintenance")
    message: str | None = Field(None, description="Human readable notice for a banner. Null when not in maintenance")
    eta: str | None = Field(
        None, description="Expected end as ISO 8601 with offset, when known. Null when unknown or not in maintenance"
    )


router = APIRouter()

MAINTENANCE_DESCRIPTION = """Current maintenance state. Public: no API key, CORS open, never cached.

Poll this to show a banner. While maintenance is on, every other data route answers
`503` with a `Retry-After` header (seconds) and this body:

```json
{"success": false, "error": "<message>", "maintenance": true, "message": "<message>", "eta": "2026-11-02T14:00:00+10:00"}
```

`eta` is null when unknown. `/health` and this endpoint stay up during maintenance.
"""


@router.get(
    "/maintenance",
    response_model=MaintenanceState,
    tags=["Core"],
    summary="Maintenance state",
    description=MAINTENANCE_DESCRIPTION,
)
async def get_maintenance_state() -> JSONResponse:
    return JSONResponse(content=maintenance_state(), headers={**NO_STORE_HEADERS, "Access-Control-Allow-Origin": "*"})
