import logging
from typing import Literal

import sentry_sdk
from fastapi import HTTPException
from sentry_sdk.integrations.arq import ArqIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

logger = logging.getLogger("opennem.utils.sentry")

ServiceType = Literal["api", "worker"]

_SENTRY_IGNORE_EXCEPTION_TYPES = [HTTPException]


def _sentry_before_send(event, hint):
    """Filter out HTTPExceptions in production"""
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, tuple(_SENTRY_IGNORE_EXCEPTION_TYPES)):
            return None
    return event


def setup_sentry(
    sentry_url: str,
    environment: str,
    service: ServiceType = "api",
) -> None:
    """
    Setup Sentry for the application.

    Args:
        sentry_url: Sentry DSN
        environment: deployment environment (local, development, staging, production)
        service: "api" or "worker" - determines which integrations to load
    """
    if environment == "local":
        logger.info("Sentry not enabled in local mode")
        return

    # Base config
    sentry_options: dict = {
        "dsn": sentry_url,
        "environment": environment,
        "traces_sample_rate": 1.0,
        "profiles_sample_rate": 1.0,
        "release": None,  # Will auto-detect from git
    }

    # Service-specific integrations
    if service == "api":
        sentry_options["integrations"] = [
            RedisIntegration(),
            SqlalchemyIntegration(),
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=set(range(500, 599)),
                http_methods_to_capture=("GET", "POST", "PUT", "DELETE", "PATCH"),
            ),
        ]
    elif service == "worker":
        sentry_options["integrations"] = [
            RedisIntegration(),
            SqlalchemyIntegration(),
            ArqIntegration(),
        ]

    # Production-specific config
    if environment == "production":
        sentry_options["before_send"] = _sentry_before_send
        sentry_options["traces_sample_rate"] = 0.1
        sentry_options["profiles_sample_rate"] = 0.1

    sentry_sdk.init(**sentry_options)

    # Set service tag for filtering in Sentry UI
    sentry_sdk.set_tag("service", service)

    logger.info(f"Sentry initialized for {service} in {environment}")
