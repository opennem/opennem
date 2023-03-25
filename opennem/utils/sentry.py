import sentry_sdk
from fastapi import HTTPException
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

_SENTRY_IGNORE_EXCEPTION_TYPES = [HTTPException]


def _sentry_before_send(event, hint):
    """Hook to sentry sending and excelude some exception types"""
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTION_TYPES):
            return None
    return event


def setup_sentry(sentry_url: str, environment: str = "development") -> None:
    sentry_sdk.init(
        sentry_url,
        traces_sample_rate=1.0,
        environment=environment,
        before_send=_sentry_before_send,
        integrations=[RedisIntegration(), SqlalchemyIntegration()],
        _experiments={
            "profiles_sample_rate": 1.0,
        },
    )
