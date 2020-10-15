import pkg_resources
import sentry_sdk

from opennem.settings import settings

VERSION = pkg_resources.get_distribution(__package__).version


if settings.env != "development":
    sentry_sdk.init(
        settings.sentry_url, traces_sample_rate=1.0, environment=settings.env
    )

__version__ = VERSION
