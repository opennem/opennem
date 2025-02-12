"""
Field types for OpenNEM pydantic schemas used in this module

This module provides custom field types and validators for use in Pydantic models
throughout the OpenNEM project, including specialized URL and floating point handlers.
"""

from typing import Annotated
from urllib.parse import urlparse, urlunparse

from pydantic import BeforeValidator, StringConstraints


def _round_float(v: float, precision: int) -> float:
    """Round a float value to specified precision"""
    if isinstance(v, float):
        return round(v, precision)
    return v


def _normalize_url_no_path(url: str) -> str:
    """
    Normalize a URL to ensure it has no path component and doesn't end with a slash

    Args:
        url: The URL string to normalize

    Returns:
        str: Normalized URL with only scheme and netloc

    Raises:
        ValueError: If URL contains a path or is malformed
    """
    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url)

    if not parsed.netloc:
        raise ValueError("Invalid URL: missing domain")

    if parsed.path and parsed.path != "/":
        raise ValueError("URL must not contain a path")

    # Reconstruct URL with only scheme and netloc
    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            "",  # path
            "",  # params
            "",  # query
            "",  # fragment
        )
    )

    return normalized


def _normalize_url_clean_path(url: str) -> str:
    """
    Normalize a URL to ensure it has a clean single-level path without double slashes

    Args:
        url: The URL string to normalize

    Returns:
        str: Normalized URL with clean path

    Raises:
        ValueError: If URL is malformed or has invalid path structure
    """
    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url)

    if not parsed.netloc:
        raise ValueError("Invalid URL: missing domain")

    # Split path and filter out empty segments
    path_parts = [p for p in parsed.path.split("/") if p]

    if not path_parts:
        raise ValueError("URL must contain exactly one path segment")

    if len(path_parts) > 1:
        raise ValueError("URL must contain only one path segment")

    # Reconstruct URL with normalized path
    clean_path = f"/{path_parts[0]}"
    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            clean_path,
            "",  # params
            "",  # query
            "",  # fragment
        )
    )

    return normalized


# Rounded float types
RoundedFloat2 = Annotated[float, BeforeValidator(lambda v: _round_float(v, 2))]
RoundedFloat4 = Annotated[float, BeforeValidator(lambda v: _round_float(v, 4))]
RoundedFloat6 = Annotated[float, BeforeValidator(lambda v: _round_float(v, 6))]
RoundedFloat8 = Annotated[float, BeforeValidator(lambda v: _round_float(v, 8))]  # used for lat, lng and polygons

# valid DUID
DUIDType = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9_./\-#]{3,32}$")]

# URL types with validation
URLNoPath = Annotated[str, BeforeValidator(_normalize_url_no_path), StringConstraints(pattern=r"^https?://[^/]+$")]

URLCleanPath = Annotated[str, BeforeValidator(_normalize_url_clean_path), StringConstraints(pattern=r"^https?://[^/]+/[^/]+$")]
