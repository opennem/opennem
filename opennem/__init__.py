# setup sentry
from opennem.settings import settings
from opennem.utils.sentry import setup_sentry

if settings.sentry_enabled:
    setup_sentry()


import warnings

# Ignore noisy twisted deprecation warnings
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="twisted"
)
