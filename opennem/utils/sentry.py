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


def _get_sentry_ignore_exception_types() -> list[type]:
    """Lazy import to avoid circular import with opennem.__init__"""
    from opennem.api.exceptions import BadCredentials, RevokedCredentials, UnauthorizedRequest
    from opennem.clients.unkey import UnkeyInvalidUserException

    return [
        HTTPException,
        UnkeyInvalidUserException,
        UnauthorizedRequest,
        BadCredentials,
        RevokedCredentials,
    ]


def _sentry_before_send(event, hint):
    """Filter out HTTPExceptions in production"""
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, tuple(_get_sentry_ignore_exception_types())):
            return None
    return event


def setup_sentry(
    sentry_url: str,
    environment: str,
    service: ServiceType = "api",
    traces_sample_rate: float = 0.05,
) -> None:
    """
    Setup Sentry for the application.

    Args:
        sentry_url: Sentry DSN
        environment: deployment environment (local, development, staging, production)
        service: "api" or "worker" - determines which integrations to load
        traces_sample_rate: fraction of transactions sent as performance traces
            (0-1). Applies to every non-local environment. Profiling is off.
    """
    if environment == "local":
        logger.info("Sentry not enabled in local mode")
        return

    # Base config
    sentry_options: dict = {
        "dsn": sentry_url,
        "environment": environment,
        "traces_sample_rate": traces_sample_rate,
        "profiles_sample_rate": 0.0,
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

    # Filter auth exceptions in all non-local environments
    sentry_options["before_send"] = _sentry_before_send

    sentry_sdk.init(**sentry_options)

    # Set service tag for filtering in Sentry UI
    sentry_sdk.set_tag("service", service)

    logger.info(f"Sentry initialized for {service} in {environment} (traces {traces_sample_rate:.0%})")
