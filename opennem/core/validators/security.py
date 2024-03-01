"""
OpenNEM Security Validators

Functions to validate security fields and schemas
"""

from opennem.api.auth.exceptions import UnauthorizedRequest
from opennem.core.normalizers import string_is_urlsafe


def validate_api_key(api_key: str) -> str:
    """Validate an API key"""
    if not api_key:
        raise UnauthorizedRequest()

    if not isinstance(api_key, str):
        raise TypeError("API Key invalid type")

    if len(api_key) < 16:
        raise ValueError("API Key too short")

    if len(api_key) > 128:
        raise ValueError("API Key too long")

    if not string_is_urlsafe(api_key):
        raise ValueError("API Key is not an URL-safe string")

    return api_key
