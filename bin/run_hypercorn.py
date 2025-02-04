#!/usr/bin/env python
"""
Script to run the asgi hypercorn server in development
and production environments.

This script provides a programmatic way to start the OpenNEM API
using Hypercorn with configurable options for SSL, workers, and
reload capabilities.
"""

import logging
from pathlib import Path

from hypercorn.config import Config
from hypercorn.run import run

from opennem import settings

logger = logging.getLogger("opennem.server")

RELOAD_PATH = Path(__file__).parent.parent.resolve() / "opennem"


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    server_ssl: bool = False,
    workers: int | None = 2,
) -> None:
    """
    Run the OpenNEM API server using Hypercorn.

    Args:
        host: The host interface to bind to
        port: The port to listen on
        server_ssl: Whether to enable SSL
        workers: Number of worker processes
    """
    config_options = {
        "bind": [f"{host}:{port}"],
        "loglevel": settings.log_level.lower(),
        "workers": workers if workers else 1,
        "application_path": "opennem.api.app:app",
    }

    # Configure development settings
    if settings.debug or settings.is_local:
        config_options.update(
            {
                "use_reloader": True,
                "workers": 1,
                "loglevel": "debug",
            }
        )

    # SSL configuration if enabled
    if server_ssl:
        config_options.update(
            {
                "keyfile": "./var/_wildcard.opennem.localhost-key.pem",
                "certfile": "./var/_wildcard.opennem.localhost.pem",
            }
        )

    config = Config.from_mapping(config_options)
    logger.info(f"Running Hypercorn server on {host}:{port}")

    try:
        exit_code = run(config)
        logger.info(f"Server exited with code {exit_code}")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


def serve():
    run_server(
        host=settings.api_server_host,
        port=settings.api_server_port,
        workers=settings.api_server_workers,
    )


if __name__ == "__main__":
    serve()
