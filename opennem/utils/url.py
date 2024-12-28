"""URL utility methods"""

from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse


def strip_query_string(url: str, param: str | None = None) -> str:
    """strip the query string from an URL

    Args:
        url (str): URL to strip
        param (Optional[str], optional): Only strip query string parameter with name. Defaults to None.

    Returns:
        str: clean URL
    """
    _parsed = urlparse(url)

    # strip out qs
    # @TODO support popping a particular key
    _parsed = _parsed._replace(query="")

    _url_clean = urlunparse(_parsed)

    return _url_clean


def get_filename_from_url(url: str) -> str:
    """Get the filename part of a url"""
    url_components = urlparse(url)
    url_path = Path(unquote(url_components.path))
    return url_path.name
