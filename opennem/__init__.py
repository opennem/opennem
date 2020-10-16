import sentry_sdk
from pkg_resources import get_distribution

from opennem.settings import settings

# VERSION = get_distribution("opennem").version
# __version__ = VERSION


if settings.env != "development":
    sentry_sdk.init(
        settings.sentry_url, traces_sample_rate=1.0, environment=settings.env
    )

