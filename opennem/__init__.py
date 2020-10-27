import sentry_sdk

from opennem.settings import settings

# from pkg_resources import get_distribution


# VERSION = get_distribution("opennem").version
# __version__ = VERSION


if settings.debug is False:
    sentry_sdk.init(
        settings.sentry_url, traces_sample_rate=1.0, environment=settings.env
    )

