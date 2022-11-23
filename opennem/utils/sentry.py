import sentry_sdk
from fastapi import HTTPException
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from opennem.clients.bom import BOMParsingException
from opennem.settings import settings

_SENTRY_IGNORE_EXCEPTION_TYPES = [BOMParsingException, HTTPException]


def _sentry_before_send(event, hint):
    """Hook to sentry sending and excelude some exception types"""
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTION_TYPES):
            return None
    return event


def setup_sentry() -> None:
    if settings.sentry_enabled:
        sentry_sdk.init(
            settings.sentry_url,
            traces_sample_rate=1.0,
            environment=settings.env,
            before_send=_sentry_before_send,
            integrations=[RedisIntegration(), SqlalchemyIntegration()],
        )
