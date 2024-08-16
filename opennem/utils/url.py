"""URL utility methods"""

import urllib
from pathlib import Path

# urljoin from here so that the netlocs can be loaded
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlparse, urlunparse  # noqa: F401

import validators

# Support S3 URI's in urllib
urllib.parse.uses_netloc.append("s3")
urllib.parse.uses_relative.append("s3")


def change_url_path(url: str, new_path: str) -> str:
    # Parse the URL into its components
    parsed_url = urlparse(url)

    # Create a new tuple with the updated path
    updated_url_components = (
        parsed_url.scheme,
        parsed_url.netloc,
        new_path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment,
    )

    # Reconstruct the URL with the updated path
    updated_url = urlunparse(updated_url_components)

    return updated_url


def bucket_to_website(bucket_path: str, to_scheme: str = "https") -> str:
    """
    Converts a bucket path to a website path

    ex. "s3://data.test.org" -> "https://data.test.org"
    """
    bucket_path_parsed = urlparse(bucket_path)
    bucket_path_parsed = bucket_path_parsed._replace(scheme=to_scheme)
    return bucket_path_parsed.geturl()


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


def is_url(url: str) -> bool:
    """Tests if a string is a URL"""
    try:
        validators.url(url)
        return True
    except validators.ValidationFailure:
        return False


def strip_url_schema(url: str, replace_schema: str = "http") -> str:
    """Strips the https schema from a URL"""
    parsed_url = urlparse(url)
    url = urlunparse(parsed_url._replace(scheme=replace_schema))
    return url


if __name__ == "__main__":
    u = "https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_20220612.zip"
    print(get_filename_from_url(u))
