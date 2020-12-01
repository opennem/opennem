import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from opennem.settings import settings


def setup_sentry() -> None:
    if settings.sentry_enabled and settings.debug is False:
        sentry_sdk.init(
            settings.sentry_url,
            traces_sample_rate=1.0,
            environment=settings.env,
            integrations=[RedisIntegration(), SqlalchemyIntegration()],
        )
