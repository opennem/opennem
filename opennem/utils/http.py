"""
    HTTP module with custom timeout and retry adaptors

"""
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 5


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
    backoff_factor=1,
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
