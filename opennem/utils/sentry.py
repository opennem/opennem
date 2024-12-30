import logging

import sentry_sdk
from fastapi import HTTPException

from opennem import settings

logger = logging.getLogger("opennem.utils.sentry")

_SENTRY_IGNORE_EXCEPTION_TYPES = [HTTPException]


def _sentry_before_send(event, hint):
    """Hook to sentry sending and excelude some exception types"""
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTION_TYPES):  # type: ignore
            return None
    return event


def setup_sentry(sentry_url: str) -> None:
    """
    Setup sentry for the application
    """
    sentry_sdk.init(
        sentry_url,
        environment=settings.env,
    )

    logger.info(f"Sentry enabled in {settings.env} mode")


def setup_sentry_from_env(sentry_url: str) -> None:
    """
    Setup sentry for the application
    """
    if settings.is_local:
        logger.info("Sentry not enabled in local mode")
        return

    elif settings.is_dev:
        sentry_sdk.init(
            sentry_url,
            environment="development",
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        logger.info("Sentry enabled in dev mode")
        return

    elif settings.is_prod:
        sentry_sdk.init(
            sentry_url,
            traces_sample_rate=0.1,
            environment="production",
            before_send=_sentry_before_send,
            # integrations=[RedisIntegration(), SqlalchemyIntegration()],  # @NOTE: default integrations
            profiles_sample_rate=0.1,
        )
        logger.info("Sentry enabled in prod mode")
        return

    else:
        logger.error("Sentry not enabled in unknown mode")
        return
