"""
Maintenance mode FastAPI application for OpenNEM.

This module provides a simple FastAPI application that returns a maintenance mode
response for all routes. Used when the main application needs to be taken offline
for maintenance.
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, PlainTextResponse

from opennem.core.maintenance import NO_STORE_HEADERS, maintenance_error_body, retry_after_seconds

app = FastAPI(
    title="OpenNEM API - Maintenance Mode",
    description="OpenNEM API Maintenance Mode Application",
    version="1.0.0",
)


@app.get("/health", include_in_schema=False)
async def health() -> PlainTextResponse:
    """Stay healthy so the platform does not restart the app."""
    return PlainTextResponse("OK")


@app.get("/")
@app.get("/{path:path}")
async def maintenance_response() -> JSONResponse:
    """503 for every other route, same body and headers as the main API's maintenance gate (#782)."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=maintenance_error_body(),
        headers={**NO_STORE_HEADERS, "Retry-After": str(retry_after_seconds())},
    )


def run_maintenance_app(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """
    Run the maintenance mode FastAPI application using uvicorn.

    Args:
        host: Host address to bind to
        port: Port to bind to
        reload: Enable auto-reload on code changes
        log_level: Logging level for uvicorn
    """
    import uvicorn

    uvicorn.run(
        "opennem.api.maintenance_app:app",
        host=host,
        port=port,
        reload=reload,
        workers=1,
        log_level=log_level,
    )


if __name__ == "__main__":
    run_maintenance_app()
