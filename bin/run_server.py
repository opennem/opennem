#!/usr/bin/env python
"""
Script to run the asgi uvicorn server in dev
and prod

"""

import logging
from pathlib import Path

import uvicorn

from opennem import settings

# from uvicorn import Config as UvicornConfig

logger = logging.getLogger("opennem.server")

RELOAD_PATH = Path(__file__).parent.parent.resolve() / "opennem"


def run_server(host: str = "0.0.0.0", port: int = 8000, server_ssl: bool = False, workers: int | None = None) -> None:
    import multiprocessing

    server_workers = multiprocessing.cpu_count()

    if not workers:
        workers = server_workers

    log_level = settings.log_level.lower()
    reload_enabled = False
    reload_dirs = None
    ssl_options = {}

    # @TODO move this into opennem.settings
    if settings.debug or settings.is_dev:
        reload_enabled = True
        log_level = "debug"
        reload_dirs = [str(RELOAD_PATH)]
        workers = 1

    if server_ssl:
        ssl_options = {
            "ssl_keyfile": "./var/_wildcard.opennem.localhost-key.pem",
            "ssl_certfile": "./var/_wildcard.opennem.localhost.pem",
        }

    uvicorn.run(
        "opennem.api.app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload_enabled,
        reload_dirs=reload_dirs,
        workers=workers,
        **ssl_options,  # type: ignore
    )

    logger.info(f"Running server on {host} {port}")


if __name__ == "__main__":
    try:
        run_server(workers=4)
    except KeyboardInterrupt:
        logger.info("User interrupted")
    except Exception as e:
        logger.error(e)
