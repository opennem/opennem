#!/usr/bin/env python
"""
Script to run the ASGI Granian server in development
and production environments.

This script provides a programmatic way to start the OpenNEM API
using Granian with configurable options for SSL, workers, and
reload capabilities.
"""

import logging
from pathlib import Path

from granian import Granian
from granian.constants import Interfaces, Loops
from granian.log import LogLevels

from opennem import settings

logger = logging.getLogger("opennem.server")

RELOAD_PATH = Path(__file__).parent.parent.resolve() / "opennem"


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    server_ssl: bool = False,
    workers: int | None = 2,
    reload: bool = False,
) -> None:
    """
    Run the OpenNEM API server using Granian.

    Args:
        host: The host interface to bind to
        port: The port to listen on
        server_ssl: Whether to enable SSL
        workers: Number of worker processes
        reload: Enable hot reload for development
    """
    log_level = settings.log_level.lower()
    log_level = LogLevels(log_level)

    if not workers:
        workers = 1

    if not log_level:
        log_level = LogLevels.debug

    # Configure development settings
    if settings.debug or settings.is_dev or settings.is_local:
        reload = True
        log_level = LogLevels.debug
        workers = 1

    logger.info(f"Running Granian server on {host}:{port} with {workers} workers")

    # Create Granian instance
    server = Granian(
        target="opennem.api.app:app",
        address=host,
        port=port,
        interface=Interfaces.ASGI,
        workers=workers,
        log_level=log_level,
        # Use asyncio loop (compatible with FastAPI)
        loop=Loops.asyncio,
        # Enable reload if in dev mode
        reload=reload,
        # Respawn failed workers
        respawn_failed_workers=True,
        # Disable websockets if not needed (better performance)
        websockets=False,
    )

    try:
        server.serve()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


def serve():
    """Production server entry point."""
    run_server(
        host=settings.api_server_host,
        port=settings.api_server_port,
        workers=settings.api_server_workers,
        reload=False,
    )


def serve_dev():
    """Development server entry point with hot reload."""
    run_server(
        host=settings.api_server_host,
        port=settings.api_server_port,
        workers=1,
        reload=True,
    )


if __name__ == "__main__":
    serve()
