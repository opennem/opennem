import sys

# Check minimum required Python version
if sys.version_info < (3, 7):
    print("OpenNEM %s requires Python 3.7 or greater")
    sys.exit(1)


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
