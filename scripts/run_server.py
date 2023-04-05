#!/usr/bin/env python
"""
    Script to run the asgi uvicorn server in dev
    and prod

"""
import logging
from pathlib import Path

import click
import uvicorn

from opennem import settings

# from uvicorn import Config as UvicornConfig

logger = logging.getLogger("opennem.server")

RELOAD_PATH = Path(__file__).parent.parent.resolve() / "opennem"


def run_server() -> None:
    log_level = "info"
    reload = False
    reload_dirs = None
    workers = 4
    ssl_options = {}

    # @TODO move this into opennem.settings
    if settings.debug:
        reload = True
        log_level = "debug"
        reload_dirs = [str(RELOAD_PATH)]
        workers = 1

    if settings.server_ssl:
        ssl_options = {
            "ssl_keyfile": "./var/_wildcard.opennem.localhost-key.pem",
            "ssl_certfile": "./var/_wildcard.opennem.localhost.pem",
        }

    uvicorn.run(
        "opennem.api.app:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=log_level,
        reload=reload,
        reload_dirs=reload_dirs,
        workers=workers,
        **ssl_options,
    )

    logger.info(f"Running server on {settings.server_host} {settings.server_port}")


@click.command()
@click.option("--host", "-h", default="localhost", help="The host to bind to [default: localhost]")
@click.option("--port", "-p", default=5432, help="The port to bind to [default: 5432]")
@click.option("--debug/--no-debug", default=False, help="Set flask to debug mode")
@click.option("--env", "-e", default=".env", help="Environment file to read into settings schema")
def run(host, port, debug, env, models):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("User interrupted")
    except Exception as e:
        logger.error(e)
