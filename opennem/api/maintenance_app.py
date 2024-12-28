"""
Maintenance mode FastAPI application for OpenNEM.

This module provides a simple FastAPI application that returns a maintenance mode
response for all routes. Used when the main application needs to be taken offline
for maintenance.
"""

from datetime import UTC, datetime

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class MaintenanceResponse(BaseModel):
    """Maintenance mode response model."""

    status: str = "maintenance"
    message: str
    estimated_return: str | None = None


app = FastAPI(
    title="OpenNEM API - Maintenance Mode",
    description="OpenNEM API Maintenance Mode Application",
    version="1.0.0",
)


@app.get("/", response_model=MaintenanceResponse)
@app.get("/{path:path}", response_model=MaintenanceResponse)
async def maintenance_response() -> JSONResponse:
    """
    Return a maintenance mode response for all routes.

    Returns:
        JSONResponse: A 503 status code with maintenance information
    """
    current_time = datetime.now(UTC)
    estimated_return = current_time.replace(hour=current_time.hour + 2).isoformat()

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "maintenance",
            "message": "OpenNEM API is currently undergoing scheduled maintenance. Please try again later.",
            "estimated_return": estimated_return,
        },
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
