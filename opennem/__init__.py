import sentry_sdk

from opennem.settings import settings


def get_sentry_env():
    pass


if settings.env != "development":
    sentry_sdk.init(
        settings.sentry_url, traces_sample_rate=1.0, environment=settings.env
    )
