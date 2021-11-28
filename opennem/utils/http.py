"""
    HTTP module with custom timeout and retry adaptors

    usage:

    from opennem.utils.http import http
    http.get(`url`) etc.

"""
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore

from opennem.settings import settings

logger = logging.getLogger("opennem.utils.http")

DEFAULT_TIMEOUT = settings.http_timeout
DEFAULT_RETRIES = settings.http_retries


def setup_http_cache() -> bool:
    """Sets up requests session local cachine using
    requests-cache if enabled in settings"""
    if not settings.http_cache_local:
        return False

    try:
        import requests_cache
    except ImportError:
        logger.error("Request caching requires requests-cache library")
        return False

    requests_cache.install_cache(".opennem_requests_cache", expire_after=300)
    return True


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


retry_strategy = Retry(
    total=DEFAULT_RETRIES,
    backoff_factor=2,
    status_forcelist=[403, 429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"],
)


http = requests.Session()

adapter_timeout = TimeoutHTTPAdapter()
http.mount("https://", adapter_timeout)
http.mount("http://", adapter_timeout)


adapter_retry = HTTPAdapter(max_retries=retry_strategy)
http.mount("https://", adapter_retry)
http.mount("http://", adapter_retry)

setup_http_cache()


def mount_timeout_adaptor(session: requests.Session) -> None:
    session.mount("https://", adapter_timeout)
    session.mount("http://", adapter_timeout)


def mount_retry_adaptor(session: requests.Session) -> None:
    session.mount("https://", adapter_retry)
    session.mount("http://", adapter_retry)
