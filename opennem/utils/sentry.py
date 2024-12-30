import logging

import sentry_sdk
from fastapi import HTTPException
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger("opennem.utils.sentry")

_SENTRY_IGNORE_EXCEPTION_TYPES = [HTTPException]

_INTEGRATIONS = [
    RedisIntegration(),
    SqlalchemyIntegration(),
    FastApiIntegration(
        transaction_style="endpoint",
        failed_request_status_codes={401, 403, *range(500, 599)},
        http_methods_to_capture=("GET", "POST"),
    ),
]


def _sentry_before_send(event, hint):
    """Hook to sentry sending and excelude some exception types"""
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, _SENTRY_IGNORE_EXCEPTION_TYPES):  # type: ignore
            return None
    return event


def setup_sentry(sentry_url: str, environment: str) -> None:
    """
    Setup sentry for the application

    @NOTE: default_integrations=False is used to disable the default integrations since there is an error in the arq integration
    """
    if environment == "local":
        logger.info("Sentry not enabled in local mode")
        return

    sentry_options = {
        "environment": environment,
        "traces_sample_rate": 1.0,
        "profiles_sample_rate": 1.0,
        "integrations": _INTEGRATIONS,
        "default_integrations": False,
    }

    if environment == "production":
        # in production we reduce the sample rate and ignore HTTP exceptions
        sentry_options["before_send"] = _sentry_before_send
        sentry_options["traces_sample_rate"] = 0.1
        sentry_options["profiles_sample_rate"] = 0.1

    sentry_sdk.init(**{**sentry_options, "dsn": sentry_url})
    logger.info(f"Sentry enabled in {environment} mode")
