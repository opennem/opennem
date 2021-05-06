import sys

# This will eventually be dynamically parsed
v = "3.7.0"
__env__ = "prod"


# Check minimum required Python version
if sys.version_info < (3, 7):
    print("OpenNEM %s requires Python 3.7 or greater")
    sys.exit(1)


# setup sentry
from opennem.settings import settings  # noqa: E402
from opennem.utils.sentry import setup_sentry  # noqa: E402

if settings.sentry_enabled:
    setup_sentry()


import warnings  # noqa: E402

# Ignore noisy twisted deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="twisted")
