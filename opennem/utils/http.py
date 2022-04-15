"""
    HTTP module with custom timeout and retry adaptors

    usage:

    from opennem.utils.http import http
    http.get(`url`) etc.

"""
import logging
from typing import Any
from urllib.request import Request

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from opennem.settings import settings
from opennem.utils.version import get_version

urllib3.disable_warnings()

logger = logging.getLogger("opennem.utils.http")

DEFAULT_TIMEOUT = settings.http_timeout
DEFAULT_RETRIES = settings.http_retries

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"  # noqa: 501

CHROME_AGENT_HEADERS = {
    "user-agent": USER_AGENT,
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "accept-encoding": "gzip, deflate",
    "scheme": "https",
    "sec-ch-prefers-color-scheme": "light",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}

API_CLIENT_HEADERS = {"user-agent": f"OpenNEM (v {get_version()})", "accept": "*/*"}


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

    requests_cache.install_cache(".elecmon_requests_cache", expire_after=60 * 60 * 4)
    logger.info("Setup HTTP cache at: {}".format(settings.http_cache_local))
    return True


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request: Request, **kwargs) -> Any:
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


retry_strategy = Retry(
    total=DEFAULT_RETRIES,
    backoff_factor=2,
    status_forcelist=[403, 429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)


# This will retry on 403's as well
retry_strategy_on_permission_denied = Retry(
    total=DEFAULT_RETRIES,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)

http = requests.Session()

http.headers.update({"User-Agent": USER_AGENT})

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
