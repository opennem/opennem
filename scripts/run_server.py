"""
    Script to run the asgi uvicorn server in dev
    and prod

"""

import logging

import uvicorn

from opennem.settings import settings

# from uvicorn import Config as UvicornConfig

logger = logging.getLogger("opennem.server")


def run_server() -> None:
    log_level = "info"
    reload = False
    reload_dirs = None
    workers = 4

    # @TODO move this into opennem.settings
    if settings.debug:
        reload = True
        log_level = "debug"
        reload_dirs = "opennem"
        workers = 1

    uvicorn.run(
        "opennem.api.app:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=log_level,
        reload=reload,
        reload_dirs=reload_dirs,
        workers=workers,
    )


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("User interrupted")
    except Exception as e:
        logger.error(e)
